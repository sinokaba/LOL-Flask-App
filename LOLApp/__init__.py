from flask import Flask
from .api_calls import APICalls
from flask_cache import Cache

app = Flask(__name__)
api = APICalls()
cache = Cache(app,config={'CACHE_TYPE': 'simple'})

import LOLApp.views