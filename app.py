# factory pattern
# DOCUMENTATION:
#  While the development flask server is running on your local machine or in the cloud you can find the documentation
#  for the API by going to 127.0.0.1:5000/swagger-ui, this is a well written piece of documentation that goes over exactly
#  how to make each call to the server...

# Core
import os

# External
from werkzeug.middleware.proxy_fix import ProxyFix
from flask import Flask, jsonify
from flask_smorest import Api
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
from flask_cors import CORS
import sqlalchemy

# Internal
from db import db
from resources.path import blp as PathBlueprint
from resources.users import blp as UserBlueprint
from resources.groups import blp as GroupBlueprint
from resources.session import blp as SessionBlueprint

# Environment variables
from dotenv import dotenv_values
config = dotenv_values(".flaskenv")

production = bool(int(config["PRODUCTION"]))
db_uri = config["DBHOST"] if production else None

# factory pattern --> .flaskenv FLASK_APP, allows for simple "flask run" 
# command when running the app locally
def app():
    app = Flask(__name__)
    CORS(app)

    if production: # If deploying multiple domains with proxy servers you would need change
        app.wsgi_app = ProxyFix(
            app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1
        )

    app.config["PROPAGATE_EXCEPTIONS"] = True
    app.config["API_TITLE"] = "Virtual File System REST API"
    app.config["API_VERSION"] = "v1"
    app.config["OPENAPI_VERSION"] = "3.0.3"
    app.config["OPENAPI_URL_PREFIX"] = "/"
    app.config["OPENAPI_SWAGGER_UI_PATH"] = "/swagger-ui" # Provides a very user friendly documentations
    app.config["OPENAPI_SWAGGER_UI_URL"] = "https://cdn.jsdelivr.net/npm/swagger-ui-dist/"
    app.config["SQLALCHEMY_DATABASE_URI"] = db_uri or "sqlite:///data.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    db.init_app(app)
    
    migrate = Migrate(app, db)

    api = Api(app)
   

    with app.app_context():
        db.create_all()

    api.register_blueprint(PathBlueprint)
    api.register_blueprint(UserBlueprint)
    api.register_blueprint(GroupBlueprint)
    api.register_blueprint(SessionBlueprint)
    
    return app



