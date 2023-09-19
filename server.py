from flask import Flask, request
from flask_cors import CORS
from src.semantic_search import SemanticSearch
from src.mattermost import Mattermost
import os

app = Flask(__name__)
CORS(app)

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
        "query" : "What did someone say about something?"
    } </h4></pre>'''

    elif request.method == 'POST':
        query = request.json['query']

        return SemanticSearch().semantic_search(query=query)
    
@app.route('/start-sync', methods=['GET'])
def start_sync():
    Mattermost().getAllPosts()

# ************************************************************** /delete_collection

# @app.route('/delete_collection', methods=['GET', 'POST'])
# def reset_vector_db():
#     if request.method == 'GET':
#         return '''<pre><h4> Send a POST request: <br>
#     {
#       "collection_name": "slack_collection"
#     }
#     </h4></pre>'''

#     elif request.method == 'POST':
#         collection_name = request.json['collection_name']

#         return app_init.chroma().delete_collection(
#             collection_name=collection_name
#         )
    
port_no = os.environ.get('PORT', 5555)

print(f"Server running on port {port_no}....")
app.run(port=int(port_no))