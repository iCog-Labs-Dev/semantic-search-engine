import os, datetime
from flask import session
from functools import wraps
from semantic_search_engine.constants import TEMP_SLACK_DATA_PATH, SQLITE_PATH
from dotenv import load_dotenv
from . import db, Auth

load_dotenv()

# App config
oauth_params = {'client_id': os.environ.get("OAUTH_CLIENT_ID"),
                'client_secret': os.environ.get("OAUTH_CLIENT_SECRET")}

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

def get_loggedin_user(client_token: str): # -> bool:
    try:
        return Auth.select().where( Auth.client_token==client_token ).dicts().get()
    except:
        return {}

def login_user(client_token: str, user_profile: dict) -> str:
    return Auth.insert(
        client_token=client_token,
        user_id=user_profile['user_id'],
        name=user_profile['name'],
        username=user_profile['username'],
        email=user_profile['email'],
        role=user_profile['role'],
        access_token=user_profile['access_token'],
        expires_at=datetime.datetime.utcfromtimestamp( float(user_profile['expires_at']) * 1000 )
    ).on_conflict_replace().execute()

def logout_user(client_token: str): # -> str:
    return Auth.delete().where(
        Auth.client_token == client_token
    ).execute()
