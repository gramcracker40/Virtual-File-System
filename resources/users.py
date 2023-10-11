from flask import request
from flask.views import MethodView
from flask_smorest import Blueprint, abort
from passlib.hash import pbkdf2_sha256
from db import db
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

from models import UserModel, GroupModel
from schemas import NewUserSchema, UserSchema

blp = Blueprint("users", "users", description="Implementing functionality for users")


@blp.route("/users")
class Users(MethodView):

    @blp.arguments(NewUserSchema)
    def post(self, user_data):
        '''
        creates a new user
        '''
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
        except IntegrityError as err:
            #duplicate = str(err.orig).split('"')[1]
            abort(409, message=f"User with - {err} - already exists")

        except SQLAlchemyError as err:
            abort(500, message=f"Database error occurred, error: {err}")

        new_user = UserModel.query.filter(UserModel.username == user_data["username"]).first()
        
        return {"message": "User created successfully", "user_id": new_user.id}, 201

    @blp.response(200, UserSchema(many=True))
    def get(self):
        '''
        get all users. 
        '''
        return UserModel.query.all()


@blp.route("/users/<int:user_id>")
class UserSpecific(MethodView):
    '''
    perform operations on a given user
    '''
    @blp.response(200, UserSchema)
    def get(self, user_id):
        '''
        get a users info by id
        '''
        return UserModel.query.get_or_404(user_id)




