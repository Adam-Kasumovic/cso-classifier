import numpy as np
import math
import re
from scipy.spatial import distance
from strsimpy.metric_lcs import MetricLCS

class PostProcess:
    """ A simple abstraction layer for using the Post-Processing module of the CSO classifier """

    def __init__(self, model = None, cso = None, enhancement = "first", result = None):
        """Function that initialises an object of class PostProcess and all its members.

        Args:
            model (dictionary): word2vec model.
            cso (dictionary): Computer Science Ontology
            enhancement (string): kind of enhancement
            result (Result class): topics identified from a document
        """
        self.cso = cso                  #Stores the CSO Ontology
        self.model = model              #contains the model 
        self.network_threshold = 1      #defines the threshold of the network (when filtering)
        self.enhancement = enhancement  #defines the type of enhancement
        
        self.result = None            # the result object
        self.list_of_topics = list()
        
        if result is not None:
            self.result = result            # the result object
            self.list_of_topics = self.result.get_union()

            
        
    
    def set_result(self, result):
        """Function that initializes the result variable in the class.

        Args:
            result (Result object): The resutls to analyse.
        """
        self.list_of_topics = list()
        self.result = result            # the result object
        self.list_of_topics = self.result.get_union()
    
    
    def get_result(self):
        return self.result
       
    
    def create_matrix_distance_from_ontology(self):
    
        len_mat = len(self.list_of_topics)    
        matrix = np.zeros((len_mat, len_mat), int)
        
        for i in range(0, len_mat):
            for j in range(i, len_mat):
                try:
                    this_dist = self.cso.get_graph_distance_in_topics(self.list_of_topics[i], self.list_of_topics[j])
                    matrix[i][j] = this_dist
                    matrix[j][i] = this_dist
                except IndexError:
                    pass
                except TypeError:
                    print(self.list_of_topics[i], self.list_of_topics[j],this_dist)
        
        norm_matrix = matrix/matrix.max()
        new_matrix = 1 - norm_matrix
        
        return new_matrix
    
    
    def create_matrix_distance_from_embeddings(self):

        len_mat = len(self.list_of_topics)
        matrix = np.zeros((len_mat, len_mat), float)
        np.fill_diagonal(matrix, 1)
    
        _list_of_topics = [i.replace(" ","_") for i in self.list_of_topics] #replacing space with underscore in topic labels
        
        embedding_size = self.model.get_embedding_size()
        
        for i in range(0, len_mat):
            for j in range(i+1, len_mat):
                try:
    
                    if self.model.check_word_in_full_model(_list_of_topics[i]):
                        terms_fst_tp = [_list_of_topics[i]]
                    else:
                        terms_fst_tp = _list_of_topics[i].split("_")
    
                    if self.model.check_word_in_full_model(_list_of_topics[j]):
                        terms_snd_tp = [_list_of_topics[j]]
                    else:
                        terms_snd_tp = _list_of_topics[j].split("_")
                    
                    embeddings_fst_tp = np.zeros(embedding_size)
                    embeddings_snd_tp = np.zeros(embedding_size)
                    for token in terms_fst_tp:
                        try:
                            embeddings_fst_tp += self.model.get_embedding_from_full_model(token)
                        except KeyError:
                            pass
    
                    for token in terms_snd_tp:
                        try:
                            embeddings_snd_tp += self.model.get_embedding_from_full_model(token)
                        except KeyError:
                            pass
                        
                    this_dist = self.cosine_similarity(embeddings_fst_tp, embeddings_snd_tp)
                    matrix[i][j] = this_dist
                    matrix[j][i] = this_dist
                except IndexError:
                    pass
                except ValueError:
                    pass
        return matrix
    
    
    def cosine_similarity(self, dataSetI, dataSetII):
        """ Function that computes the cosine similarity as opposite of the cosine disrtance
        """
        return 1 - distance.cosine(dataSetI, dataSetII) #becuase this computes the distance and not the similarity
    
    
    def get_good_threshold(self, matrix, multiplicative = 2):
        number_of_nodes = len(matrix)
        minimum_number_of_edges = math.ceil(multiplicative*number_of_nodes)
        # Function "triu" removes the first diagonal and the lower triangle
        # In this way we get the unique distances only.
        all_elems = np.triu(matrix,+1).flatten().tolist() 
        all_elems.sort(reverse=True)
        try:
            threshold = all_elems[minimum_number_of_edges]
        except IndexError:
            threshold = all_elems[-1]
        
        return threshold


    def filtering_outliers(self):
        
        syntactic = self.result.get_syntactic()
        syntactic_to_keep = [topic for topic in syntactic if len(re.findall(r'\w+', topic)) > 1]
        
    
        
        embed_matrix = self.create_matrix_distance_from_embeddings()
        ontol_matrix = self.create_matrix_distance_from_ontology() 
        
        joined_matrix = np.maximum(embed_matrix, ontol_matrix)
        threshold = self.get_good_threshold(joined_matrix, self.network_threshold)
        
        #The following checks if a topic is connected with other topics with similarity higher than the threshold
        selected_topics = list()
        for i in range(len(self.list_of_topics)):
            t_len = len(np.where(joined_matrix[i] >= threshold)[0]) # Taking [0] as np.where returns a tuple (list,list) with positions. We don't need [1]
            if t_len > 1:
                selected_topics.append(self.list_of_topics[i]) # the topic is then appended to the selected topics
            
        # We identify the excluded topics then.     
        excluded_topics = set(self.list_of_topics).difference(set(selected_topics))
        
        # Now among the excluded, which one we can still promote?
        topics_to_spare = set()
    
        # At this stage we check if among the excluded topics there are some which happen to be parents of the selected topics
        for topic in selected_topics:
            try:
                its_broaders = self.cso.get_all_broaders_of_topic(topic)
            except KeyError:
                its_broaders = list()
            tts = excluded_topics.intersection(list(its_broaders))
            for i in tts:
                topics_to_spare.add(i)
    
        # At this stage we check if among the excluded topics there are some which have string similarity higher than the threshold.
        metric_lcs = MetricLCS()
        for topic in excluded_topics:
            for good_topic in selected_topics:
                distance = metric_lcs.distance(topic, good_topic)
                if distance < 0.5:
                    topics_to_spare.add(topic)
                    break
            
        
        # Modulating the result.
        
        selected_topics_set = set(selected_topics+syntactic_to_keep).union(topics_to_spare)
        selected_topics = list(selected_topics_set)
        
        self.result.set_syntactic(list(set(self.result.get_syntactic()).intersection(selected_topics_set)))
        self.result.set_semantic(list(set(self.result.get_semantic()).intersection(selected_topics_set)))
        self.result.set_union(selected_topics)
        self.result.set_enhanced(self.cso.climb_ontology(selected_topics, self.enhancement))
        
        
        return self.result