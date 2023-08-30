from flask import Flask, request
from flask_cors import CORS
from src.utils.app_init import AppInit
from src.semantic_search import SemanticSearch as s
import ast
import os


app = Flask(__name__)


app_init = AppInit()
# ************************************************************** /


@app.route('/', methods=['GET'])
def root_route():
    if request.method == 'GET':
        # query = request.args.get('query')
        return '''<h1>Hi ✋</h1>'''


# ************************************************************** /search


@app.route('/search', methods=['GET', 'POST'])
def semantic_search():
    if request.method == 'GET':
        # query = request.args.get('query')
        return '''<pre><h4> Send a POST request: <br>
    {
        "query" : "What did someone say about something?",
        "together_api_key": "---------------------------"
    } </h4></pre>'''

    elif request.method == 'POST':
        query = request.json['query']
        api_key = request.json['together_api_key']

        return s.semantic_search(
            query=query,
            api_key=api_key
        )


# ************************************************************** /togetherai/<action>

@app.route('/togetherai/<action>', methods=['GET', 'POST'])
def start_model(action):
    if request.method == 'GET':
        return '''<pre><h4> Send a POST request:<br>
    {
        "together_api_key": "---------------------------"
    } </h4></pre>'''

    elif request.method == 'POST':
        # action = request.args.get('action')
        api_key = request.json['together_api_key']

        together = app_init.llm(
            together_api_key=api_key
        )

        return together.start_model() if action == 'start' else together.stop_model() if action == 'stop' else "Use routes '/start' or '/stop'"


# ************************************************************** /pull

@app.route('/pull', methods=['GET', 'POST'])
def pull_or_clone():
    if request.method == 'GET':
        return '''<pre><h4> Send a POST request: <br>
    {
      "repo_url": "https://github.com/iCog-Labs-Dev/slack-export-data.git"
    }
    </h4></pre>'''

    elif request.method == 'POST':
        repo_url = request.json['repo_url']

        return app_init.pull_from_repo(
            repo_url=repo_url
        ).fetch_slack_export_from_github()

# ************************************************************** /upsert


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

        return app_init.slack().upsert_channels(
            channel_names=ast.literal_eval(channel_names)
            # step=step
        )
# ************************************************************** /delete_all
# TODO: find a better spot (maybe in the 'Slack' module)


@app.route('/delete_all', methods=['GET', 'POST'])
def reset_vector_db():
    if request.method == 'GET':
        return '''<pre><h4> Send a POST request: <br>
    {
      "collection_name": "slack_collection"
    }
    </h4></pre>'''

    elif request.method == 'POST':
        collection_name = request.json['collection_name']

        return app_init.chroma().delete_collection(
            collection_name=collection_name
        )
    
port_no = os.environ.get('PORT', 5000)

print(f"Server running on port {port_no}....")
# app.run(port=int(port_no))
