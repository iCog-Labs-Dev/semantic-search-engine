from chromadb import EmbeddingFunction
from semantic_search_engine.llm import TogetherLLM
from semantic_search_engine.chroma import ChromaSingleton
from semantic_search_engine import constants
from langchain import LLMChain, PromptTemplate
from chromadb.utils import embedding_functions
from langchain.llms.base import LLM
import os

class SemanticSearch():
    """The entrypoint to the package that contains the necessary data to 
    make a semantic search.
    """  

    def __init__(self) -> None:
        """initializes the necessary data to perform a semantic search
        """        

        # prompt template to be used by a chain
        self.prompt_template = PromptTemplate(
            input_variables=["context", "metadata", "query"],

            # the system prompt needs work
            template=\
            """
                <<SYS>> \n 
                    You are a helpful assistant, You will only answer the\
                    questions the Human asks. You will be given a chat\
                    message as context. Write a response that explains the human\
                    query based on what is discussed in the chat message.You\must\
                    answer questions using the context provided.A metadata that\
                    contains data related to the chat message will be provided.\
                    the metadata will be a json with a user key that represents the\
                    sender of the message and a ts key which is the timestamp of the\
                    time the chat message was sent.\ use this data to better explain\
                    the chat message.. If there isn't enough context, simply reply "This\
                    topic was not discussed previously"\
                <</SYS>> \n\n 
                [INST]\n
                    context: \n\n{context} \n\n\n\
                    metadata: \n\n{metadata} \n\n\n\
                    human query: {query}\n\
                    your response:\n \
                [/INST]
            """
        )

        # embedding function to be used by chroma
        self.embedding_function = embedding_functions.DefaultEmbeddingFunction()

        # A custom built langchain LLM 
        self.llm = TogetherLLM()  #  

        # A langchain chain constructed with the above attributes
        self.chain = LLMChain(
                llm=self.llm, 
                prompt=self.prompt_template,
                # include the necessary output parser
            )
        
        # a chroma collection
        self.collection = ChromaSingleton().\
            get_connection().\
            get_or_create_collection(
                constants.CHROMA_COLLECTION,
                embedding_function= self.embedding_function
            )  # this should ge only get_collection      

   
    def semantic_search(self, query : str, user : str = ""):
        """executes a semantic search on an LLM based on a certain query from a\
        vector db.

        Parameters
        ----------
        query : str
            the search query text
        api_key : str, optional, deprecated
            prevously used to represent a togetherAI api_key but currently not\
            used, by default None

        Returns
        -------
        str
            an explanation of for the query provided by the LLM
        """
        # TODO : implement the code below with crud
        query_result = self.collection.query(
            query_texts=[query],
            # where = {
            #     "chat" : {
            #         "$in" : self.__filter(user)
            #     }
            # }
        )

        return self.chain.run(
            { 
                "context" : query_result["documents"][0][0],
                "metadata" : query_result["metadatas"][0][0],
                "query" : query    
            }
        )


class SemanticSearchBuilder():
    """A builder pattern class used to build a semantic search

    Although the SemanticSearch class has default implementations of a\
    prompt template, llm and embedding funciton. this builder can be used\
    to change any of the state above. chain will be updated when calling\
    build.
    """
    ss = SemanticSearch()

    def set_prompt_tempate(self, prompt_template : PromptTemplate) -> None:
        """changes the default prompt template

        Parameters
        ----------
        prompt_template : PromptTemplate
            the new prompt template to change to
        """
        self.ss.prompt_template = prompt_template

    def set_embedding_function(self, embedding_function : EmbeddingFunction) -> None:
        """changes the default embedding function used by chroma

        Parameters
        ----------
        embedding_function : EmbeddingFunction
            an embedding function from chroma.embedding_function
        """
        self.ss.embedding_function = embedding_function

    def set_llm(self, llm : LLM) -> None:
        """changes the default embedding function used by langchain.

        Parameters
        ----------
        llm : LLM
            a custom langchain LLM wrapper. see\
            https://python.langchain.com/docs/modules/model_io/models/llms/custom_llm\
            for more
        """
        self.ss.llm = llm

    def set_chain(self, chain) -> None:
        """changes the default langchain chain implementation. if you use this then
        the current state of the SemanticSearch object will not be used. instead
        the chain should provide all the state needed.

        Parameters
        ----------
        chain : LLMChain
            the chain to be used, this will use the llm, embedding function etc. you\
            provide.
        """
        self.ss.chain = chain

    def build(self) -> SemanticSearch:
        """finalizes the build process and returns the final SemanticSearch object.

        Returns
        -------
        SemanticSearch
            the built semantic search object
        """
        # update the chain
        self.chain = LLMChain(
                llm=self.llm, 
                prompt=self.prompt_template,
                # include the necessary output parser
            )
        
        return self.ss
