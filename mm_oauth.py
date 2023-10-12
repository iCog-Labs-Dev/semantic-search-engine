import os
from flask import session
from functools import wraps
from peewee import SqliteDatabase
from semantic_search_engine.constants import TEMP_SLACK_DATA_PATH, SQLITE_PATH
from dotenv import load_dotenv

load_dotenv()

os.makedirs(SQLITE_PATH, exist_ok=True)

# get or create connection with SQLite database
db = SqliteDatabase(
   SQLITE_PATH + '/auth.db' #, pragmas={'journal_mode': 'wal', 'cache_size': 10000,'foreign_keys': 1}
)

# App config
oauth_params = {'client_id': '3pcn3aajptb3uganhkymhoxpio',
                'client_secret': 'hmo9noxwh3najnjpj9q77mro1a'}

def register_oauth_client(oauth):
    mm_client = oauth.register(
        name='mattermost',
        client_id=os.environ.get("OAUTH_CLIENT_ID"),
        client_secret=os.environ.get("OAUTH_CLIENT_SECRET"),
        access_token_url='http://localhost:8065/oauth/access_token',
        access_token_params=oauth_params,
        authorize_url='http://localhost:8065/oauth/authorize',
        authorize_params=None,
        api_base_url='http://localhost:8065',
        userinfo_endpoint='http://localhost:8065/api/v4/users/me',  # This is needed if using openId to fetch user info
        client_kwargs={'scope': 'user:email'},
    )

    return mm_client

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        loggedin_user = dict(session).get('profile', None)
        # Check the server session to see if the User has previouly logged in (before the session expires)
        if loggedin_user:
            return f(loggedin_user, *args, **kwargs)
        return 'You aint logged in, no page for u!'
    return decorated_function
