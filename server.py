from flask import Flask, request, jsonify
from flask_cors import CORS
import threading
import os
import shelve
from semantic_search_engine.semantic_search import SemanticSearch
from semantic_search_engine.mattermost.mattermost import Mattermost
from semantic_search_engine.mattermost.mm_api import MattermostAPI as MM_Api
from semantic_search_engine.slack.slack import Slack

#Test
from semantic_search_engine import constants
# from semantic_search_engine.slack.slack import extract_zip, channels, users, all_channels
from io import BytesIO
from semantic_search_engine.chroma import ChromaSingleton

app = Flask(__name__)
CORS(app)

semantic_client = SemanticSearch()
collection = semantic_client.collection
mattermost = Mattermost(collection)
slack = Slack(collection)
# ************************************************************** /

@app.route('/', methods=['GET'])
def root_route():
    # return '''<h1>Hi ✋</h1>'''
    with shelve.open(constants.SETTINGS_SHELVE_NAME) as settings:
        res = dict(settings)
        res['is_syncing'] = mattermost.is_syncing()
    with shelve.open(constants.FETCH_TIME_SHELVE_NAME) as fetch_time:
        res['last_fetch_time'] = fetch_time[constants.FETCH_TIME_SHELVE_NAME] * 1000

    return res

# =========== Test Chroma ===========
# TODO: remove this endpoint
@app.route('/chroma/<action>', methods=['POST'])
def chroma_route(action):
    query = request.json['query']
    n_results = request.json['n_results']
    source = request.json['source']
    user_id = request.json['user_id']

    channels_list = MM_Api().get_user_channels(user_id=user_id)

    if action == 'query':
        res = semantic_client.collection.query(
                query_texts=[query],
                n_results=n_results,
                where = {
                    "$or": [
                            {
                                "access": {
                                    "$eq": "pub"
                                }
                            },
                            {
                                "channel_id": {
                                    "$in": channels_list
                                }
                            },
                            {
                            "source" : { "$eq" : source }
                            }
                        ]
                    }
            )
        res['alist'] = channels_list
    
        return res


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

        return semantic_client.semantic_search(query=query, user_id=user_id)
    
# ************************************************************** /start-sync
    
@app.route('/start-sync', methods=['GET'])
def start_sync():
    try:
        sync_thread = threading.Thread(target=mattermost.start_sync)
        sync_thread.start()
    except: return 'Something went wrong!'

    return 'Started sync!'

# ************************************************************** /stop-sync
 
@app.route('/stop-sync', methods=['GET'])
def stop_sync():
    mattermost.stop_sync()
    return 'Stopped sync!'

# ************************************************************** /slack
@app.route('/upload-slack-zip', methods= ['POST'])
def save_slack_zip():
    temp_path = constants.TEMP_SLACK_DATA_PATH
    file_path = os.path.join(temp_path, 'slack-export-data.zip')

    if "file" not in request.files:
        return jsonify({
            "error" : "File Not Sent"
        })
    
    os.makedirs(temp_path, exist_ok=True)
    file = request.files["file"]

    file.save(file_path)            # Save the zip file
    slack.extract_zip(file_path)    # Extract it
    os.remove(file_path)            # Delete the zip file

    # TODO: should return list of channels
    return 'Extracted!'

@app.route('/import-slack-data', methods= ['POST'])
def import_data():
    slack.import_slack_data()

    return 'Imported!'

# ************************************************************** /reset

@app.route('/reset', methods=['GET', 'POST'])
def reset_all():
    if request.method == 'GET':
        return '''<pre><h4> Send a POST request: <br>
    {
        "mattermost" : true | false,
        "slack" : true | false
    } </h4></pre>'''

    elif request.method == 'POST':
        body = request.get_json()

        if body.get("mattermost", False):
            mattermost.reset_mattermost()

        if body.get("slack", False):
            slack.reset_slack()
    
    return 'Reset Successful!'

# ************************************************************** /settings

@app.route('/settings', methods=['GET', 'POST'])
def settings():
    if request.method == 'GET':
        return '''<pre><h4> Send a POST request: <br>
    {
        "mattermost_api_url" : "the URL of the mattermost server",
        "fetch_interval" : "interval to sync messages (in minutes)",
        "personal_access_token": "the pesonal access token of an admin user"
    } </h4></pre>'''

    elif request.method == 'POST':
        body = request.get_json()
        res = {}

        with shelve.open(constants.SETTINGS_SHELVE_NAME) as settings:
            if 'mattermost_api_url' in body: 
                settings['mattermost_api_url'] = body['mattermost_api_url']
            
            if 'mattermost_url' in body: 
                settings['mattermost_url'] = body['mattermost_url']

            if 'fetch_interval' in body: 
                settings['fetch_interval'] = body['fetch_interval']
                mattermost.update_fetch_interval(int(settings['fetch_interval']))

            if 'personal_access_token' in body:  
                settings['personal_access_token'] = body['personal_access_token']

            res = dict(settings)

        res['is_syncing'] = mattermost.is_syncing()

        return res or 'Something went wrong!'



port_no = os.environ.get('PORT', 5555)

print(f"Server running on port {port_no}...")
app.run(port=int(port_no), debug=True)
