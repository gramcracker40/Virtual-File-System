from flask import request
from flask.views import MethodView
from flask_smorest import Blueprint, abort
from passlib.hash import pbkdf2_sha256
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from db import db
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from datetime import datetime, date, time

from models import PathModel, UserModel
from schemas import UserSchema
from session_handler import sessions

blp = Blueprint("session", "session", description="Implementing functionality for sessions")

session_counter = 0


@blp.route("/session")
class Session(MethodView):
    
    @blp.arguments(UserSchema)
    def post(self, login_data):
        '''
        post your login info, username and password to initiate a session.
        Record the session details to make subsequent calls to the api. 
        '''
        global session_counter
        user = UserModel.query.filter_by(username=login_data['username']).first()

        # check to see if user_id already has a session? or just overwrite the old session data?
        session_counter += 1
        if user and pbkdf2_sha256.verify(login_data["password"], user.password):
            sessions[session_counter] = {
                "success": True, "user_id": user.id, 
                "group_id": user.group.id, "session_id": session_counter,
                "username": user.username, "cwd_id": 0
            }
            return sessions[session_counter], 201
        
        
        
        abort(401, message="Invalid credentials")

    
