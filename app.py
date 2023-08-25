from flask import Flask, request
from flask_cors import CORS
from src.llm.semantic_search import SemanticSearch as s
from src.llm.llama import TogetherLLM


port_no = 5000

app = Flask(__name__)

@app.route("/", methods=['GET', 'POST'])
def semantic_search_query():

  if request.method == 'GET':
    # query = request.args.get('query')
    return 'Send a POST request!'

  elif request.method == 'POST':
    query = request.json['query']
    api_key = request.json['together_api_key']
    model_name = request.json['together_model_name']
    embedding_model_hf = request.json['embedding_model_hf']
    embedding_api_url = request.json['embedding_api_url']

    return s.semantic_search(
      query=query,
      api_key=api_key,
      model_name=model_name,
      embedding_model_hf=embedding_model_hf,
      embedding_api_url=embedding_api_url
      )

@app.route("/start-model", methods=['GET', 'POST'])
def start_model():
  if request.method == 'GET':
    # api_key = request.args.get('api_key')
    # llm = request.args.get['llm']
    return '<h4> Send a POST request with: "together_api_key" & "model_name" </h4>'

  elif request.method == 'POST':
    api_key = request.json['together_api_key']
    model = request.json['model_name']
    return TogetherLLM(
      together_api_key=api_key,
      model=model
    ).start_model()

@app.route("/stop-model", methods=['GET', 'POST'])
def stop_model():
  if request.method == 'GET':
    return '<h4> Send a POST request with: "together_api_key" & "model_name" </h4>'

  elif request.method == 'POST':
    api_key = request.json['together_api_key']
    model = request.json['model_name']
    return TogetherLLM(
      together_api_key=api_key,
      model=model
    ).stop_model()


print(f"Server running on port {port_no}....")
app.run(port=port_no)