'''
HTTP Methods on Groups

CRUD operations only

see schemas.py for the smorest Blueprint decorators listed above each class method

'''


from flask.views import MethodView
from flask_smorest import Blueprint, abort
from db import db
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

from models import GroupModel, UserModel, UsersGroupsModel
from schemas import NewGroupSchema, UpdateGroupSchema, GroupSchema, DeleteGroupSchema
from helpers.sessions import session_id_check, update_session_activity
from session_handler import sessions

blp = Blueprint("groups", "groups", description="Implementing functionality for groups")

@blp.route("/groups")
class Groups(MethodView):

    @blp.arguments(NewGroupSchema)
    def post(self, group_data):
        '''
        creates a new group, adds the session user who created it as the first member. 
        '''
        # checks for valid session details
        if not session_id_check(group_data["session_id"]):
            abort(409, message="Session ID provided does not exist or is not active, login again...")

        try:
            user = UserModel.query.get_or_404(sessions[group_data['session_id']]['user_id'])
            new_group = GroupModel(name=group_data["name"])

            new_group.users.append(user)
            sessions[group_data["session_id"]]["groups"].append(new_group.id)

            db.session.add(new_group)
            db.session.add(user)
            db.session.commit()

            update_session_activity(group_data["session_id"])
        except IntegrityError as err:
            #duplicate = str(err.orig).split('"')[1]
            abort(409, message=f"Group with name - '{new_group.name}' - already exists")

        except SQLAlchemyError as err:
            abort(500, message=f"Database error occurred, error: {err}")

        return {"Success":True, "message":f"group '{group_data['name']}' has been created"}
    
    @blp.response(200, GroupSchema(many=True))
    def get(self):
        '''
        get all groups and their users
        '''
        return GroupModel.query.all()

    @blp.arguments(DeleteGroupSchema)
    def delete(self, group_data):
        '''
        delete a group given the name/id of the group. only admins can delete groups.
        '''
        if not session_id_check(group_data["session_id"]):
            abort(409, message="Session ID provided does not exist or is not active, login again...")
        
        # seeing which groups the calling member is associated with. 
        session_groups = sessions[group_data['session_id']]['groups']

        # determining the parameter passed to filter on group
        if "name" in group_data.keys():
            group = GroupModel.query.filter(GroupModel.name == group_data['name']).first_or_404(description="Could not find a group with the name passed")
        elif "id" in group_data.keys():
            group = GroupModel.query.get_or_404(group_data['id'], description="Group id does not exist")
        else:
            abort(400, message="Please pass a 'name' or 'id' of a valid group to delete a group.")

        # only admins can delete groups
        if group.id not in session_groups and sessions[group_data['session_id']]['admin']:
            abort(400, message="You can not delete a group you are not a member of.")

        db.session.delete(group)
        db.session.commit()

        update_session_activity(group_data["session_id"])

        return {"Success": True, "message": f"group {group.name} deleted successfully"}, 200
    
    @blp.arguments(UpdateGroupSchema)
    def patch(self, update_data):
        '''
        add or remove a user from the group, give the group_id or group_name and the user_id or username. 
        also pass the action, which needs to be "add" or "remove". must be a member of the group to add/remove
        from the group.
        '''
        if not session_id_check(update_data["session_id"]):
            abort(409, message="Session ID provided does not exist or is not active, login again...")

        session_groups = sessions[update_data["session_id"]]["groups"]
        
        # checking for group to perform action on 
        if "group_id" in update_data.keys():
            group = GroupModel.query.get_or_404(update_data["group_id"])
        elif "group_name" in update_data.keys():
            group = GroupModel.query.filter(GroupModel.name == update_data["group_name"]).first_or_404()

        if group.id not in session_groups:
            abort(400, message="session user is not in the group and cannot add/remove on the group")

        # checking for user to perform action on 
        if "user_id" in update_data.keys():
            user = UserModel.query.get_or_404(update_data["user_id"])
        elif "username" in update_data.keys():
            user = UserModel.query.filter(UserModel.username == update_data["username"]).first_or_404()
        else:
            abort(400, message="Please specify either a user_id or username of a user to add to this group")

        # determining the 'action' to do with verified group and user
        try:
            if update_data["action"] == "add" and user not in group.users:
                group.users.append(user)
                sessions[update_data["session_id"]]["groups"].append(group.id)
            elif update_data["action"] == "remove" and user in group.users:
                group.users.remove(user)
                sessions[update_data["session_id"]]["groups"].remove(group.id)
        except ValueError as err: #edge case
            abort(400, message="User is not in group")
        
        # commit to the database
        db.session.add(group)
        db.session.add(user)
        db.session.commit()
        
        update_session_activity(update_data["session_id"])

        return {"Success":True}, 201