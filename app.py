from flask import Flask, request
from flask_cors import CORS
from src.llm.semantic_search import SemanticSearch as s
# from src.database.chroma import *
from environment import *

port_no = 5000



# upsert_channels(['random', 'general'])

app = Flask(__name__)


@app.route("/", methods=['GET', 'POST'])
def semantic_search_query():

  if request.method == 'GET':
    query = request.args.get('query')
    return s.semantic_search(query)

  elif request.method == 'POST':
    query = request.json['query']
    return s.semantic_search(query)
  
print(f"Server running on port {port_no}....")
app.run(port=port_no)