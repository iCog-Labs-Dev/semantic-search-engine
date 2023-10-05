from flask import Flask, request, Response
from flask_cors import CORS
import threading
import os
import shelve
from semantic_search_engine.semantic_search import SemanticSearch
from semantic_search_engine.mattermost.mattermost import Mattermost
from semantic_search_engine.mattermost.mm_api import MattermostAPI as MM_Api
from semantic_search_engine.slack.slack import Slack
from semantic_search_engine.constants import FETCH_INTERVAL_SHELVE, SHELVE_FIELD, LAST_FETCH_TIME_SHELVE, MM_PAT_SHELVE, MM_API_URL_SHELVE, TEMP_SLACK_DATA_PATH


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
    res = {}
    with shelve.open(FETCH_INTERVAL_SHELVE) as fetch_interval_db:
        res['fetch_interval'] = fetch_interval_db[SHELVE_FIELD]

    with shelve.open(LAST_FETCH_TIME_SHELVE) as last_fetch_time_db:
        res['last_fetch_time'] = last_fetch_time_db[SHELVE_FIELD] * 1000
        
    res['is_syncing'] = mattermost.is_syncing()

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
                    "$and": [
                        {   "$or": [
                                {
                                    "access": {
                                        "$eq": "pub"
                                    }
                                },
                                {
                                    "channel_id": {
                                        "$in": channels_list
                                    }
                                }
                            ]
                        },
                        {
                            "source" : { "$eq" : source }
                        }
                    ]
                }
            )
        res['channel_list'] = channels_list
    
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
    
@app.route('/start-sync', methods=['GET', 'POST'])
def start_sync():
    if request.method == 'GET':
        return '''<pre><h4> Send a POST request: <br>
    {
        "mm_api_url" : "the URL of the mattermost API"
    } </h4></pre>'''

    elif request.method == 'POST':
        body = request.get_json()

        # Update the API URL in shelve
        if body.get("mm_api_url", False):
            with shelve.open( MM_API_URL_SHELVE ) as mm_api_url_db:
                mm_api_url_db[SHELVE_FIELD] = body['mm_api_url']
        else:
            return 'Mattermost API URL not set!'
        
        try:
            sync_thread = threading.Thread(target=mattermost.start_sync)
            sync_thread.start()
        except: return 'Something went wrong while attempting to sync!'

        return {
            "is_syncing": mattermost.is_syncing()
        }

# ************************************************************** /stop-sync
 
@app.route('/stop-sync', methods=['GET'])
def stop_sync():
    mattermost.stop_sync()
    return {
            "is_syncing": mattermost.is_syncing()
        }

# ************************************************************** /slack
@app.route('/upload-slack-zip', methods= ['POST'])
def save_slack_zip():
    
    file_path = os.path.join(TEMP_SLACK_DATA_PATH, 'slack-export-data.zip')

    if "file" not in request.files:
        return Response("{ 'error' : 'File Not Sent' }", status=500, mimetype='application/json')
    
    file = request.files["file"]

    file.save(file_path)            # Save the zip file
    slack.extract_zip(file_path)    # Extract it
    os.remove(file_path)            # Delete the zip file

    # TODO: should return list of channels
    return Response("{ 'message' : 'Successfully Extracted!' }", status=500, mimetype='application/json')

# ************************************************************** /slack

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

# ************************************************************** /set_personal_access_token

@app.route('/set_personal_access_token', methods=['GET', 'POST'])
def set_personal_access_token():
    if request.method == 'GET':
        return '''<pre><h4> Send a POST request: <br>
    {
        "personal_access_token": "the pesonal access token of an admin user"
    } </h4></pre>'''

    elif request.method == 'POST':
        body = request.get_json()

        if body.get("personal_access_token", False): 
            with shelve.open( MM_PAT_SHELVE ) as mm_pat_db:
                mm_pat_db[SHELVE_FIELD] = body['personal_access_token']
                return dict(mm_pat_db)
        else:
            return 'Please provide a personal access token!'


# ************************************************************** /set_fetch_interval

@app.route('/set_fetch_interval', methods=['GET', 'POST'])
def set_fetch_interval():
    if request.method == 'GET':
        return '''<pre><h4> Send a POST request: <br>
    {
        "fetch_interval": "the time interval between fetches (in seconds)"
    } </h4></pre>'''

    elif request.method == 'POST':
        body = request.get_json()

        if body.get("fetch_interval", False): 
            with shelve.open( FETCH_INTERVAL_SHELVE ) as fetch_interval_db:
                fetch_interval_db[SHELVE_FIELD] = int( body['fetch_interval'] )
                return dict(fetch_interval_db)
        else:
            return 'Please provide a fetch interval!'



port_no = os.environ.get('PORT', 5555)

print(f"Server running on port {port_no}...")
app.run(port=int(port_no), debug=True)
