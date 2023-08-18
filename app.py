from flask import Flask, request
from src.LLM.methods import *
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
print("Server running....")

app.run(port=port_no)