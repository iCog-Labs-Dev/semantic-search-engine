from flask import Flask, request
from flask_cors import CORS
from src.LLM.llama import semantic_search
from src.database.chroma import *
from environment import *

port_no = 5000



upsert_channels(['random', 'general'])

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