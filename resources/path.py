from flask import request
from flask.views import MethodView
from flask_smorest import Blueprint, abort
from passlib.hash import pbkdf2_sha256
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from db import db
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from datetime import datetime, date, time

from models import PathModel

blp = Blueprint("path", "path", description="Implementing functionality for paths")

@blp.route("/path")
class Path(MethodView):
    
    def post(self, creation_data):
        '''
        create a new file or directory
        '''


    def delete(self, path_id):
        '''
        delete a path
        '''


    def get(self, path_id):
        '''
        get a path by id
        '''


    def patch(self, path_id):
        '''
        update a path's details
        '''


