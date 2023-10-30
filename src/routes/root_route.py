import shelve
from flask import Response, Blueprint
from json import dumps as to_json
from semantic_search_engine.constants import FETCH_INTERVAL_SHELVE, LAST_FETCH_TIME_SHELVE, CHROMA_SHELVE
from routes.login_decorator import login_required
from . import mattermost

root_bp = Blueprint("root", __name__)

# ************************************************************** /ping

@root_bp.route('/ping', methods=['HEAD'])
def ping():
    return ''

# ************************************************************** /

@root_bp.route('/get', methods=['GET'])
@login_required(admin_only=True)
def root_route(loggedin_user):
    try:
        res = {}
        with shelve.open(FETCH_INTERVAL_SHELVE) as fetch_interval_db:
            res['fetch_interval'] = fetch_interval_db[FETCH_INTERVAL_SHELVE]

        with shelve.open(LAST_FETCH_TIME_SHELVE) as last_fetch_time_db:
            res['last_fetch_time'] = last_fetch_time_db[LAST_FETCH_TIME_SHELVE] * 1000
        
        with shelve.open( CHROMA_SHELVE ) as chroma_n_results_db:
            res['chroma_n_results'] =  chroma_n_results_db['chroma_n_results']
            res['max_chroma_distance'] =  chroma_n_results_db['max_chroma_distance']
            
        res['is_syncing'] = mattermost.is_syncing()
        res['in_progress'] = mattermost.sync_in_progress

        return Response(to_json(res), status=200, mimetype='application/json')
    
    except Exception as err:
        return Response(to_json({
            'message': 'Something went wrong! Please restart the server.',
            'log': str( err )
            }), status=500, mimetype='application/json')
