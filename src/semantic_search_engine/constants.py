import os
from dotenv import load_dotenv
import shelve

load_dotenv()

# Chroma
DIR = os.path.dirname(os.path.abspath(__file__))
CHROMA_PATH = os.environ.get("SS_CHROMA_DB_PATH") or os.path.join(DIR, 'chroma_db')
CHROMA_HOST = os.environ.get("SS_CHROMA_DB_HOST") or "127.0.0.1"
CHROMA_PORT = os.environ.get("SS_CHROMA_DB_PORT") or 5555
CHROMA_COLLECTION = os.environ.get("SS_CHROMA_COLLECTION_NAME") or "messages"

# Shelve
MM_SHELVE_NAME= os.environ.get("MM_SHELVE_NAME") or "last_fetch_time"
SLACK_SHELVE_NAME= os.environ.get("SLACK_SHELVE_NAME") or "slack_store"
SETTINGS_SHELVE_NAME= os.environ.get("SETTINGS_SHELVE_NAME") or "settings"

# LLM
TOGETHER_API_KEY= os.environ.get("TOGETHER_API_KEY")
TOGETHER_MODEL_NAME= os.environ.get("TOGETHER_MODEL_NAME") or "togethercomputer/llama-2-70b-chat"

# Mattermost
MM_USER_NAME= os.environ.get("MM_USER_NAME") or "Admin"
MM_PASSWORD= os.environ.get("MM_PASSWORD") or "password"


# Constants from shelve
try:
    with shelve.open(SETTINGS_SHELVE_NAME) as settings:
        MM_SERVER_URL= (settings['mattermost-url'] + '/api/v4') or 'http://localhost:8065/api/v4'
        MM_FETCH_INTERVAL= (settings['fetch-interval'] * 60) or 5       # fetch interval in seconds 
        MM_PERSONAL_ACCESS_TOKEN= settings['personal-access-token'] or ''
except:
    print(f'The shelve "{SETTINGS_SHELVE_NAME}" doesn\'t exist and will be created!')
    MM_SERVER_URL= os.environ.get("MM_SERVER_URL") or "http://localhost:8065/api/v4"
    MM_FETCH_INTERVAL= os.environ.get("MM_FETCH_INTERVAL") or 5
    MM_PERSONAL_ACCESS_TOKEN= os.environ.get("MM_PERSONAL_ACCESS_TOKEN")

