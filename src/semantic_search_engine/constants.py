import os
from dotenv import load_dotenv
import shelve

load_dotenv()

# Chroma
DIR =  os.getcwd() #os.path.dirname(os.path.abspath(__file__))
CHROMA_PATH = os.path.join(DIR, 'chroma_db')
CHROMA_COLLECTION = "messages"
    # The following are only required if chroma is running as a hosted instance
CHROMA_HOST = os.environ.get("SS_CHROMA_DB_HOST") or "127.0.0.1"
CHROMA_PORT = os.environ.get("SS_CHROMA_DB_PORT") or 5555

# Slack Sqlite
SQLITE_PATH = os.path.join(DIR, 'db')
TEMP_SLACK_DATA_PATH = os.path.join(SQLITE_PATH, 'temp/')

# LLM       # TODO: We should use our own instance of a hosted LLM
TOGETHER_API_KEY = os.environ.get("TOGETHER_API_KEY")
TOGETHER_MODEL_NAME = os.environ.get("TOGETHER_MODEL_NAME") or "togethercomputer/llama-2-70b-chat"

# Mattermost    # TODO: Replace these with the client_id and client_secret required for oauth
MM_USER_NAME = "Admin"
MM_PASSWORD = "password"

# Defaults
DEFAULT_FETCH_INTERVAL = 15 * 60    # Default fetch interval in minutes
DEFAULT_LAST_FETCH_TIME = 0
DEFAULT_CHROMA_N_RESULTS = 25

# Shelve
SHELVE_PATH = os.path.join(DIR, 'shelve')
SHELVE_FIELD = 'value'

LAST_FETCH_TIME_SHELVE = os.path.join(SHELVE_PATH, "last_fetch_time")
FETCH_INTERVAL_SHELVE = os.path.join(SHELVE_PATH, "fetch_interval")
MM_PAT_SHELVE = os.path.join(SHELVE_PATH, "personal_access_token")
MM_API_URL_SHELVE = os.path.join(SHELVE_PATH, "mattermost_api_url")
CHROMA_N_RESULTS_SHELVE = os.path.join(SHELVE_PATH, "chroma_n_results")
# SETTINGS_SHELVE = os.path.join(SHELVE_PATH, "settings")

# # Constants from shelve
# with shelve.open(SETTINGS_SHELVE_NAME) as settings:
#     MM_API_URL = settings['mattermost_api_url']

#     CHROMA_N_RESULTS = settings['chroma_n_results']

#     # TODO: This should be kept more securely
#     MM_PERSONAL_ACCESS_TOKEN = settings['personal_access_token']

