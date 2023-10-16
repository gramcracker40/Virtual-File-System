# external
import sys
from flask.views import MethodView
from flask_smorest import Blueprint, abort
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from datetime import datetime

# internal
from models import PathModel, UserModel, GroupModel
from schemas import NewPathSchema, PathSchema, UpdatePathSchema, DeletePathSchema, GetPathSchema
from session_handler import sessions
from db import db
from helpers.utilities import confirm_path, construct_path
from helpers.sessions import session_id_check, update_session_activity

from helpers.path import valid_permission_octal_check, octal_to_permission_string, permissions_check, owner_check

# path routes object
blp = Blueprint("path", "path", description="Implementing functionality for paths")

default_permissions = "rwx------"

@blp.route("/path")
class Path(MethodView):
    """
    functions to create, read, update, delete paths using a variety of parameters
        that are clearly defined in the schemas for each route
    """
    @classmethod
    def id_check(self, data):
        # grab the id of the path we are working with
        if "path" in data.keys():
            id = confirm_path(data['path'], data['session_id'])[0]
        elif "id" in data.keys():
            id = data['id']
        else:
            abort(400, message="Please pass either a valid 'path' or 'id'")
        
        return id

    @blp.arguments(NewPathSchema)
    def post(self, creation_data):
        """
        create a new file or directory, follow rules of NewPathSchema. 'path' must be a valid directory. specify
        only a pid or a path, not both.
        """
        # setting required parameters
        new_path = PathModel(
            file_name=creation_data["file_name"], file_type=creation_data["file_type"]
        )

        # checks for valid session details
        if not session_id_check(creation_data["session_id"]):
            abort(409, message="Session ID provided does not exist or is not active, login again...")

        # checking to see the parent directory of the new path.
        #   can be determined by 'pid' or 'path'. If neither are passed
        #   it will use the sessions cwd. can also account for root by simply being 0.
        if "pid" in creation_data.keys():
            temp = PathModel.query.filter(
                PathModel.id == creation_data["pid"],
            ).first_or_404(description="directory does not exist") \
            if creation_data["pid"] != 0 else 0 # root check
            
            new_path.pid = temp
        elif "path" in creation_data.keys():
            id, path = confirm_path(creation_data["path"], creation_data["session_id"])
            temp = PathModel.query.get_or_404(
                id, description="directory does not exist"
            ) if id != 0 else 0 

            if temp == 0:  # root check
                new_path.pid = 0
            elif temp.file_type == "directory":
                new_path.pid = id
            else:
                abort(
                    400,
                    message="'path' can not be a file. please specify a directory instead.",
                )
        else:
            new_path.pid = sessions[creation_data["session_id"]]["cwd_id"]

        # checking the sessions permission in the parent directory. if they have write permissions they will be able to create a Path in the directory. 
        new_path_dir = PathModel.query.get_or_404(new_path.pid, description=f"Could not find parent directory for creation") \
                    if new_path.pid != 0 else 0
        has_permission = permissions_check(creation_data['session_id'], new_path_dir, permission_needed="w")
        
        if not has_permission:
            abort(400, message=f"session user does not have the correct permissions in directory '{new_path_dir.file_name}'")
        
        # check to see if file_name passed already exists in cwd.
        # prevents duplicates in the entire file system.
        paths = PathModel.query.filter(PathModel.pid == new_path.pid)
        for each in paths:
            if each.file_name == creation_data["file_name"]:
                abort(
                    409,
                    message=f"Path with name - {creation_data['file_name']} already exists in this directory",
                )

        # checking contents. no contents allowed when creating a directory.
        if ("contents" in creation_data.keys() 
            and creation_data["file_type"] == "file"
        ):
            new_path.contents = creation_data["contents"].encode() # encoding the string into bytes object
        elif creation_data["file_type"] == "file": 
            new_path.contents = bytes(b'')
        elif (
            "contents" in creation_data.keys()
            and creation_data["file_type"] == "directory"
        ):
            abort(400, "Cannot pass contents when creating a directory.")
    
        # set path attributes not accepted from user on creation of path
        path_type = "d" if creation_data["file_type"] == "directory" else "-"
        new_path.permissions = f"{path_type}{default_permissions}"
    
        new_path.hidden = True if new_path.file_name[0] == "." else False
    
        new_path.modification_time = datetime.now()
        new_path.file_size = sys.getsizeof(new_path.contents)
        
        new_path.user_id = sessions[creation_data["session_id"]]["user_id"]
        new_path.group_id = sessions[creation_data["session_id"]]["groups"][0] # add their first group id only. 

        try:
            db.session.add(new_path)
            db.session.commit()

        except IntegrityError as err:
            abort(400, message=f"Error: {err}")

        except SQLAlchemyError as err:
            abort(500, message=f"Internal database error\n\n{err}")

        update_session_activity(creation_data["session_id"])

        return {
            "Success": True,
            "message": f"Path name - {new_path.file_name} created in '{construct_path(new_path.pid)}'",
        }, 201
    
    @blp.arguments(GetPathSchema)
    @blp.response(200, PathSchema())
    def get(self, path_data):
        """
        get a specific path and its contents in the file system. only use when trying to get
            the contents of a file. Must have appropriate permissions on the file. 
        """
        if not session_id_check(path_data["session_id"]):
            abort(409, message="Session ID provided does not exist or is not active, login again...")

        id = Path.id_check(path_data)

        if id == 0: 
            abort(400, message="root is not a file or directory")

        path = PathModel.query.get_or_404(id)

        # checking the sessions permission in the desired path.  
        has_permission = permissions_check(path_data['session_id'], path, permission_needed="r")
        if not has_permission:
            abort(400, message=f"session user does not have the correct permissions in Path: '{path.file_name}'")

        update_session_activity(path_data["session_id"])

        return path, 200

    
    @blp.arguments(UpdatePathSchema)
    def patch(self, update_data):
        '''
        update a given path, can pass a 'path' to update or simply the 'id' of the Path. Will automatically change the
            modification_time of the path. 
        '''

        # checks for valid session details
        if not session_id_check(update_data["session_id"]):
            abort(409, message="Session ID provided does not exist or is not active, login again...")

        id = Path.id_check(update_data)
        path = PathModel.query.get_or_404(id)
        owner = owner_check(update_data["session_id"], path)

        # runs through each key passed to update the given path with. performs permission checks at each key
        # making sure that the calling sessions has the appropriate rights for that action. 
        for key in update_data:
            if key == "contents":
                # need 'w' permissions to update the contents of a file. 
                has_permission = permissions_check(update_data['session_id'], path, permission_needed="w")
                if not has_permission:
                    abort(400, message=f"session user does not have the correct permissions in Path: '{path.file_name}'\nneed 'w' permissions. ")
                
                if path.file_type != "directory":
                    setattr(path, key, update_data[key].encode())
                else:
                    abort(400, message="You can not set contents on a directory. ")
            elif key == "permissions":
                permission_rwx = octal_to_permission_string(update_data["permissions"])\
                    if valid_permission_octal_check(update_data["permissions"]) else None
                temp_type = "d" if path.file_type == "directory" else "-"

                # permissions_check to ensure the calling session has rights to change permissions on Path. 
                if not owner and 2 not in sessions[update_data["session_id"]]["groups"]:
                    abort(400, message="Only the owner of the Path and admins can update the permissions of a path.")
                
                if permission_rwx != None:
                    permission_rwx_full = f"{temp_type}{permission_rwx}"
                    setattr(path, key, permission_rwx_full)
                else:
                    abort(400, message=f"invalid permissions --> {update_data['permissions']}")

            elif key == "group_id":
                group = GroupModel.query.get_or_404(update_data[key], 
                            description=f"Group with 'group_id':{update_data[key]} does not exist")
                if not owner and 2 not in sessions[update_data["session_id"]]["groups"]:
                    abort(400, message="Only the owner of the Path and admins can update the group_id of a Path.")
                setattr(path, key, group.id)             
            
            elif key == "group_name":
                group = GroupModel.query.filter(GroupModel.name == update_data['group_name']).first_or_404(
                    description = f"Group with 'name':{update_data[key]} does not exist")
                if not owner and 2 not in sessions[update_data["session_id"]]["groups"]:
                    abort(400, message="Only the owner of the Path and admins can update the group_id of a Path.")
                setattr(path, "group_id", group.id)
        
            elif key == "user_id":
                user = UserModel.query.get_or_404(update_data[key], 
                            description=f"User with 'user_id':{update_data[key]} does not exist")
                if not owner and 2 not in sessions[update_data["session_id"]]["groups"]:
                    abort(400, message="Only the owner of the Path and admins can update the user_id of a Path.")
                setattr(path, key, user.id)   

            elif key == "username":
                user = UserModel.query.filter(UserModel.username == update_data[key]).first_or_404(
                    description = f"User with 'username':{update_data[key]} does not exist")
                if not owner and 2 not in sessions[update_data["session_id"]]["groups"]:
                    abort(400, message="Only the owner of the Path and admins can update the user_id of a Path.")
                setattr(path, "user_id", user.id)
            else:
                setattr(path, key, update_data[key])

        # only place a modification time can be updated is through an update.
        path.modification_time = datetime.now()
        update_session_activity(update_data["session_id"])

        try:
            db.session.commit()

        except IntegrityError as err:
            abort(400, message=f"Error: {err}")

        except SQLAlchemyError as err:
            abort(500, message=f"Internal database error\n\n{err}")

        return {"Success": True}, 201

    @blp.arguments(DeletePathSchema)
    def delete(self, delete_data):
        '''
        delete a path, pass a valid absolute or relative path or simply
            the id of the path. must have session_id included in request 
            to ensure the permission of the calling session to perform the action
        '''
        # checks for valid session details
        if not session_id_check(delete_data["session_id"]):
            abort(409, message="Session ID provided does not exist or is not active, login again...")

        id = Path.id_check(delete_data)        
        path = PathModel.query.get_or_404(id)
        path_str = construct_path(id)
        owner = owner_check(delete_data["session_id"], path)

        # permissions check
        if not owner and 2 not in sessions[delete_data["session_id"]]["groups"]:
            abort(400, message="Only the owner of the Path and admins can delete a Path")

        update_session_activity(delete_data["session_id"])

        # need to add recursive function to delete everything beneath it if it is a directory. 
        # will leave stranded paths. 
        db.session.delete(path)
        db.session.commit()

        return {"Success": True, "message": f"successfully deleted '{path_str}'"}, 200