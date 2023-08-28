from langchain import LLMChain
from src.llm.prompt import Prompt
from src.llm.llama import TogetherLLM
from src.database.slack.slack import Slack
from src.database.chroma import Chroma
from src.embedding.embedding import Embedding

class SemanticSearch:

    # DEFAULT_SYSTEM_PROMPT = """\
    #     You are a helpful, respectful and honest assistant. Always answer as helpfully as possible, while being safe. Your answers should not include any harmful, unethical, racist, sexist, toxic, dangerous, or illegal content. Please ensure that your responses are socially unbiased and positive in nature.
    #     If a question does not make any sense, or is not factually coherent, explain why instead of answering something not correct. If you don't know the answer to a question, please don't share false information.\
    # """

    def semantic_search(query, api_key, model_name, embedding_model_hf, embedding_api_url):

        prompt = Prompt(
            system_prompt = """\
                You are a helpful assistant, you always only answer for the assistant then you stop. You will only answer the question the Human asks.
                You will be given a sequence of chat messages related to a certain topic. Write a response that answers the question based on what is discussed in the chat messages.
                You must answer the question based on only chat messages you are given.
                Don't answer anything outside the context you are provided and do not respond with anything from your general knowledge.
                Try to mention the ones that you get the context from.
                You may also look at the chat history to get additional context if necessary.
                If there isn't enough context, simply reply "This topic was not discussed previously"\
            """, # or DEFAULT_SYSTEM_PROMPT,
            instruction = """\
                ### Chat Messages (Context): \n\n{context} \n\n\n
                ### Chat History: \n\n{chat_history} \nHuman: {user_input} \nAssistant:\n \
            """
        )
        search_prompt = prompt.get_prompt()
        # memory = prompt.get_buffer_memory()

        # llm = HuggingFacePipeline(pipeline = pipe, model_kwargs = {'temperature':0})
        llm = TogetherLLM(
            model= model_name,
            together_api_key=api_key,
            temperature=0.1,
            max_tokens=512
        )

        llm_chain = LLMChain(
            llm=llm,
            prompt=search_prompt,
            verbose=False
            # memory=memory
        )
        # llm_chain.predict(context="Alice: What's an LLM? \n Bob: It's an abbreviation for Large Langage Model.", user_input="Hi, my name is Sam")

        chroma_db = Chroma(
            path_to_db = "./chroma_db"
        )
        chroma_collection = chroma_db.get_collection("slack_collection")

        embedding = Embedding(
            embedding_model_hf = embedding_model_hf,
            embedding_api_url = embedding_api_url
        )

        slack = Slack(
            collection=chroma_collection,
            slack_data_path="./src/database/slackdata/",
            embedding=embedding
        )

        context, metadata = slack.get_data_from_chroma(query, num_results=5) # ,condition = { "channel": {"$eq": "general"}, "user_id": {"$in": ["U05D1SQDNSH", "U05DHDPL4FK", "U05CQ93C3FZ", "U05D4M7RGQ3"]} }

        response = llm_chain.predict(context=context, user_input=query)

        return {'response': str(response), 'metadata': metadata}



  
  

        


    # semantic_search("Hello, my name is John.")
    # semantic_search("What did Tollan say about semantic search?")
    # semantic_search("What are some models that are comparable to GPT 3?")
    # semantic_search("How can I make some pancakes?")
    # semantic_search("What's my name?")
    # semantic_search("Alright, Thanks!")