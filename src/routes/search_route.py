from flask import request, Blueprint, Response
from routes.login_decorator import login_required
from json import dumps as to_json
from semantic_search_engine.semantic_search.search import SemanticSearch

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
