from flask import request
from flask.views import MethodView
from flask_smorest import Blueprint, abort
from passlib.hash import pbkdf2_sha256
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from db import db
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from datetime import datetime, date, time

from models import PathModel, UserModel
from schemas import NewSessionSchema, SessionDeleteSchema
from session_handler import sessions
from helpers.sessions import rand_string


# flask_smorest "blueprint" that will map routes in organized fashion
blp = Blueprint("session", "session", description="Implementing functionality for sessions")

# # session timeout duration. 
session_logout_duration = time(0,30,0) # (hours, minutes, seconds)

@blp.route("/session")
class Session(MethodView):

    @blp.arguments(NewSessionSchema)
    def post(self, login_data):
        '''
        post your login info, username and password to initiate a session.
        Record the session details to make subsequent calls to the api. 

        ALL Routes need a session_id passed to ensure the call is from a logged in user.
        '''
        #TODO add spam check and create lockouts after certain number of tries.
        user = UserModel.query.filter_by(username=login_data['username']).first()
        
        id = rand_string(size=32)
        if user and pbkdf2_sha256.verify(login_data["password"], user.password):
            sessions[id] = {
                "success": True, "user_id": user.id, 
                "groups": [each.id for each in user.groups], "session_id": id,
                "username": user.username, "cwd_id": 0, "active":True, "last_active": datetime.now()
            }
            return sessions[id], 201
        
        abort(401, message="Invalid credentials")

    @blp.arguments(SessionDeleteSchema)
    def delete(self, data):
        '''
        delete a session given an ID.
        '''
        try:
            del sessions[data["session_id"]]
            return {"Success": True}, 200
        except KeyError as err:
            abort(404, message=f"Error: session {err} does not exist.")
    
    def put(self):
        '''
        update all sessions activity. background task runs this route every 30 seconds. 
        filters all of the inactive sessions out of the sessions object. 
        '''
        start_time = datetime.now()

        #TODO: check the private key that only the background task should have access to.
        #TODO: add private key generation to beginning and place as arg in background task. 

        # update the activity if they've been active 
        # in the last session_logout_duration
        to_delete = []
        for session in sessions: 
            elapsed_time = start_time - sessions[session]["last_active"]
            hours, remainder = divmod(elapsed_time.total_seconds(), 3600)
            minutes, seconds = divmod(remainder, 60)
            time_obj = time(int(hours), int(minutes), int(seconds))

            if time_obj > session_logout_duration:
                sessions[session]["active"] = False
                to_delete.append(session)
       
        # perform removal after loop so dict does not change size
        for each in to_delete: 
            del sessions[each]

        return {"Success": True}, 200


#sessions[session_id]["last_active"] = start_time if session_id else None