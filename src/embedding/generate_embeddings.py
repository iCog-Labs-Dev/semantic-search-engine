import requests
import ast
import os

from environment import *


url = os.environ["EMBEDDING_URL"] 
embedding_model_url = os.environ["EMBEDDING_MODEL_SPACE_LINK"] 

# Get the list of embeddings for all messages in a channel
def embed_channel_messages(channel_messages):
  msg_list = channel_messages.astype(str).tolist()
  post_data = {
            'link': embedding_model_url ,
            # 'query': "['hi','hello']"
            'query': str(msg_list)
          }

  embeddings = requests.post(url, data = post_data, headers = {"Content-Type": "application/x-www-form-urlencoded"})

  return ast.literal_eval(embeddings.text)

# Get the corresponding embedding for the user's query
def embed_query(query):
  post_data = {
            'link': embedding_model_url ,
            # 'query': "['hi','hello']"
            'query': str([query])
          }

  embeddings = requests.post(url, data = post_data, headers = {"Content-Type": "application/x-www-form-urlencoded"}, timeout=120)

  return ast.literal_eval(embeddings.text)[0]