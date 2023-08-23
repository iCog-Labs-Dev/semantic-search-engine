from flask import Flask, request
from flask_cors import CORS
from src.LLM.methods import *
import os

os.environ["TOGETHER_API_KEY"] = "ac17a88fb15afc19f632fc58d39d177814f3ead1d013f7adc9bce9f3ccf33580"
os.environ["NGROK_AUTH_TOKEN"] = "2UKtqNC7pDrDKG272UqIOy4rvSm_2ezkSxzZ7LDUBey1S2dM6"

os.environ["EMBEDDING_URL"] = 'https://hackingfaces.onrender.com/embed'
os.environ["EMBEDDING_MODEL_SPACE_LINK"] = 'https://huggingface.co/spaces/tollan/instructor-xl'
# os.environ["EMBEDDING_MODEL_SPACE_LINK"] = 'https://huggingface.co/spaces/tollan/sentence-transformers-embedding'

port_no = 5000

app = Flask(__name__)


@app.route("/", methods=['GET', 'POST'])
def semantic_search_query():

  if request.method == 'GET':
    query = request.args.get('query')
    return semantic_search(query)

  elif request.method == 'POST':
    query = request.json['query']
    return semantic_search(query)
  
print(f"Server running on port {port_no}....")
app.run(port=port_no)