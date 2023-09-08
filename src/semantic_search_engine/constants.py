import os

DIR = os.path.dirname(os.path.abspath(__file__))

CHROMA_PATH = os.environ.get("SS_CHROMA_DB_PATH") or os.path.join(DIR, 'chroma_db')
CHROMA_HOST = os.environ.get("SS_CHROMA_DB_HOST") or "127.0.0.1"
CHROMA_PORT = os.environ.get("SS_CHROMA_DB_PORT") or 5555
CHROMA_COLLECTION = os.environ.get("SS_CHROMA_COLLECTION_NAME") or "messages"

# choose sql database to use. accepts "sqlite", "postgres" or "mysql"
# "sqlite" by default
SQL_DB_TYPE = os.environ.get("SS_SQL_DB_TYPE") or "sqlite"

# sqlite related data
SQLITE_DB_PATH = os.environ.get("SS_SQLITE_DB_PATH") or os.path.join(DIR, 'sqlite.db')

# load postgres related data
POSTGRESQL_DB_HOST = os.environ.get("SS_POSTGRESQL_DB_HOST") or "127.0.0.1"
POSTGRESQL_DB_PORT = os.environ.get("SS_POSTGRESQL_DB_PORT") or 5432
POSTGRESQL_DB_USER = os.environ.get("SS_POSTGRESQL_DB_USER") or "postgres"
POSTGRESQL_DB_PASSWORD = os.environ.get("SS_POSTGRESQL_DB_PASSWORD")
POSTGRESQL_DB_NAME = os.environ.get("SS_POSTGRESQL_DB_NAME") or "semantic_search_engine"

# load mysql related data
MYSQL_DB_HOST = os.environ.get("SS_MYSQL_DB_HOST") or "127.0.0.1"
MYSQL_DB_PORT = os.environ.get("SS_MYSQL_DB_PORT") or 3306
MYSQL_DB_USER = os.environ.get("SS_MYSQL_DB_USER") or "app"
MYSQL_DB__PASSWORD = os.environ.get("SS_MYSQL_DB_PASSWORD")
MYSQL_DB_NAME = os.environ.get("MYSQL_DB_NAME") or "semantic_search_engine"

# required environment variables
#  TOGETHER_API_KEY=xxxxx
