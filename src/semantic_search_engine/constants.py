import os
from dotenv import load_dotenv
import shelve

load_dotenv()

# Chroma
DIR =  os.getcwd() #os.path.dirname(os.path.abspath(__file__))
CHROMA_PATH = os.environ.get("SS_CHROMA_DB_PATH") or os.path.join(DIR, 'chroma_db')
CHROMA_HOST = os.environ.get("SS_CHROMA_DB_HOST") or "127.0.0.1"
CHROMA_PORT = os.environ.get("SS_CHROMA_DB_PORT") or 5555
CHROMA_COLLECTION = os.environ.get("SS_CHROMA_COLLECTION_NAME") or "messages"

# Shelve
FETCH_TIME_SHELVE_NAME= os.environ.get("FETCH_TIME_SHELVE_NAME") or "last_fetch_time"
SETTINGS_SHELVE_NAME= os.environ.get("SETTINGS_SHELVE_NAME") or "settings"

# LLM
TOGETHER_API_KEY= os.environ.get("TOGETHER_API_KEY")
TOGETHER_MODEL_NAME= os.environ.get("TOGETHER_MODEL_NAME") or "togethercomputer/llama-2-70b-chat"

# Mattermost
MM_USER_NAME= os.environ.get("MM_USER_NAME") or "Admin"
MM_PASSWORD= os.environ.get("MM_PASSWORD") or "password"

# Sqlite
SQLITE_PATH = os.environ.get("SQLITE_PATH") or os.path.join(DIR, 'sqlite')
TEMP_SLACK_DATA_PATH = os.path.join(SQLITE_PATH, 'temp/')

# Constants from shelve
with shelve.open(SETTINGS_SHELVE_NAME) as settings:
    if 'mattermost_api_url' in settings:
        MM_API_URL= (settings['mattermost_api_url']) or "http://localhost:8065/api/v4"
    else:
        MM_API_URL= os.environ.get("MM_API_URL") or "http://localhost:8065/api/v4"

    if 'mattermost_url' in settings:
        MM_URL= (settings['mattermost_url']) or "http://localhost:8065/"
    else:
        MM_URL= os.environ.get("MM_URL") or "http://localhost:8065/"

    # TODO: This should be removed
    if 'personal_access_token' in settings:
        MM_PERSONAL_ACCESS_TOKEN= settings['personal_access_token']
    else:
        MM_PERSONAL_ACCESS_TOKEN= os.environ.get("MM_PERSONAL_ACCESS_TOKEN") or ''

