from flask import request, Blueprint, Response
from src.routes.login_decorator import login_required
from json import dumps as to_json
from src.semantic_search_engine.semantic_search.search import SemanticSearch

search_bp = Blueprint("search", __name__)

# ************************************************************** /search

@search_bp.route('/<option>', methods=['GET', 'POST'])
@login_required(admin_only=False)
def semantic_search(loggedin_user, option):
    if request.method == 'GET':
        return '''<pre><h4> Send a POST request: <br>
    {
        "query" : "What did someone say about something?"
    } </h4>
    </pre>'''

    elif request.method == 'POST':
        query = request.json.get('query', False)
        # TODO: Temp NO AUTH
        user_id = request.json.get('user_id', '')

        if not query:
            return Response(to_json({ 'message' : 'Please provide a query!' }), status=400, mimetype='application/json')
        if len(query) < 2 or len(query) > 500:
            return Response(to_json({ 'message' : 'The query must be between 2 - 500 characters long.' }), status=400, mimetype='application/json')
            
        try:
            # TODO: Temp NO AUTH
            # semantic_client = SemanticSearch(
            #     access_token=loggedin_user['auth_token'],
            #     user_info=loggedin_user['user_info']
            # )
            # TODO: Temp NO AUTH
            semantic_client = SemanticSearch(
                user_id=user_id
            )

            return semantic_client.semantic_search(
                query=request.json.get('query')
            )
        
        except Exception as err:
            return Response(to_json({
                'message': 'Something went wrong, please try again!',
                'log': str( err )
            }), status=500, mimetype='application/json')


# **************************************************************************************************************************** /
# ****************************************************************************************************************************
from src.semantic_search_engine.chroma import ChromaSingleton
from src.semantic_search_engine.mattermost.mm_details import MMDetails as MM_Api
from src.semantic_search_engine.shelves import retrieve_one
from src.semantic_search_engine.slack.models import User,Message, ChannelMember, Channel
# =========== Test Auth ===========
# @search_bp.route('/current_user', methods=['GET'])
# @login_required(admin_only=False)
# def current_user(loggedin_user):
#     print(loggedin_user)
#     return Response(to_json(loggedin_user), status=200, mimetype='application/json')

# =========== Test Chroma ===========
# TODO: remove this endpoint
from src.semantic_search_engine.constants import PAT_SHELVE
@search_bp.route('/db/<db>', methods=['GET', 'POST'])
@login_required(admin_only=False)
def chroma_route(db):
    if db == 'chroma':
        query = request.json['query'] or 'Hello'
        n_results = request.json['n_results'] or 40
        source = request.json['source'] or 'sl'
        user_id = request.json['user_id']
        pat = retrieve_one(
            shelve_name=PAT_SHELVE,
            key='personal_access_token'
        )
        channels_list = MM_Api(access_token=pat).get_user_channels(user_id=user_id) or [''] if source == 'mm' else ['']

        # query_result = collection.query(
        #         query_texts=[query],
        #         n_results=self.chroma_n_results,
        #         where = { "channel_id": { "$in": channels_list } } # Fiter chroma reslults by channel_id
        #     )
        res = ChromaSingleton().get_chroma_collection().query(
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

