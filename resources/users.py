'''
CRUD functions for Users



'''


from flask.views import MethodView
from flask_smorest import Blueprint, abort
from passlib.hash import pbkdf2_sha256
from db import db
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from datetime import datetime

from models import UserModel, GroupModel, PathModel
from schemas import NewUserSchema, UserSchema, DeleteUserSchema
from session_handler import sessions
from helpers.sessions import session_id_check, update_session_activity

blp = Blueprint("users", "users", description="Implementing functionality for users")

@blp.route("/users")
class Users(MethodView):

    @blp.arguments(NewUserSchema)
    def post(self, user_data):
        '''
        creates a new user, automatically creates a directory with their username in "users"
        only admins can create new users. 

        '''
        if not session_id_check(user_data["session_id"]):
            abort(409, message="Session ID provided does not exist or is not active, login again...")

        # 2 will always be the id of the admin group. 
        if 2 not in sessions[user_data["session_id"]]["groups"]:
            abort(400, message="You must be the in the admin group to create new users.")

        if UserModel.query.filter(UserModel.username == user_data["username"]).first():
            abort(409, message="A user with that username already exists")
           
        default_group = GroupModel.query.filter(GroupModel.name == "default").first()

        try:
            user = UserModel(
                username=user_data['username'], 
                password=pbkdf2_sha256.hash(user_data['password']),
            )
            user.groups.append(default_group)

            db.session.add(user)
            db.session.commit()

            # grab new user to set the user_id of the new users directory. 
            newly_made_user = UserModel.query.filter(UserModel.username == user_data['username']).first()
            
            # builds the starting directory for the user in the file system 
            users_folder = PathModel(
                file_name=user_data["username"],
                file_type="directory",
                permissions="drwx------", 
                user_id=newly_made_user.id, 
                group_id=1, 
                file_size=0, 
                modification_time=datetime.now(), 
                pid=1, # 1 is the users directory always. see initialize_defaults.py
                hidden=False
            )

            db.session.add(users_folder)
            db.session.commit()
        except IntegrityError as err:
            abort(409, message=f"User with - {err} - already exists")

        except SQLAlchemyError as err:
            abort(500, message=f"Database error occurred, error: {err}")

        new_user = UserModel.query.filter(UserModel.username == user_data["username"]).first()
        
        update_session_activity(user_data["session_id"])
        
        return {"message": "User created successfully", "user_id": new_user.id}, 201

    @blp.response(200, UserSchema(many=True))
    def get(self):
        '''
        get all users. and their group membership. 
        '''
        return UserModel.query.all()
    
    @blp.arguments(DeleteUserSchema())
    def delete(self, user_data):
        '''
        delete a user by passing the user id or the username
        user must be an admin
        '''
        try:
            if (
                user_data["session_id"] not in sessions
                or not sessions[user_data["session_id"]]["active"]
            ):
                abort(
                    409,
                    message="Session ID provided does not exist or is not active, login again...",
                )

            if 2 not in sessions[user_data['session_id']]['groups']: # admin check
                abort(400, message=f"session user is not an admin and can not create other users")

            if "id" in user_data.keys():
                user = UserModel.query.get_or_404(user_data["id"], description="User ID not found")
            elif "username" in user_data.keys():
                user = UserModel.query.filter(UserModel.username == user_data["username"])\
                    .first_or_404(description="username not found")
            else:
                abort(400, message="Please pass a valid user id or username")

            db.session.delete(user)
            db.session.commit()

            update_session_activity(user_data["session_id"])
            
            return {"Success": True}, 200

        except SQLAlchemyError as err:
            abort(500, message=f"Internal server error --> {err}")

    #add patch method


