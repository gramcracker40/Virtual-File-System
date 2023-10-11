from flask import request
from flask.views import MethodView
from flask_smorest import Blueprint, abort
from passlib.hash import pbkdf2_sha256
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from db import db
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from datetime import datetime, date, time

from models import GroupModel, UserModel, UsersGroupsModel
from schemas import NewGroupSchema, UpdateGroupSchema, GroupSchema

blp = Blueprint("groups", "groups", description="Implementing functionality for groups")


@blp.route("/groups")
class Groups(MethodView):

    @blp.arguments(NewGroupSchema)
    def post(self, group_data):
        '''
        creates a new group
        '''
        try:
            new_group = GroupModel(**group_data)

            db.session.add(new_group)
            db.session.commit()
        except IntegrityError as err:
            #duplicate = str(err.orig).split('"')[1]
            abort(409, message=f"Group with - {new_group.name} - already exists")

        except SQLAlchemyError as err:
            abort(500, message=f"Database error occurred, error: {err}")

        return {"Success":True, "message":f"group '{group_data['name']}' has been created"}
    
    @blp.response(200, GroupSchema(many=True))
    def get(self):
        return GroupModel.query.all()

    @blp.arguments(NewGroupSchema)
    def delete(self, group):
        '''
        delete a group given the name of the group.  
        '''
        group = GroupModel.query.filter(GroupModel.name == group['name']).first_or_404()

        db.session.delete(group)
        db.session.commit()

        return {"message": f"group {group.name} deleted successfully"}, 200
    
    @blp.arguments(UpdateGroupSchema)
    def patch(self, update_data):
        '''
        add or remove a user from the group, give the group_id or group_name and the user_id or username. 
        also pass the action, which needs to be "add" or "remove"
        '''
        if "group_id" in update_data.keys():
            group = GroupModel.query.get_or_404(update_data["group_id"])
        elif "group_name" in update_data.keys():
            group = GroupModel.query.filter(GroupModel.name == update_data["group_name"]).first_or_404()

        if "user_id" in update_data.keys():
            user = UserModel.query.get_or_404(update_data["user_id"])
        elif "username" in update_data.keys():
            user = UserModel.query.filter(UserModel.username == update_data["username"]).first_or_404()
        else:
            abort(400, message="Please specify either a user_id or username of a user to add to this group")

        try:
            if update_data["action"] == "add" and user not in group.users:
                group.users.append(user)
            else:
                group.users.remove(user)
        except ValueError as err:
            abort(400, message="User is not in group")
        

        db.session.add(group)
        db.session.add(user)
        db.session.commit()

        return {"Success":True}, 201