from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import shelve
from semantic_search_engine.semantic_search import SemanticSearch
from semantic_search_engine.mattermost import Mattermost
# from semantic_search_engine.llm import TogetherLLM as together

#Test
from semantic_search_engine.chroma import get_chroma_collection
from semantic_search_engine import constants
from semantic_search_engine.slack import extract_zip, channels, users, all_channels
from io import BytesIO
from semantic_search_engine.chroma import ChromaSingleton

app = Flask(__name__)
CORS(app)

semantic_client = SemanticSearch()
# ************************************************************** /

@app.route('/', methods=['GET'])
def root_route():
    if request.method == 'GET':
        return '''<h1>Hi ✋</h1>'''



# =========== Test Chroma ===========
@app.route('/chroma/<action>', methods=['GET'])
def chroma_route(action): 
    if action == 'query':
        return semantic_client.collection.query(
            query_texts=['Hello'],
            n_results=100
            # Get all messages from slack or specific channels that the user's a member of in MM
            # where = {
            #     "$or" : [
            #         {
            #             "platform" : "sl"
            #         },
            #         # "$and" : [ { "access" : "private" } ]
            #         {
            #             "channel_id" : {
            #                             "$in" : channels_list
            #                             }
            #         }
            #     ]
            # }
        )


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
    # together().start()
    Mattermost().start_sync()
    return 'Started sync!'

# ************************************************************** /stop-sync
 
@app.route('/stop-sync', methods=['GET'])
def stop_sync():
    # together().stop()
    Mattermost().stop_sync()
    return 'Stopped sync!'

# ************************************************************** /slack
@app.route('/import-data', methods= ['POST'])
def import_data():
    
    if "zip_file" not in request.files:
        return jsonify({
            "error" : "File Not Sent"
        })
    
    file = request.files["zip_file"]

    extract_zip(BytesIO(file))

    channels()  # upload channels to shelve
 
    users()  # upload users to shelve

    for msg in all_channels():
        semantic_client.collection.upsert(
            id = msg["id"],
            documents= [msg["text"]],
            metadatas= [
                {
                    "platform" : "sl",
                    "access" : "pub",
                    "channel_id" : msg["channel"],
                    "user_id" : msg["user"]
                }
            ]
        )


# ************************************************************** /reset-all

@app.route('/reset/<action>', methods=['GET', 'POST'])
def reset_all(action):
    Mattermost().stop_sync()
    if action=='mattermost' or action=='all':
        # Delete the chroma collection
        try:
            # ChromaSingleton().get_connection().delete_collection(name=constants.CHROMA_COLLECTION)
            semantic_client.collection.delete()
            print(f'Chroma collection "{constants.CHROMA_COLLECTION}" deleted!')
            # Delete mattermost shelve store
            with shelve.open(constants.MM_SHELVE_NAME) as db:
                db[constants.MM_SHELVE_NAME] = 0
                # del db
                print('Mattermost shelve reset!')
        except:
            print(f'No collection named {constants.CHROMA_COLLECTION} detected or the shelve "{constants.MM_SHELVE_NAME}" doesn\'t exist')

    if action=='slack' or action=='all':
        pass
        # TODO: Delete slack shelve store
        '''with shelve.open(constants.SLACK_SHELVE_NAME) as db:
        del db'''
    
    return 'Reset Successful!'

port_no = os.environ.get('PORT', 5555)

print(f"Server running on port {port_no}....")
app.run(port=int(port_no))


# ************************************************************** /settings

@app.route('/settings', methods=['GET', 'POST'])
def settings():
    if request.method == 'GET':
        return '''<pre><h4> Send a POST request: <br>
    {
        "mattermost-url" : "the URL of the mattermost server",
        "fetch-interval" : "interval to sync messages (in minutes)",
        "personal-access-token": "the pesonal access token of an admin user"
    } </h4></pre>'''

    elif request.method == 'POST':
        mmURL = request.json['mattermost-url'] or ''
        interval = request.json['fetch-interval'] or ''
        pat = request.json['personal-access-token'] or ''

        with shelve.open(constants.SETTINGS_SHELVE_NAME) as settings:
            settings['mattermost-url'] = mmURL
            settings['fetch-interval'] = interval
            settings['personal-access-token'] = pat

        return 'Settings updated!'
