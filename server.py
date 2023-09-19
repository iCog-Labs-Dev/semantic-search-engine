from flask import Flask, request
from flask_cors import CORS
from semantic_search_engine.semantic_search import SemanticSearch
from semantic_search_engine.mattermost import Mattermost
from semantic_search_engine.llm import TogetherLLM as together
import os

app = Flask(__name__)
CORS(app)

# ************************************************************** /

@app.route('/', methods=['GET'])
def root_route():
    if request.method == 'GET':
        return '''<h1>Hi ✋</h1>'''


# ************************************************************** /search


@app.route('/search', methods=['GET', 'POST'])
def semantic_search():
    if request.method == 'GET':
        # query = request.args.get('query')
        return '''<pre><h4> Send a POST request: <br>
    {
        "query" : "What did someone say about something?",
        "user_id": "The id of the currently logged in user"
    } </h4></pre>'''

    elif request.method == 'POST':
        query = request.json['query']
        user_id = request.json['user_id']

        return SemanticSearch().semantic_search(query=query, user_id=user_id)
    
# ************************************************************** /start-sync
    
@app.route('/start-sync', methods=['GET'])
def start_sync():
    together().start()
    Mattermost().start_sync()

# ************************************************************** /stop-sync
 
@app.route('/stop-sync', methods=['GET'])
def stop_sync():
    together().stop()
    Mattermost().stop_sync()

# ************************************************************** /slack
@app.route('/slack', methods=['GET', 'POST'])
def upsert_slack():
    pass
    # TODO: upsert slack data from file to chroma


# ************************************************************** /reset-all

@app.route('/reset-all', methods=['GET', 'POST'])
def reset_all():
    pass
#     TODO: delete the chroma collection
#     TODO: delete the 'slack' and 'last_fetch_time' stores

port_no = os.environ.get('PORT', 5555)

print(f"Server running on port {port_no}....")
app.run(port=int(port_no))