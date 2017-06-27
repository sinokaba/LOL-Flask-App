from flask import Flask
from flask_cache import Cache
from flask_sqlalchemy import SQLAlchemy
from .api_calls import APICalls

app = Flask(__name__)

app.config.update(
	DEBUG = True,
	SECRET_KEY = "Secret",
	TEMPLATES_AUTO_RELOAD = True
)
#create instance of apicalls class at startup to quickly be able to access riot api
cache = Cache(app,config={'CACHE_TYPE': 'simple'})
api = APICalls()
#app.config["SQLALCHEMY_DATABSE_URI"] = "postgresql://postgres:1WILLchange!@localhost/mydatabase"

import LOLApp.views