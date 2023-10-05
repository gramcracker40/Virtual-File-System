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

blp = Blueprint("session", "session", description="Implementing functionality for sessions")

sessions = {}

@blp.route("/session")
class Session(MethodView):

    @blp.arguments(UserSchema)
    def post(self, login_data):
        '''
        post your login info, username and password to initiate a session.
        Record the session details to make subsequent calls to the api. 
        '''

        user = UserModel.query.filter_by(username=login_data['username']).first()

        # check to see if user_id already has a session. 


        if user and pbkdf2_sha256.verify(login_data["password"], user.password):
            sessions[user.username] = {
                "success": True, "user_id": user.id, 
                "group_id": user.group.id, "session_id": len(sessions)
            }
            return sessions[-1], 201

        abort(401, message="Invalid credentials")