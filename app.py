from flask import Flask, request
from flask_cors import CORS
from src.llm.semantic_search import SemanticSearch as s
from src.llm.llama import TogetherLLM
from src.database.slack.pull_from_repo import FetchFromRepo
from src.database.slack.slack import Slack
from src.database.chroma import Chroma  # Shouldn't be imported here
import ast


port_no = 5000

app = Flask(__name__)


# ************************************************************** /search

@app.route("/search", methods=['GET', 'POST'])
def semantic_search_query():
  if request.method == 'GET':
    # query = request.args.get('query')
    return '''<pre><h4> Send a POST request: <br>
    {
        "query" : "What did someone say about something?",
        "together_api_key": "---------------------------",
        "together_model_name": "togethercomputer/llama-2-70b-chat",
        "embedding_model_hf": "https://huggingface.co/spaces/tollan/instructor-xl",
        "embedding_api_url": "https://hackingfaces.onrender.com/embed"
    } </h4></pre>'''

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


# ************************************************************** /togetherai/<action>

@app.route("/togetherai/<action>", methods=['GET', 'POST'])
def start_model(action):
  if request.method == 'GET':
    return '''<pre><h4> Send a POST request:<br>
    {
        "together_api_key": "---------------------------",
        "model_name": "togethercomputer/llama-2-70b-chat"
    } </h4></pre>'''

  elif request.method == 'POST':
    # action = request.args.get('action')
    api_key = request.json['together_api_key']
    model = request.json['model_name']

    together = TogetherLLM(
      together_api_key=api_key,
      model=model
    )

    return together.start_model() if action=='start' else together.stop_model()


# ************************************************************** /pull

@app.route('/pull', methods=['GET', 'POST'])
def pull_or_clone():
  if request.method == 'GET':
    return '''<pre><h4> Send a POST request: <br>
    {
      "repo_url": "https://github.com/TollanBerhanu/MatterMost-LLM-test-Slack-export-Jun-19-2023---Jun-20-2023.git"
    }
    </h4></pre>'''
  
  elif request.method == 'POST':
    repo_url = request.json['repo_url']

    return FetchFromRepo(
      repo_url=repo_url
    ).fetch_slack_export_from_github()

# ************************************************************** /upsert
# TODO: find a better spot (maybe in the 'Slack' module)
@app.route('/upsert', methods=['GET', 'POST'])
def upsert_to_db():
  if request.method == 'GET':
    return '''<pre><h4> Send a POST request: <br>
    {
      "channel_names": "['random', 'test', 'general']"
    }

    ** Passing an empty array will upsert all channels **
    </h4></pre>'''
  
  elif request.method == 'POST':
    channel_names = request.json['channel_names']
    # step = request.json['step']

    return Slack().upsert_channels(
      channel_names=ast.literal_eval(channel_names.text)
      # step=step
    )
# ************************************************************** /delete_all
# TODO: find a better spot (maybe in the 'Slack' module)
@app.route('/delete_all', methods=['GET', 'POST'])
def reset_vector_db():
  if request.method == 'GET':
    return '''<pre><h4> Send a POST request: <br>
    {
      "path_to_db": "./chroma_db",
      "collection_name": "slack_collection"
    }

    ** Passing an empty array will upsert all channels **
    </h4></pre>'''
  
  elif request.method == 'POST':
    path_to_db = request.json['path_to_db']
    collection_name = request.json['collection_name']

    return Chroma(
      path_to_db=path_to_db
    ).delete_collection(collection_name)   # Shouldn't be called here

print(f"Server running on port {port_no}....")
app.run(port=port_no)