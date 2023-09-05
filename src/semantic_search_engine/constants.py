import os

DIR = os.path.dirname(os.path.abspath(__file__))

DB_PATH = os.environ.get("SS_CHROMA_DB_PATH") or os.path.join(DIR, 'chroma_db')
DB_HOST = os.environ.get("SS_CHROMA_DB_HOST") or "127.0.0.1"
DB_PORT = os.environ.get("SS_CHROMA_DB_PORT") or 5555

# required environment variables
#  TOGETHER_API_KEY=xxxxx
