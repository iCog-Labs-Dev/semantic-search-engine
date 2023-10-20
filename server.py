import sys
import time
sys.path.append('./src')
import os, requests, threading, shelve

from json import dumps as to_json
from time import sleep
from flask import Flask, request, Response, send_file
from flask_cors import CORS
from functools import wraps
# from flask_sse import sse

from semantic_search_engine.semantic_search import SemanticSearch
from semantic_search_engine.mattermost.mattermost import Mattermost
from semantic_search_engine.mattermost.mm_api import MattermostAPI as MM_Api
from semantic_search_engine.slack.slack import Slack
from semantic_search_engine.slack.models import User, Channel, ChannelMember, Message
from semantic_search_engine.constants import FETCH_INTERVAL_SHELVE, LAST_FETCH_TIME_SHELVE, CHROMA_N_RESULTS_SHELVE, TEMP_SLACK_DATA_PATH

from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__)
# CORS(app)
# CORS(app, resources={r"/*": {"origins": "http://localhost:8065"}}, supports_credentials=True)
CORS(app=app,
     origins=os.getenv("MM_URL"),
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
def login_required(admin_only: bool):
    def inner_decorator(func):
        @wraps(func)
        def decorated_function(*args, **kwargs):
            cookies = dict(request.cookies)
            auth_token = cookies.get('MMAUTHTOKEN')
            user_id = cookies.get('MMUSERID')
            if not (auth_token and user_id):
                return Response(to_json({ 'message' : 'You must send requests with credentials enabled and be logged in!' }), status=400, mimetype='application/json')
            
            res = requests.get(
                f'{mm_api_url}/users/me',
                headers={ "Authorization": f"Bearer {cookies.get('MMAUTHTOKEN')}" },
            )
            if res.status_code != requests.codes.ok:
                return Response(to_json({ 'message' : 'Unauthorized! Your session might have expired.' }), status=401, mimetype='application/json')
            
            user_details = res.json()
            user_email = user_details.get('email', '')
            user_roles = user_details.get('roles', '').split(' ')

            #Check if an invalid response is returned from the API
            if not (user_email and user_roles):
                return Response(to_json({ 'message' : 'Invalid user data!' }), status=401, mimetype='application/json')

            #Check if the user has system_user role
            if not admin_only and 'system_user' not in user_roles:
                return Response(to_json({ 'message' : 'Unauthorized! You should be a Mattermost user' }), status=401, mimetype='application/json')
            
            # Check if the route requires admin privileges or not
            if admin_only and 'system_admin' not in user_roles:     
                return Response(to_json({ 'message' : 'Unauthorized! You don\'t have Admin privileges!' }), status=401, mimetype='application/json')
            loggedin_user = {
                'auth_token': auth_token,
                'user_info': {
                    'user_id': user_id,
                    'name': f"{user_details.get('first_name', '')} {user_details.get('last_name', '')}".strip() or  user_details.get('username', ''),
                    'email': user_email
                }
            }
            return func(loggedin_user, *args, **kwargs)
        return decorated_function
    return inner_decorator



# ************************************************************** /img

@app.route('/img', methods=['GET'])
def ping_img():
    return send_file('./src/img/user.webp', mimetype='image/webp')

# ************************************************************** /

@app.route('/', methods=['GET'])
@login_required(admin_only=True)
def root_route(loggedin_user):
    try:
        res = {}
        with shelve.open(FETCH_INTERVAL_SHELVE) as fetch_interval_db:
            res['fetch_interval'] = fetch_interval_db[FETCH_INTERVAL_SHELVE]

        with shelve.open(LAST_FETCH_TIME_SHELVE) as last_fetch_time_db:
            res['last_fetch_time'] = last_fetch_time_db[LAST_FETCH_TIME_SHELVE] * 1000
        
        with shelve.open( CHROMA_N_RESULTS_SHELVE ) as chroma_n_results_db:
            res['chroma_n_results'] =  chroma_n_results_db[CHROMA_N_RESULTS_SHELVE]
            
        res['is_syncing'] = mattermost.is_syncing()

        return Response(to_json(res), status=200, mimetype='application/json')
    
    except:
        return Response(to_json({
            'message': 'Something went wrong! Please restart the server.',
            'log': sys.exc_info()[0]
            }), status=500, mimetype='application/json')


# ************************************************************** /search

@app.route('/search', methods=['GET', 'POST'])
@login_required(admin_only=False)
def semantic_search(loggedin_user):
    if request.method == 'GET':
        return '''<pre><h4> Send a POST request: <br>
    {
        "query" : "What did someone say about something?"
    } </h4>
    </pre>'''

    elif request.method == 'POST':
        query = request.json.get('query', False)
        if not query:
            return Response(to_json({ 'message' : 'Please provide a query!' }), status=400, mimetype='application/json')
        if len(query) < 2 or len(query) > 500:
            return Response(to_json({ 'message' : 'The query must be between 2 - 500 characters long.' }), status=400, mimetype='application/json')
            
        try:
            return semantic_client.semantic_search(
                query=request.json.get('query'),
                user_info=loggedin_user['user_info'],
                access_token=loggedin_user['auth_token']
            )
        except:
            return Response(to_json({
                'message': 'Something went wrong, please try again!',
                'log': sys.exc_info()[0]
            }), status=500, mimetype='application/json')

    
# ************************************************************** /start_sync
    
@app.route('/start_sync', methods=['GET'])
@login_required(admin_only=True)
def start_sync(loggedin_user):
    access_token = loggedin_user['auth_token']
    try:
        sync_thread = threading.Thread(target=mattermost.start_sync, args=(access_token,))
        sync_thread.start()

        sleep(1)    # Wait for the first sync to be scheduled
        return Response(to_json({
            'is_syncing': mattermost.is_syncing()
        }), status=200, mimetype='application/json')
    
    except: 
        return Response(to_json({
            'message': 'Something went wrong while attempting to sync!',
            'log': sys.exc_info()[0]
        }), status=500, mimetype='application/json')


# ************************************************************** /stop_sync
 
@app.route('/stop_sync', methods=['GET'])
@login_required(admin_only=True)
def stop_sync(loggedin_user):
    try:
        mattermost.stop_sync()

        return Response(to_json({
            'is_syncing': mattermost.is_syncing()
        }), status=200, mimetype='application/json')
    
    except:
        return Response(to_json({
            'message': 'Something went wrong while stopping the sync!',
            'log': sys.exc_info()[0]
        }), status=500, mimetype='application/json')

# ************************************************************** /upload_slack_zip
@app.route('/upload_slack_zip', methods= ['GET', 'POST'])
@login_required(admin_only=True)
def save_slack_zip(loggedin_user):
    if request.method == 'GET':
        return '''<pre><h4> Send a POST request: <br>
        MultipartFormData    
            file = (Zip file containing slack export data)
    </h4></pre>'''

    elif request.method == 'POST':
        if "file" not in request.files:
            return Response(to_json({
                'message' : 'File Not Sent!'
            }), status=400, mimetype='application/json')
        try:
            file = request.files["file"]
            file_path = os.path.join(TEMP_SLACK_DATA_PATH, 'slack-export-data.zip')

            file.save(file_path)                                        # Save the zip file
            channel_details = slack.upload_slack_data_zip(file_path)    # Extract it and read the channel details
            os.remove(file_path)                                        # Delete the zip file

            return Response(to_json(channel_details), status=201, mimetype='application/json')
        
        except:
            return Response(to_json({
                'message': 'Something went wrong while uploading the file!',
                'log': sys.exc_info()[0]
            }), status=500, mimetype='application/json')

# ************************************************************** /store_slack_data
# @app.route('/time')
# def time_stream():
#     def generate_time():
#         while True:
#             yield f"data: {time.strftime('%H:%M:%S')}\n\n"
#             time.sleep(1)
#     return Response(generate_time(), content_type='text/event-stream')

@app.route('/store_slack_data', methods= ['GET', 'POST'])
# @login_required(admin_only=True)
def store_data():
    # if request.method == 'GET':
    #     return '''<pre><h4> Send a POST request: <br>
    # {   
    #     "channel_id" : {
    #         "store_all" : true | false,
    #         "store_none" : true | false,
    #         "start_date" : (start date in POSIX time),
    #         "end_date" : (end date in POSIX time)
    #     },
    #     ...
    # } </h4></pre>'''

    # elif request.method == 'POST':
    if True:
        try:
            # channel_specs = request.get_json()
            channel_specs = {'C05D1SE01B7': {'store_all': True, 'store_none': False, 'start_date': 1687165577, 'end_date': 1697805748.681}, 'C05D77W3N76': {'store_all': True, 'store_none': False, 'start_date': 1687165577, 'end_date': 1697805748.681}, 'C05D7863DRA': {'store_all': True, 'store_none': False, 'start_date': 1687165686, 'end_date': 1697805748.681}, 'C05ABCDE01': {'store_all': True, 'store_none': False, 'start_date': 1687166738, 'end_date': 1697805748.681}}
            # slack.store_slack_data(channel_specs=channel_specs)
            #TODO: should return progress in real-time (channel by channel)

            # def generate_time():
            #     while True:
            #         yield f"data: {time.strftime('%H:%M:%S')}\n\n"
            #         time.sleep(1)
            # return Response(slack.test_yield(), content_type='text/event-stream')

            # return Response(to_json( 'Slack data stored!' ), status=201, mimetype='application/json')
            return Response(slack.store_slack_data(channel_specs=channel_specs), content_type='text/event-stream')
        
        except:
             return Response(to_json({
                'message': 'Something went wrong while saving the data!',
                'log': sys.exc_info()[0]
            }), status=500, mimetype='application/json')

# ************************************************************** /reset

@app.route('/reset', methods=['GET', 'POST'])
@login_required(admin_only=True)
def reset_all(loggedin_user):
    if request.method == 'GET':
        return '''<pre><h4> Send a POST request: <br>
    {
        "mattermost" : true | false,
        "slack" : true | false
    } </h4></pre>'''

    elif request.method == 'POST':
        try:
            body = request.get_json()

            if body.get("mattermost", False):
                mattermost.reset_mattermost()

            if body.get("slack", False):
                slack.reset_slack()
            
            return Response(to_json( 'Reset Successful!' ), status=200, mimetype='application/json')

        except:
            return Response(to_json({
                'message': 'Something went wrong while resetting!',
                'log': sys.exc_info()[0]
            }), status=500, mimetype='application/json')
    

# ************************************************************** /set_fetch_interval

@app.route('/set_fetch_interval', methods=['GET', 'POST'])
@login_required(admin_only=True)
def set_fetch_interval(loggedin_user):
    if request.method == 'GET':
        return '''<pre><h4> Send a POST request: <br>
    {
        "fetch_interval": "the time interval between fetches (in seconds)"
    } </h4></pre>'''

    elif request.method == 'POST':
        try:
            body = request.get_json()

            if body.get('fetch_interval', False): 
                fetch_interval = abs (float( body['fetch_interval'] ))
                if fetch_interval < (15 * 60) or fetch_interval > (24 * 60 * 60):
                    return Response(to_json({ 'message': 'Fetch interval must be between 15 minutes and 24 hours!' }), status=400, mimetype='application/json')
                
                with shelve.open( FETCH_INTERVAL_SHELVE ) as fetch_interval_db:
                    fetch_interval_db[FETCH_INTERVAL_SHELVE] = fetch_interval
                    mattermost.update_fetch_interval(fetch_interval_db[FETCH_INTERVAL_SHELVE])

                    return Response(to_json( dict(fetch_interval_db) ), status=200, mimetype='application/json')
            else:
                return Response(to_json({ 'message': 'Please provide a fetch interval!' }), status=400, mimetype='application/json')
            
        except ValueError:
            return Response(to_json({ 'message': 'Invalid interval! Interval must be a number.' }), status=400, mimetype='application/json')
        except:
            return Response(to_json({
                'message': 'Something went wrong while setting the fetch interval!',
                'log': sys.exc_info()[0]
            }), status=500, mimetype='application/json')

# ************************************************************** /set_chroma_n_results

@app.route('/set_chroma_n_results', methods=['GET', 'POST'])
@login_required(admin_only=True)
def set_chroma_n_results(loggedin_user):
    if request.method == 'GET':
        return '''<pre><h4> Send a POST request: <br>
    {
        "chroma_n_results": "the no. of messages given to the LLM as context"
    } </h4></pre>'''

    elif request.method == 'POST':
        try:
            body = request.get_json()

            if body.get("chroma_n_results", False): 
                chroma_n_results = abs (int( body['chroma_n_results'] ))
                if chroma_n_results < 25 and chroma_n_results > 100:
                    return Response(to_json({ 'message': 'Please provide a number between 25 - 100!' }), status=400, mimetype='application/json')
                
                with shelve.open( CHROMA_N_RESULTS_SHELVE ) as chroma_n_results_db:
                    chroma_n_results_db[CHROMA_N_RESULTS_SHELVE] = chroma_n_results
                    return Response(to_json( dict(chroma_n_results_db) ), status=200, mimetype='application/json')
            else:
                return Response(to_json({ 'message': 'Please provide the number of messages to be used as context!' }), status=400, mimetype='application/json')

        except:
            return Response(to_json({
                'message': 'Something went wrong while setting Chroma n_results!',
                'log': sys.exc_info()[0]
            }), status=500, mimetype='application/json')


# **************************************************************************************************************************** /
# ****************************************************************************************************************************

# =========== Test Auth ===========
@app.route('/current_user', methods=['GET'])
@login_required(admin_only=False)
def current_user(loggedin_user):
    print(loggedin_user)
    return Response(to_json(loggedin_user), status=200, mimetype='application/json')

# =========== Test Chroma ===========
# TODO: remove this endpoint
@app.route('/query_db/<db>', methods=['POST'])
def chroma_route(db):
    if db == 'chroma':
        query = request.json['query']
        n_results = request.json['n_results']
        source = request.json['source']
        user_id = request.json['user_id']
        channels_list = MM_Api(access_token='x1p9oaut17gsdxqurhp9po6hoe').get_user_channels(user_id=user_id) if source == 'mm' else ['']

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


# **************************************************************************************************************************** /
# ****************************************************************************************************************************



port_no = os.environ.get('PORT', 5555)

print(f"Server running on port {port_no}...")
if __name__ == '__main__':
    app.run(port=int(port_no), debug=True)
