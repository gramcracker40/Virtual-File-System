from flask import request
from flask.views import MethodView
from flask_smorest import Blueprint, abort
from passlib.hash import pbkdf2_sha256
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from db import db
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from datetime import datetime, date, time

blp = Blueprint("create", "create", description="All creation functionality")

@blp.route("/create")
class Create(MethodView):
    
    def post(self, creation_data):
        '''
        create a new file or directory
        '''
