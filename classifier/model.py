import pickle
import os
import json

from classifier.config import Config
from classifier import misc


class Model:
    """ A simple abstraction layer for using the Word Embedding Model """
    
    def __init__(self, load_model = True):
        """ Initialising the model class
        """
        self.model = dict()
        self.full_model = None
        self.config = Config()
        
        self.embedding_size = 0
        
        if load_model:
            self.load_models()

        
    def check_word_in_model(self, word):
        """ It checks whether a word is available in the cached model
        """
        if word in self.model:
            return True
        
        return False
    
    def check_word_in_full_model(self, word):
        """ It checks whether a word is available in the word2vec model
        """
        if word in self.full_model:
            return True
        
        return False

    def get_embedding_from_full_model(self, word):
        """ Returns the embedding vector of the word:word
        Args:
            word (string): word that potentially belongs to the model
        
        Return:
            list (of size self.embedding_size): containing all embedding values
        """
        try:
            return self.full_model[word]
        except KeyError:
            return [0]*self.embedding_size #array full of zeros: just don't move in the embedding space

    def get_words_from_model(self, word):
        """ Returns the similar words to the word:word
        Args:
            word (string): word that potentially belongs to the model
        
        Return:
            dictionary: containing info about the most similar words to word. Empty if the word is not in the model.
        """
        try:
            return self.model[word]
        except KeyError:
            return {}
        
        
    def load_models(self):
        """Function that loads both models. 
        """
        self.load_chached_model()
        self.load_word2vec_model()


    def load_chached_model(self):
        """Function that loads the cached Word2vec model. 
        The ontology file has been serialised with Pickle. 
        The cached model is a json file (dictionary) containing all words in the corpus vocabulary with the corresponding CSO topics.
        The latter has been created to speed up the process of retrieving CSO topics given a token in the metadata
        """
        
        self.check_cached_model()
        with open(self.config.get_cached_model()) as f:
           self.model = json.load(f)
        print("Model loaded.")
           
    
    def check_cached_model(self, notification = False):
        """Function that checks if the cached model is available. If not, it will attempt to download it from a remote location.
        Tipically hosted on the CSO Portal.
        """
        if not os.path.exists(self.config.get_cached_model()):
            print('[*] Beginning download of cached model from', self.config.get_cahed_model_remote_url())
            misc.download_file(self.config.get_cahed_model_remote_url(), self.config.get_cached_model())
            
            
    def load_word2vec_model(self):
        """Function that loads Word2vec model. 
        This file has been serialised using Pickle allowing to be loaded quickly.
        """
        self.check_word2vec_model()
        self.full_model = pickle.load(open(self.config.get_model_pickle_path(), "rb"))
        self.embedding_size = self.full_model.vector_size
    
    
    def get_embedding_size(self):
        """Function that returns the size of the embedding model. 
        """
        return self.embedding_size
          
    def check_word2vec_model(self):
        """Function that checks if the model is available. If not, it will attempt to download it from a remote location.
        Tipically hosted on the CSO Portal.
        """
        if not os.path.exists(self.config.get_model_pickle_path()):
            print('[*] Beginning model download from', self.config.get_model_pickle_remote_url())
            misc.download_file(self.config.get_model_pickle_remote_url(), self.config.get_model_pickle_path())  

  
    def setup(self):
        """Function that sets up the word2vec model
        """
        misc.print_header("MODELS: CACHED & WORD2VEC")
        
        if not os.path.exists(self.config.get_cached_model()):
            print('[*] Beginning download of cached model from', self.config.get_cahed_model_remote_url())
            task_completed = misc.download_file(self.config.get_cahed_model_remote_url(), self.config.get_cached_model())

            if task_completed:
                print("File containing the cached model has been downloaded successfully.")
            else:
                print("We were unable to complete the download of the cached model.")
        else:
            print("Nothing to do. The cached model is already available.")
            
        if not os.path.exists(self.config.get_cached_model()):
            print('[*] Beginning download of word2vec model from', self.config.get_model_pickle_remote_url())
            task_completed = misc.download_file(self.config.get_model_pickle_remote_url(), self.config.get_model_pickle_path())

            if task_completed:
                print("File containing the word2vec model has been downloaded successfully.")
            else:
                print("We were unable to complete the download of the word2vec model.")
        else:
            print("Nothing to do. The word2vec model is already available.")
    

    def update(self, force = False): 
        """Function that updates the models
        The variable force is for the future when we will have models versioning.
        """
        misc.print_header("MODELS: CACHED & WORD2VEC")
        try:
            os.remove(self.config.get_cached_model())
        except FileNotFoundError:
            print("Couldn't delete file cached model: not found")
        
        try:
            os.remove(self.config.get_model_pickle_path())
        except FileNotFoundError:
            print("Couldn't delete file word2vec model: not found")
        print("Updating the models: cached and word2vec")
        task_completed1 = misc.download_file(self.config.get_cahed_model_remote_url(), self.config.get_cached_model())
        task_completed2 = misc.download_file(self.config.get_model_pickle_remote_url(), self.config.get_model_pickle_path())
        if task_completed1 and task_completed2:
            print("Models downloaded successfully.")

            








