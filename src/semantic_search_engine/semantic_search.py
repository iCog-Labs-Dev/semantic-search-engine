from chromadb import EmbeddingFunction
from semantic_search_engine.llm import TogetherLLM
from semantic_search_engine.chroma import  get_chroma_collection
from semantic_search_engine.constants import CHROMA_N_RESULTS_SHELVE
from langchain import LLMChain, PromptTemplate
from chromadb.utils import embedding_functions
from langchain.llms.base import LLM
from datetime import datetime
from semantic_search_engine.mattermost.mm_api import MattermostAPI as MMApi
from semantic_search_engine.slack.slack import Slack as Sl
import os, shelve

from json import dumps as to_json
from flask import Response

class SemanticSearch():
    """The entrypoint to the package that contains the necessary data to 
    make a semantic search.
    """  

    def __init__(self) -> None:
        """initializes the necessary data to perform a semantic search
        """        
        # Sample prompt
        # '''
        #  * Your name is SNET and you are a helpful semantic search assistant.
        # * You will be given a sequence of chat messages as context. 
        # * Write a response that answers the question based on what is given to you as context in the chat messages.
        # * You must answer the question based on only chat messages you are given.
        # * Don't answer anything outside the context you are provided and do not respond with anything from your general knowledge.
        # * Try to mention the ones that you get the context from.
    # Try to mention the people that you get the context from and the times the messages were posted.
        # * If there isn't enough context, simply reply "This topic was not discussed previously"
        # '''
        # prompt template to be used by a chain
        self.prompt_template = PromptTemplate(
            input_variables=["context", "query", "user"],

            # the system prompt needs work
            template="""
[INST]\n
    <<SYS>>
    You are a helpful assistant and your name is Llama.
    Look at the following chat messages between the triple quotes.

    ### Chat messages:
    ```
    \n{context}\n
    ```

    The following question is asked by '{user}'.

    ### Question: 
    \n{query}\n
    
    Write a response that answers the question based on what is discussed in the chat messages.
    You must answer the question based on only the list of messages you are given.
    Don't answer anything outside the context(messages) you are provided and do not respond with anything from your general knowledge.
    If the messages are not related to the question, respond with "This topic was not discussed previously".
    Do not provide any explanations leading to your response. Your responses should be concise and straightforward. 
    <</SYS>>\n
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
        

        # Get or create a chroma collection
        self.collection = get_chroma_collection(self.embedding_function)

    def semantic_search(self, query : str, user_info: dict, access_token: str):
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
        # Get the number of results to be returned by Chroma from shelve
        with shelve.open(CHROMA_N_RESULTS_SHELVE) as chroma_n_results:
            n_results = int(chroma_n_results[CHROMA_N_RESULTS_SHELVE])
        
        # Initialze MMApi with the user's access_token
        mm_api = MMApi(access_token=access_token)

        # Get the channels list for the user from Mattermost's API
        mm_channels_list = mm_api.get_user_channels(user_id=user_info['user_id'])
        # Get the channels list of Slack
        sl_channels_list = Sl.get_user_channels( user_info['email'] )
        # Concatenate the two lists to get the list of all channel_ids the user can access in Chroma
        channels_list = mm_channels_list + sl_channels_list

        try:
            query_result = self.collection.query(
                query_texts=[query],
                n_results=n_results,
                # Get all messages from slack or specific channels that the user's a member of in MM
                where = { "channel_id": { "$in": channels_list } }
            )
        except Exception as err:
            return Response(to_json({
                'message' : 'Failed to add to Chroma!',
                'log': err
                }), status=500, mimetype='application/json')

        # Get the details for each user, channel and message returned from chroma
        try:
            metadata_details = self.get_metadata_details(
                mm_api=mm_api,
                ids=query_result["ids"][0],
                metadatas=query_result["metadatas"][0],
                distances=query_result["distances"][0]
            )
        except Exception as err:
            return Response(to_json({
                'message' : 'Fetching context details failed!',
                'log': err
                }), status=500, mimetype='application/json')

        # Get the response from the LLM
        try:
            llm_response = self.chain.run(
                { 
                    "context" : '\n'.join( query_result["documents"][0] ),
                    "query" : query,
                    "user": user_info['name']
                    # "query" : f"{ user_info['name'] }: { query }"
                }
            )
        except Exception as err:
            return Response(to_json({
                'message' : 'LLM response failed!',
                'log': err
                }), status=500, mimetype='application/json')
        
        return {
            "llm": llm_response,
            "context": metadata_details
        }


    @staticmethod
    def get_metadata_details(mm_api, ids, metadatas, distances):
        response = []

        for idx, metadata in enumerate(metadatas):
            
            schema = {
                "user_name":"",
                "user_dm_link": "",
                "channel_name":"",
                "channel_link":"",
                "message":"",
                "message_link":"",
                "time":"",
                "source":"",
                "access":"",
                "score":""
            }
            if metadata['source']=='mm':
                user_data = mm_api.get_user_details(
                    metadata['user_id'],
                    'first_name', 'last_name', 'username'
                    )
                channel_data = mm_api.get_channel_details(
                    metadata['channel_id'],
                    'name', 'display_name', 'team_id'
                    )

                post_data = mm_api.get_post_details(
                    ids[idx],
                    'id', 'message', 'update_at' # create_at
                    )
                team_data = mm_api.get_team_details(
                    channel_data['team_id'],
                    'name'
                )

                # Look for "api" from the right and cut out the url after that...  "http://localhost:8065/api/v4"  -->  "http://localhost:8065/"
                # mm_url = api_url[: api_url.rfind("api") ]
                
                mm_url = os.getenv("MM_URL")
                link_url = f"{ mm_url }/{ team_data['name'] }"
                            
                schema['user_name'] = user_data['name']                                                     # 1. user_name
                schema['user_dm_link'] = f"{ link_url }/messages/@{ user_data['username'] }"                # 2. user_dm_link

                schema['channel_name'] = channel_data['name']                                               # 3. channel_name 
                schema['channel_link'] = f"{ link_url }/channels/{ channel_data['name'] }"                  # 4. channel_link 
            
                schema['message'] = post_data['message']                                                    # 5. message
                schema['message_link'] = f"{ link_url }/pl/{ post_data['id'] }"                             # 6. message_link
                schema['time'] = (post_data['update_at']) / 1000                                            # 7. time

                schema['source'] = metadata['source']                                                       # 8. source (mm)
                schema['access'] = metadata['access']                                                       # 9. access
                schema['score'] = 1 - distances[idx]                                                        # 10. score
            
            elif metadata['source']=='sl':
                sl_data = Sl.get_user_details( metadata['user_id'] )              
                schema['user_name'] = sl_data['real_name'] or sl_data['name']                               # 1. user_name
                # schema['user_dm_link'] = ...                                                              # 2. user_dm_link  (not applicable to slack)

                sl_data = Sl.get_channel_details( metadata['channel_id'] )    
                schema['channel_name'] = sl_data['name']                                                    # 3. channel_name 
                # schema['channel_link'] = ...                                                              # 4. channel_link       (not applicable to slack)
            
                sl_data = Sl.get_message_details( ids[idx] )   
                schema['message'] = sl_data['text']                                                         # 5. message
                # schema['message_link'] = ...                                                              # 6. message_link       (not applicable to slack)
                ts = round( datetime.timestamp( sl_data['time'] ) , 3)
                schema['time'] = ts                                                                         # 7. time

                schema['source'] = metadata['source']                                                       # 8. source (sl)
                schema['access'] = metadata['access']                                                       # 9. access
                schema['score'] = 1 - distances[idx]                                                        # 10. score
                
            response.append(schema)
        
        return response



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
        self.collection = get_chroma_collection(self.ss.embedding_function)

        # update the chain
        self.chain = LLMChain(
                llm=self.llm, 
                prompt=self.prompt_template,
                # include the necessary output parser
            )
        
        return self.ss
