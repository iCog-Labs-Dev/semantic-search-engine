import os

from dotenv import load_dotenv
load_dotenv()

wsgi_app = "server:app"
workers = 2
worker_class = "gevent"
timeout = 3600
graceful_timeout = 60
port_no = os.environ.get('PORT', 5555)
bind  = "0.0.0.0:"+str(port_no)
errorlog = "-"  # Print errors to stdout