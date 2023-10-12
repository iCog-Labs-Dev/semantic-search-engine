import sys
sys.path.append('./src')
from flask import Flask, request, Response, redirect, url_for, session
from flask_cors import CORS
from datetime import timedelta
import threading
import os
import shelve

from authlib.integrations.flask_client import OAuth
from mm_oauth import register_oauth_client, login_required

from semantic_search_engine.semantic_search import SemanticSearch
from semantic_search_engine.mattermost.mattermost import Mattermost
from semantic_search_engine.mattermost.mm_api import MattermostAPI as MM_Api
from semantic_search_engine.slack.slack import Slack
from semantic_search_engine.slack.models import User, Channel, ChannelMember, Message
from semantic_search_engine.constants import FETCH_INTERVAL_SHELVE, SHELVE_FIELD, LAST_FETCH_TIME_SHELVE, MM_PAT_SHELVE, MM_API_URL_SHELVE, CHROMA_N_RESULTS_SHELVE, TEMP_SLACK_DATA_PATH

from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__)
CORS(app)   # , resources={r"/*": {"origins": "http://localhost:3000"}})
oauth = OAuth(app)
mm_client = register_oauth_client(oauth=oauth)

# Session config
app.secret_key = os.getenv("APP_SECRET_KEY") or 'some_key_for_session_encryption'
app.config['SESSION_COOKIE_NAME'] = 'mattermost-login-session'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=720)   # 720 - The session lasts for 12 Hours

# semantic_search_engine initializations
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


# ******************************************************** OAUTH *************************************************************
# **************************************************************************************************************************** /

@app.route('/login')
def login():
    google = oauth.create_client('mattermost')  # create the google oauth client
    redirect_uri = url_for('authorize', _external=True)
    return google.authorize_redirect(redirect_uri)

@app.route('/authorize')
def authorize():
    print('Authorized')
    token = oauth.google.authorize_access_token()   # Get access token from Mattermost oauth
    user_info = oauth.google.userinfo()  # uses openId endpoint to fetch user info
    print('TOKEN: ', token)
    print('USER_INFO', user_info)
    # resp.raise_for_status()
    # print(resp.text)
    print(user_info)

    # Here you use the profile/user data that you got and query your database find/register the user and set ur own data in the session not the profile from google
    session['profile'] = {
        "user_id" : user_info['id'],
        "name" : f"{ user_info['first_name'] } { user_info['last_name'] }".strip(),
        "username" : user_info['username'],
        "email" : user_info['email'],
        "role" : user_info['roles'],
        "access_token": token['access_token'],
        "expires_at": token['expires_at'],
    }
    session.permanent = True  # make the session permanant so it keeps existing after browser gets closed
    return ''#redirect('/')

@app.route('/logout')
def logout():
    for key in list(session.keys()):
        session.pop(key)    # Remove the session
    return ''#redirect('/')

@app.route('/test_oauth')
@login_required
def hello_world():
    return dict(session)['profile']['email']

# **************************************************************************************************************************** /

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

        res = collection.query(
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
        rows = Message.select()
        res = []
        for row in rows:
            res.append(row.time)

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

# ************************************************************** /upload-slack-zip
@app.route('/upload-slack-zip', methods= ['GET', 'POST'])
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

# ************************************************************** /store-slack-data

@app.route('/store-slack-data', methods= ['GET', 'POST'])
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
                mattermost.update_fetch_interval(fetch_interval_db[SHELVE_FIELD])
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
                chroma_n_results_db[SHELVE_FIELD] = int( body['chroma_n_results'] )
                return dict(chroma_n_results_db)
        else:
            return 'Please provide the number of messages / results to be used as context!'


port_no = os.environ.get('PORT', 5555)

print(f"Server running on port {port_no}...")
app.run(port=int(port_no), debug=True)
