from flask import Flask
from flask_cache import Cache
from flask_sqlalchemy import SQLAlchemy
from .api_calls import APICalls

app = Flask(__name__)

#create instance of apicalls class at startup to quickly be able to access riot api
api = APICalls()
cache = Cache(app,config={'CACHE_TYPE': 'simple'})

#app.config["SQLALCHEMY_DATABSE_URI"] = "postgresql://postgres:1WILLchange!@localhost/mydatabase"

import LOLApp.views