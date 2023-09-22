import os
from dotenv import load_dotenv

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

# LLM
TOGETHER_API_KEY= os.environ.get("TOGETHER_API_KEY")
TOGETHER_MODEL_NAME= os.environ.get("TOGETHER_MODEL_NAME") or "togethercomputer/llama-2-70b-chat"

# Mattermost
MM_SERVER_URL= os.environ.get("MM_SERVER_URL") or "http://localhost:8065/api/v4"
MM_USER_NAME= os.environ.get("MM_USER_NAME") or "Admin"
MM_PASSWORD= os.environ.get("MM_PASSWORD") or "password"
MM_PERSONAL_ACCESS_TOKEN= os.environ.get("MM_PERSONAL_ACCESS_TOKEN")
MM_FETCH_INTERVAL= os.environ.get("MM_FETCH_INTERVAL") or 5
