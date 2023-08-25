import requests
import ast

class Embedding:

  def __init__(self, embedding_model_hf, embedding_api_url):
    self.embedding_model_hf = embedding_model_hf 
    self.embedding_api_url = embedding_api_url

  # Get the list of embeddings for all messages in a channel
  def embed_channel_messages(self, channel_messages):
    msg_list = channel_messages.astype(str).tolist()
    post_data = {
              'link': self.embedding_model_hf ,
              # 'query': "['hi','hello']"
              'query': str(msg_list)
            }

    embeddings = requests.post(self.embedding_api_url, data = post_data, headers = {"Content-Type": "application/x-www-form-urlencoded"})

    return ast.literal_eval(embeddings.text)

  # Get the corresponding embedding for the user's query
  def embed_query(self, query):
    post_data = {
              'link': self.embedding_model_hf ,
              # 'query': "['hi','hello']"
              'query': str([query])
            }

    embeddings = requests.post(self.embedding_api_url, data = post_data, headers = {"Content-Type": "application/x-www-form-urlencoded"}, timeout=120)

    return ast.literal_eval(embeddings.text)[0]