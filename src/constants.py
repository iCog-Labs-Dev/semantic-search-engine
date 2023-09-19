import os
from dotenv import load_dotenv

load_dotenv()

# Chroma
DIR = os.path.dirname(os.path.abspath(__file__))
CHROMA_PATH = os.environ.get("SS_CHROMA_DB_PATH") or os.path.join(DIR, 'chroma_db')
CHROMA_HOST = os.environ.get("SS_CHROMA_DB_HOST") or "127.0.0.1"
CHROMA_PORT = os.environ.get("SS_CHROMA_DB_PORT") or 5555
CHROMA_COLLECTION = os.environ.get("SS_CHROMA_COLLECTION_NAME") or "messages"

# LLM
TOGETHER_API_KEY= os.environ.get("TOGETHER_API_KEY") or "ac17a88fb15afc19f632fc58d39d177814f3ead1d013f7adc9bce9f3ccf33580"

# Mattermost
MATTERMOST_SERVER_URL= os.environ.get("MATTERMOST_SERVER_URL") or "http://localhost:8065/api/v4"
MM_USER_NAME= os.environ.get("MM_USER_NAME") or "Admin"
MM_PASSWORD= os.environ.get("MM_PASSWORD") or "password"
MM_PERSONAL_ACCESS_TOKEN= os.environ.get("MM_PERSONAL_ACCESS_TOKEN") or None
