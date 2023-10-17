import sys
sys.path.append('./src')
import os, requests, threading, shelve

from time import sleep
from flask import Flask, jsonify, request, Response
from flask_cors import CORS
from functools import wraps
# from flask_sse import sse

from semantic_search_engine.semantic_search import SemanticSearch
from semantic_search_engine.mattermost.mattermost import Mattermost
from semantic_search_engine.mattermost.mm_api import MattermostAPI as MM_Api
from semantic_search_engine.slack.slack import Slack
from semantic_search_engine.slack.models import User, Channel, ChannelMember, Message
from semantic_search_engine.constants import FETCH_INTERVAL_SHELVE, LAST_FETCH_TIME_SHELVE, MM_PAT_ID_SHELVE, CHROMA_N_RESULTS_SHELVE, TEMP_SLACK_DATA_PATH

from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__)
# CORS(app)
# CORS(app, resources={r"/*": {"origins": "http://localhost:8065"}}, supports_credentials=True)
CORS(app=app,
     origins=['http://localhost:8065', 'http://127.0.0.1:8065'],
     supports_credentials=True)   # , resources={r"/*": {"origins": "http://localhost:3000"}})

mm_api_url = os.getenv("MM_API_URL")

# Session config
app.secret_key = os.getenv("APP_SECRET_KEY")  # Set the secret key for session management
app.config['SESSION_COOKIE_SAMESITE'] = 'None'
app.config['SESSION_COOKIE_SECURE'] = True

# semantic_search_engine initializations
semantic_client = SemanticSearch()
collection = semantic_client.collection
mattermost = Mattermost(collection)
slack = Slack(collection)
# ************************************************************** /
def admin_required(admin_only: bool):
    def login_required(func):
        @wraps(func)
        def decorated_function(*args, **kwargs):
            cookies = dict(request.cookies)
            auth_token = cookies.get('MMAUTHTOKEN')
            user_id = cookies.get('MMUSERID')
            if not (auth_token and user_id):
                return 'You must login and send requests with credentials enabled!', 500
            
            user_details = requests.get(
                f'{mm_api_url}/users/me',
                headers={ "Authorization": f"Bearer {cookies.get('MMAUTHTOKEN')}" },
            )
            if user_details.status_code != requests.codes.ok:
                return 'Unauthorized! Your session might have expired.', 401
            
            user_email = user_details.json().get('email', '')
            user_roles = user_details.json().get('roles', '').split(' ')

            #Check if an invalid response is returned from the API
            if not (user_email and user_roles):
                return 'Invalid user data!', 401

            #Check if the user has system_user role
            if not admin_only and 'system_user' not in user_roles:
                return 'Unauthorized! You should be a Mattermost user', 401
            
            # Check if the route requires admin privileges or not
            if admin_only and 'system_admin' not in user_roles:     
                return 'Unauthorized! You don\'t have Admin privileges!', 401
            loggedin_user = {
                'auth_token': auth_token,
                'user_id': user_id,
                'email': user_email
            }
            return func(loggedin_user, *args, **kwargs)
        return decorated_function
    return login_required

@app.route('/', methods=['GET'])
@admin_required(admin_only=True)
def root_route():
    # return '''<h1>Hi ✋</h1>'''
    res = {}
    with shelve.open(FETCH_INTERVAL_SHELVE) as fetch_interval_db:
        res['fetch_interval'] = fetch_interval_db[FETCH_INTERVAL_SHELVE]

    with shelve.open(LAST_FETCH_TIME_SHELVE) as last_fetch_time_db:
        res['last_fetch_time'] = last_fetch_time_db[LAST_FETCH_TIME_SHELVE] * 1000
    
    with shelve.open( CHROMA_N_RESULTS_SHELVE ) as chroma_n_results_db:
        res['chroma_n_results'] =  chroma_n_results_db[CHROMA_N_RESULTS_SHELVE]
        
    res['is_syncing'] = mattermost.is_syncing()

    return res


# ******************************************************** Get Current User ***************************************************

@app.route('/current_user', methods=['GET'])
@admin_required(admin_only=False)
def current_user(loggedin_user):
    print(loggedin_user)
    return loggedin_user

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
@admin_required(admin_only=False)
def semantic_search(loggedin_user):
    if request.method == 'GET':
        return '''<pre><h4> Send a POST request: <br>
    {
        "query" : "What did someone say about something?"
    } </h4>
    </pre>'''

    elif request.method == 'POST':
        query = request.json['query']
        user_id = loggedin_user['user_id']
        access_token = loggedin_user['auth_token']

        return semantic_client.semantic_search(
                    query=query,
                    user_id=user_id,
                    access_token=access_token
            ) 

    
# ************************************************************** /start_sync
    
@app.route('/start_sync', methods=['GET'])
@admin_required(admin_only=True)
def start_sync(loggedin_user):
    access_token = loggedin_user['auth_token']
    try:
        sync_thread = threading.Thread(target=mattermost.start_sync)
        sync_thread.start(access_token=access_token)
    except: return 'Something went wrong while attempting to sync!'

    sleep(2)
    return {
        "is_syncing": mattermost.is_syncing()
    }

# ************************************************************** /stop_sync
 
@app.route('/stop_sync', methods=['GET'])
@admin_required(admin_only=True)
def stop_sync():
    mattermost.stop_sync()
    sleep(1)
    return {
        "is_syncing": mattermost.is_syncing()
    }

# ************************************************************** /upload_slack_zip
@app.route('/upload_slack_zip', methods= ['GET', 'POST'])
@admin_required(admin_only=True)
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
@admin_required(admin_only=True)
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
@admin_required(admin_only=True)
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

# @app.route('/set_personal_access_token', methods=['GET', 'POST'])
# @admin_required(admin_only=True)
# def set_personal_access_token():
#     if request.method == 'GET':
#         return '''<pre><h4> Send a POST request: <br>
#     {
#         "personal_access_token": "the pesonal access token of an admin user"
#     } </h4></pre>'''

#     elif request.method == 'POST':
#         body = request.get_json()

#         if body.get("personal_access_token", False): 
#             with shelve.open( MM_PAT_ID_SHELVE ) as mm_pat_db:
#                 mm_pat_db[MM_PAT_ID_SHELVE] = body['personal_access_token']
#                 return dict(mm_pat_db)
#         else:
#             return 'Please provide a personal access token!'


# ************************************************************** /set_fetch_interval

@app.route('/set_fetch_interval', methods=['GET', 'POST'])
@admin_required(admin_only=True)
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
@admin_required(admin_only=True)
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
if __name__ == '__main__':
    app.run(port=int(port_no), debug=True)
