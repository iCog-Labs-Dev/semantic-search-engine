from langchain import LLMChain
from src.llm.prompt import Prompt
from src.llm.llama import TogetherLLM
from src.database.slack.slack import Slack
from src.database.chroma import Chroma
from src.embedding.embedding import Embedding
from src.utils.app_init import AppInit

class SemanticSearch:

    # DEFAULT_SYSTEM_PROMPT = """\
    #     You are a helpful, respectful and honest assistant. Always answer as helpfully as possible, while being safe. Your answers should not include any harmful, unethical, racist, sexist, toxic, dangerous, or illegal content. Please ensure that your responses are socially unbiased and positive in nature.
    #     If a question does not make any sense, or is not factually coherent, explain why instead of answering something not correct. If you don't know the answer to a question, please don't share false information.\
    # """

    def semantic_search(query, api_key):

        app = AppInit()

        llm_chain = LLMChain(
            llm =  app.llm(
                together_api_key=api_key
            ),
            prompt = app.prompt().get_prompt(),
            verbose = False
            # memory= app.prompt.get_buffer_memory()
        )
        # llm_chain.predict(context="Alice: What's an LLM? \n Bob: It's an abbreviation for Large Langage Model.", user_input="Hi, my name is Sam")

        slack = Slack(
            collection = app.chroma().get_collection("slack_collection"),
            slack_data_path = "./src/database/slackdata/",
            embedding = app.embedding()
        )

        context, metadata = slack.get_data_from_chroma(query, num_results=5) # ,condition = { "channel": {"$eq": "general"}, "user_id": {"$in": ["U05D1SQDNSH", "U05DHDPL4FK", "U05CQ93C3FZ", "U05D4M7RGQ3"]} }

        response = llm_chain.predict(context=context, user_input=query)

        return {'response': str(response), 'metadata': metadata}
