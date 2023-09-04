from abc import ABC, abstractmethod

class LLM():

    @abstractmethod
    def get_llm(*args, **kwargs):
        pass

class Llama(LLM):
    
    def get_llm(*args, **kwargs):
        pass

class TogetherAI(LLM):

    def get_llm(*args, **kwargs):
        pass