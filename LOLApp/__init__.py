from flask import Flask
from flask_cache import Cache
from .apiCalls import APICalls

app = Flask(__name__)

app.config.update(
	DEBUG = True,
	SECRET_KEY = "Secret",
	TEMPLATES_AUTO_RELOAD = True
)
#create instance of apicalls class at startup to quickly be able to access riot api
cache = Cache(app,config={'CACHE_TYPE': 'simple'})

import LOLApp.views