import os
# import sys
# sys.path.append('./src')
from flask import Flask, request
from flask_cors import CORS

from src.routes.root_route import root_bp
from src.routes.sync_route import sync_bp
from src.routes.search_route import search_bp
from src.routes.settings_route import settings_bp
from src.routes.slack_route import slack_bp
from src.semantic_search_engine.shelves import create_default_shelve

from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__)
# CORS(app, resources={r"/*": {"origins": "http://localhost:8065"}}, supports_credentials=True)
# TODO: Temp NO AUTH
# CORS(app)
CORS(app=app,
     origins=[os.getenv("MM_URL"), os.getenv("MM_API_URL") or ''],
     supports_credentials=True)

# Session config
# app.secret_key = os.getenv("APP_SECRET_KEY")  # Set the secret key for session management
# app.config['SESSION_COOKIE_SAMESITE'] = 'None'
# app.config['SESSION_COOKIE_SECURE'] = True

# TODO: Temp NO AUTH
from src.semantic_search_engine.constants import SHELVE_PATH, PAT_SHELVE
create_default_shelve(
    shelve_name=PAT_SHELVE,
    personal_access_token=''
)

app.register_blueprint(root_bp, url_prefix="/root")
app.register_blueprint(sync_bp, url_prefix="/sync")
app.register_blueprint(search_bp, url_prefix="/search")
app.register_blueprint(settings_bp, url_prefix="/settings")
app.register_blueprint(slack_bp, url_prefix="/slack")

@app.route('/', methods=['GET'])
def ping():
    cookies = dict(request.cookies)
    print('Cookies: ', cookies)
    return 'Hi ✋'

port_no = os.environ.get('PORT', 5555)

print(f"Server running on port {port_no}...")
if __name__ == '__main__':
    app.run(port=int(port_no), debug=True, host="0.0.0.0")
else:
    gunicorn_app = app
