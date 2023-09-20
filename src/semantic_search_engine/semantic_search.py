from chromadb import EmbeddingFunction
from semantic_search_engine.llm import TogetherLLM
from semantic_search_engine.chroma import ChromaSingleton
from semantic_search_engine import constants
from langchain import LLMChain, PromptTemplate
from chromadb.utils import embedding_functions
from langchain.llms.base import LLM
from semantic_search_engine.mattermost import Mattermost

class SemanticSearch():
    """The entrypoint to the package that contains the necessary data to 
    make a semantic search.
    """  

    def __init__(self) -> None:
        """initializes the necessary data to perform a semantic search
        """        
        # Sample prompt
        # '''
        # You are a helpful assistant, you will only answer the questions the Human asks. You will be given a chat message as context. \
        # Write a response that explains the human query based on what is discussed in the chat message.You must answer questions using the context provided. \
        # A metadata that contains data related to the chat message will be provided. 
        # The metadata will be a json with a user key that represents the sender of the message and a ts key which is the timestamp of the time the chat message was sent. \
        # Use this data to better explain the chat message. If there isn't enough context, simply reply "This topic was not discussed previously"
        # '''
        # prompt template to be used by a chain
        self.prompt_template = PromptTemplate(
            input_variables=["context", "query"],

            # the system prompt needs work
            template="""
[INST]\n
    <<SYS>>
        * Your name is SNET and you are a helpful semantic search assistant.
        * You will be given a sequence of chat messages as context. 
        * Write a response that answers the question based on what is given to you as context in the chat messages.
        * You must answer the question based on only chat messages you are given.
        * Don't answer anything outside the context you are provided and do not respond with anything from your general knowledge.
        * Try to mention the ones that you get the context from.
        * If there isn't enough context, simply reply "This topic was not discussed previously"
    <</SYS>>\n

    ### Context (chat messages): \n\n{context}\n\n
    ### Query: {query}\n
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
                verbose=True
                # include the necessary output parser
            )
        
        # a chroma collection
        self.collection = ChromaSingleton().\
            get_connection().\
            get_or_create_collection(
                constants.CHROMA_COLLECTION,
                embedding_function= self.embedding_function
            )  # this should ge only get_collection      
        

    # def __filter(self, user_id : str) -> list[str]:
    #     """extracts and returns a list of chat ids in which a user is permitted to view.

    #     Parameters
    #     ----------
    #     user_id : str
    #         the id of the user making the query

    #     Returns
    #     -------
    #     list[str]
    #         a list of chat ids a user is permitted to view
    #     """
    #     # TODO : implement chat filter functionality
   
    def semantic_search(self, query : str, user_id: str):
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
        # TODO: if public or (MM && private && in:channels_list) or slack
        channels_list = Mattermost().get_user_channels(user_id=user_id)
        print(channels_list)

        query_result = self.collection.query(
            query_texts=[query],
            n_results=100
            # Get all messages from slack or specific channels that the user's a member of in MM
            # where = {
            #     "$or" : [
            #         {
            #             "platform" : "sl"
            #         },
            #         # "$and" : [ { "access" : "private" } ]
            #         {
            #             "channel_id" : {
            #                             "$in" : channels_list
            #                            }
            #         }
            #     ]
            # }
        )

        # context = []
        # for msg in query_result["documents"][0]:
        #     context.append('(date) Someone: ' + msg)

        return self.chain.run(
            { 
                "context" : '\n'.join( query_result["documents"][0] ),
                "query" : query    
            }
        )



    

    def get_user_details(self, user_id, *args, datasource = "mm"):
        pass
    
    def get_channel_details(channel_id, *args):
        pass

    def get_message_details(message_id, *args):
        pass





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
