import sys
sys.path.append('./src')
from flask import Flask, request, Response
from flask_cors import CORS
import threading
import os
import shelve
from semantic_search_engine.semantic_search import SemanticSearch
from semantic_search_engine.mattermost.mattermost import Mattermost
from semantic_search_engine.mattermost.mm_api import MattermostAPI as MM_Api
from semantic_search_engine.slack.slack import Slack
from semantic_search_engine.slack.models import User, Channel, ChannelMember, Message
from semantic_search_engine.constants import FETCH_INTERVAL_SHELVE, LAST_FETCH_TIME_SHELVE, MM_PAT_SHELVE, MM_API_URL_SHELVE, CHROMA_N_RESULTS_SHELVE, TEMP_SLACK_DATA_PATH


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
        res['fetch_interval'] = fetch_interval_db[FETCH_INTERVAL_SHELVE]

    with shelve.open(LAST_FETCH_TIME_SHELVE) as last_fetch_time_db:
        res['last_fetch_time'] = last_fetch_time_db[LAST_FETCH_TIME_SHELVE] * 1000
        
    res['is_syncing'] = mattermost.is_syncing()

    return res

# =========== Test Chroma ===========
# TODO: remove this endpoint
@app.route('/query_db/<db>', methods=['POST'])
def chroma_route(db):
    if db == 'chroma':
        query = request.json['query']
        n_results = request.json['n_results']
        source = request.json['source']
        user_id = request.json['user_id']
        channels_list = MM_Api().get_user_channels(user_id=user_id) if source == 'mm' else ['']

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
    
    elif db == 'sqlite':
        table = request.json['table']
        if table == 'User': rows = User.select().dicts()
        elif table == 'Message': rows = Message.select().dicts()
        elif table == 'Channel': rows = Channel.select().dicts()
        elif table == 'ChannelMember': rows = ChannelMember.select().dicts()
        else: return 'Enter a valid table name'
        res = [row for row in rows]
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
    
# ************************************************************** /start_sync
    
@app.route('/start_sync', methods=['GET', 'POST'])
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
                mm_api_url_db[MM_API_URL_SHELVE] = body['mm_api_url']
        else:
            return 'Mattermost API URL not set!'
        
        try:
            sync_thread = threading.Thread(target=mattermost.start_sync)
            sync_thread.start()
        except: return 'Something went wrong while attempting to sync!'

        return {
            "is_syncing": mattermost.is_syncing()
        }

# ************************************************************** /stop_sync
 
@app.route('/stop_sync', methods=['GET'])
def stop_sync():
    mattermost.stop_sync()
    return {
            "is_syncing": mattermost.is_syncing()
        }

# ************************************************************** /upload_slack_zip
@app.route('/upload_slack_zip', methods= ['GET', 'POST'])
def save_slack_zip():
    if request.method == 'GET':
        return '''<pre><h4> Send a POST request: <br>
        MultipartFormData    
            file = (Zip file containing slack export data)
    </h4></pre>'''

    elif request.method == 'POST':
        if "file" not in request.files:
            return Response("{ 'error' : 'File Not Sent' }", status=500, mimetype='application/json')
        file = request.files["file"]
        file_path = os.path.join(TEMP_SLACK_DATA_PATH, 'slack-export-data.zip')

        file.save(file_path)            # Save the zip file
        channel_details = slack.upload_slack_data_zip(file_path)    # Extract it and read the channel details
        os.remove(file_path)            # Delete the zip file

    # return Response(channel_details, status=500, mimetype='application/json')
    return channel_details

# ************************************************************** /store_slack_data

@app.route('/store_slack_data', methods= ['GET', 'POST'])
def store_data():
    if request.method == 'GET':
        return '''<pre><h4> Send a POST request: <br>
    {   
        "channel_id" : {
            "store_all" : true | false,
            "store_none" : true | false,
            "start_date" : (start date in POSIX time),
            "end_date" : (end date in POSIX time)
        },
        ...
    } </h4></pre>'''

    elif request.method == 'POST':
        channel_specs = request.get_json()
        slack.store_slack_data(channel_specs=channel_specs)

        #TODO: should return progress in real-time (channel by channel)
        return Response("{ 'message' : 'Slack data stored!' }", status=200, mimetype='application/json')

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
    
    return Response("{ 'message' : 'Reset Successful!' }", status=200, mimetype='application/json')

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
                mm_pat_db[MM_PAT_SHELVE] = body['personal_access_token']
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
                fetch_interval_db[FETCH_INTERVAL_SHELVE] = int( body['fetch_interval'] )
                mattermost.update_fetch_interval(fetch_interval_db[FETCH_INTERVAL_SHELVE])
                return dict(fetch_interval_db)
        else:
            return 'Please provide a fetch interval!'

# ************************************************************** /set_chroma_n_results

@app.route('/set_chroma_n_results', methods=['GET', 'POST'])
def set_chroma_n_results():
    if request.method == 'GET':
        return '''<pre><h4> Send a POST request: <br>
    {
        "chroma_n_results": "the no. of messages given to the LLM as context"
    } </h4></pre>'''

    elif request.method == 'POST':
        body = request.get_json()

        if body.get("chroma_n_results", False): 
            with shelve.open( CHROMA_N_RESULTS_SHELVE ) as chroma_n_results_db:
                chroma_n_results_db[CHROMA_N_RESULTS_SHELVE] = int( body['chroma_n_results'] )
                return dict(chroma_n_results_db)
        else:
            return 'Please provide the number of messages / results to be used as context!'


port_no = os.environ.get('PORT', 5555)

print(f"Server running on port {port_no}...")
app.run(port=int(port_no), debug=True)
