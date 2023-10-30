import sys
sys.path.append('./src')
import os
from flask import Flask, request
from flask_cors import CORS

from routes.root_route import root_bp
from routes.sync_route import sync_bp
from routes.search_route import search_bp
from routes.settings_route import settings_bp
from routes.slack_route import slack_bp

from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__)
# CORS(app)
# CORS(app, resources={r"/*": {"origins": "http://localhost:8065"}}, supports_credentials=True)
CORS(app=app,
     origins=os.getenv("MM_URL"),
     supports_credentials=True)   # , resources={r"/*": {"origins": "http://localhost:3000"}})

# Session config
# app.secret_key = os.getenv("APP_SECRET_KEY")  # Set the secret key for session management
# app.config['SESSION_COOKIE_SAMESITE'] = 'None'
# app.config['SESSION_COOKIE_SECURE'] = True

app.register_blueprint(root_bp, url_prefix="/root")
app.register_blueprint(sync_bp, url_prefix="/sync")
app.register_blueprint(search_bp, url_prefix="/search")
app.register_blueprint(settings_bp, url_prefix="/settings")
app.register_blueprint(slack_bp, url_prefix="/slack")

@app.route('/', methods=['GET'])
def ping():
    cookies = dict(request.cookies)
    print('hi', cookies)
    return 'Hi'

port_no = os.environ.get('PORT', 5555)

print(f"Server running on port {port_no}...")
if __name__ == '__main__':
    app.run(port=int(port_no), debug=True, host="0.0.0.0")


# **************************************************************************************************************************** /
# ****************************************************************************************************************************

# =========== Test Chroma ===========
# TODO: remove this endpoint
# @app.route('/query_db/<db>', methods=['POST'])
# def chroma_route(db):
#     if db == 'chroma':
#         query = request.json['query']
#         n_results = request.json['n_results']
#         source = request.json['source']
#         user_id = request.json['user_id']
#         channels_list = MM_Api(access_token='x1p9oaut17gsdxqurhp9po6hoe').get_user_channels(user_id=user_id) if source == 'mm' else ['']

#         res = collection.query(
#                 query_texts=[query],
#                 n_results=n_results,
#                 where = {
#                     "$and": [
#                         {   "$or": [
#                                 {
#                                     "access": {
#                                         "$eq": "pub"
#                                     }
#                                 },
#                                 {
#                                     "channel_id": {
#                                         "$in": channels_list
#                                     }
#                                 }
#                             ]
#                         },
#                         {
#                             "source" : { "$eq" : source }
#                         }
#                     ]
#                 }
#             )
        
#         res['channel_list'] = channels_list
#         return res
    
#     elif db == 'sqlite':
#         table = request.json['table']
#         if table == 'User': rows = User.select().dicts()
#         elif table == 'Message': rows = Message.select().dicts()
#         elif table == 'Channel': rows = Channel.select().dicts()
#         elif table == 'ChannelMember': rows = ChannelMember.select().dicts()
#         else: return 'Enter a valid table name'
#         res = [row for row in rows]
#         return res


# **************************************************************************************************************************** /
# ****************************************************************************************************************************

