import sys
sys.path.append('./src')
from flask import Flask, jsonify, make_response, request, Response, url_for, session
from flask_cors import CORS
from flask_sse import sse
from datetime import timedelta, datetime
import threading
import os
import shelve

from authlib.integrations.flask_client import OAuth
from semantic_search_engine.oauth.mm_oauth import register_oauth_client, login_required, get_loggedin_user, login_user, logout_user

from semantic_search_engine.semantic_search import SemanticSearch
from semantic_search_engine.mattermost.mattermost import Mattermost
from semantic_search_engine.mattermost.mm_api import MattermostAPI as MM_Api
from semantic_search_engine.slack.slack import Slack
from semantic_search_engine.slack.models import User, Channel, ChannelMember, Message
from semantic_search_engine.constants import FETCH_INTERVAL_SHELVE, LAST_FETCH_TIME_SHELVE, MM_PAT_SHELVE, MM_API_URL_SHELVE, CHROMA_N_RESULTS_SHELVE, TEMP_SLACK_DATA_PATH

from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__)
# CORS(app)
# CORS(app, resources={r"/*": {"origins": "http://localhost:8065"}}, supports_credentials=True)
CORS(app=app,
     origins=['http://localhost:8065', 'http://127.0.0.1:8065', 'http://localhost:8065/oauth/authorize'],
     supports_credentials=True)   # , resources={r"/*": {"origins": "http://localhost:3000"}})
oauth = OAuth(app)
mm_client = register_oauth_client(oauth=oauth)

# Session config
# Set the secret key for session management
app.secret_key = "sessionss"

# Configure the session to match your Express session settings
app.config['SESSION_COOKIE_SAMESITE'] = 'None'
app.config['SESSION_COOKIE_SECURE'] = True

# The /new route
@app.route('/new', methods=['POST'])
def new():
    try:
        token = request.json.get('token')
        print(token)
        session['ss_engine'] = token
        return jsonify({"message": "saved"}), 201
    except Exception as error:
        print(error)
        return str(error), 500

# The /token route
@app.route('/token', methods=['GET'])
def get_token():
    try:
        print(dict(session))
        token = session.get('ss_engine')
        print(token)
        return jsonify({"message": f'sse_{token}' })
    except Exception as error:
        print(error)
        return str(error), 500

# if __name__ == '__main__':
#     app.run(port=3002)
    

    

# app.secret_key = os.getenv("APP_SECRET_KEY") or 'some_key_for_session_encryption'
# app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=720)   # 720 - The session lasts for 12 Hours
# # app.config['SESSION_COOKIE_HTTPONLY'] = False
# app.config['SESSION_COOKIE_NAME'] = 'MM_SS_AUTH'
# app.config['SESSION_COOKIE_SAMESITE'] = 'None'
# app.config['SESSION_COOKIE_SECURE'] = True

# semantic_search_engine initializations
semantic_client = SemanticSearch()
collection = semantic_client.collection
mattermost = Mattermost(collection)
slack = Slack(collection)
# ************************************************************** /

@app.route('/root', methods=['GET'])
def root_route():
    # return '''<h1>Hi ✋</h1>'''
    res = {}
    with shelve.open(FETCH_INTERVAL_SHELVE) as fetch_interval_db:
        res['fetch_interval'] = fetch_interval_db[FETCH_INTERVAL_SHELVE]

    with shelve.open(LAST_FETCH_TIME_SHELVE) as last_fetch_time_db:
        res['last_fetch_time'] = last_fetch_time_db[LAST_FETCH_TIME_SHELVE] * 1000
        
    res['is_syncing'] = mattermost.is_syncing()
    
    print(request.cookies)
    cookies = dict(request.cookies)
    print(cookies.get('MMAUTHTOKEN'))
    print(cookies.get('MMUSERID'))

    return res


# ******************************************************** OAUTH *************************************************************
# **************************************************************************************************************************** /

@app.route('/login', methods=['GET'])
def login():
    mm_client = oauth.create_client('mattermost')  # create the mm_client oauth client
    redirect_uri = url_for('authorize', _external=True)

    return mm_client.authorize_redirect(redirect_uri)

@app.route('/oauth/callback')
def authorize():
    print('Authorized')
    # client_token = session.get('client_token')  # Get the client_token from session
    # if client_token is None:
    #     return 'Authentication failed!'
    try:
        session['ss_engine'] = 'token from auth after login number 5'
    except Exception as error:
        print(error)

    token = mm_client.authorize_access_token()   # Get access token from Mattermost oauth
    user_info = mm_client.userinfo()  # uses openId endpoint to fetch user info
    print('TOKEN: ', token)
    # print('USER_INFO', user_info)

    user_profile = {
        "user_id" : user_info['id'],
        "name" : f"{ user_info['first_name'] } { user_info['last_name'] }".strip(),
        "username" : user_info['username'],
        "email" : user_info['email'],
        "role" : user_info['roles'],
        "access_token": token['access_token'],
        "expires_at": token['expires_in']
    }

    # Save logged in users data in sqlite
    # login_user(client_token=client_token, user_profile=user_profile)
    session['user_profile'] = user_profile 

    # resp = make_response('Setting the cookie')  
    # resp.set_cookie('GFG','ComputerScience Portal') 
    return 'Authenticated!'

@app.route('/logout', methods=['GET'])
def logout():
    client_token = request.headers.get('client_token')
    logout_user(client_token=client_token)
    
    return 'logged out!'

@app.route('/current_user', methods=['GET'])
def current_user():
    user_profile = session.get('user_profile')
    print(user_profile)
    
    return user_profile

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
def semantic_search():
    if request.method == 'GET':
        # query = request.args.get('query')
        return '''<pre><h4> Send a POST request: <br>
    {
        "query" : "What did someone say about something?"
    } </h4>

    Headers: client_token = "The client token of the User"
    </pre>'''

    elif request.method == 'POST':
        query = request.json['query']
        print(request.headers)
        client_token = request.headers.get('client_token')
        loggedin_user = get_loggedin_user(client_token=client_token)

        print(loggedin_user)
 
        if loggedin_user:
            user_id = loggedin_user.get('user_id', False)
            access_token = loggedin_user.get('access_token', False)

            return semantic_client.semantic_search(query=query, user_id=user_id)
        else:
            return 'Unauthorized!'   

    
# ************************************************************** /start_sync
    
@app.route('/start_sync', methods=['GET', 'POST'])
def start_sync():
    if request.method == 'GET':
        return '''<pre><h4> Send a POST request: <br>
    {
        "mm_api_url" : "the URL of the mattermost API",
        "client_token" : "The client token of the Admin"
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
if __name__ == '__main__':
    app.run(port=int(port_no), debug=True)
