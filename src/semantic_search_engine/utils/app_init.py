from semantic_search_engine.database.slack.slack import Slack
from semantic_search_engine.database.chroma import Chroma
from semantic_search_engine.embedding.embedding import Embedding
from semantic_search_engine.llm.together_llm import TogetherLLM
from semantic_search_engine.llm.prompt import Prompt
from semantic_search_engine.database.slack.pull_from_repo import FetchFromRepo

class AppInit:

    # together_api_key = '------------------------'
    together_model_name = 'togethercomputer/llama-2-70b-chat'
    embedding_model_hf = 'https://huggingface.co/spaces/tollan/instructor-xl'
    embedding_api_url = 'https://hackingfaces.onrender.com/embed'
    collection_name = 'slack_collection'


    def pull_from_repo(self, repo_url):
        pull_from_repo = FetchFromRepo(
            repo_url = repo_url
        )

        return pull_from_repo

    def embedding(self):
        embedding = Embedding(
            embedding_model_hf = self.embedding_model_hf,
            embedding_api_url = self.embedding_api_url
        )

        return embedding
    
    def chroma(self):
        chroma = Chroma(
            path_to_db = "./chroma_db"
        )

        return chroma

    def slack(self):
        chroma_collection = self.chroma().get_collection(self.collection_name)

        slack = Slack(
            collection=chroma_collection,
            slack_data_path='./src/database/slackdata/',
            embedding=self.embedding()
        )

        return slack

    def llm(self, together_api_key):
        # llm = HuggingFacePipeline(pipeline = pipe, model_kwargs = {'temperature':0})
        llm = TogetherLLM(
            model= self.together_model_name,
            together_api_key=together_api_key,
            temperature=0.1,
            max_tokens=512
        )

        return llm
    
    def prompt(self):
        prompt = Prompt(
            system_prompt = """\
                You are a helpful assistant, you always only answer for the assistant then you stop. You will only answer the question the Human asks.
                You will be given a sequence of chat messages related to a certain topic. Write a response that answers the question based on what is discussed in the chat messages.
                You must answer the question based on only chat messages you are given.
                Don't answer anything outside the context you are provided and do not respond with anything from your general knowledge.
                Try to mention the ones that you get the context from.
                If there isn't enough context, simply reply "This topic was not discussed previously"\
            """, # or DEFAULT_SYSTEM_PROMPT,
                # You may also look at the chat history to get additional context if necessary.
            instruction = """\
                ### Chat Messages (Context): \n\n{context} \n\n\n
                Human: {user_input} \nAssistant:\n \
            """
                ### Chat History: \n\n{chat_history} \n
        )

        return prompt