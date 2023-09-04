from semantic_search_engine.llm import TogetherAI, Llama
from semantic_search_engine.chroma import ChromaSingleton
from langchain import LLMChain
class SemanticSearch:

    @classmethod
    def semantic_search(cls, query, api_key):
        """_summary_
        Parameters
        ----------
        query : str
            _description_
        api_key : str
            _description_
        """

        llm = TogetherAI().get_llm()

        vector_db = ChromaSingleton()

        chain = LLMChain(
                llm=llm, 
                prompt="",
                # include the necessary output parser
            )
        
        chain.run()
