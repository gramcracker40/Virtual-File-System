import sys
from flask.views import MethodView
from flask_smorest import Blueprint, abort
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from datetime import datetime

# internal
from models import PathModel
from schemas import NewPathSchema, PathSchema, UpdatePathSchema
from session_handler import sessions
from db import db
from helpers.utilities import confirm_path

blp = Blueprint("path", "path", description="Implementing functionality for paths")


@blp.route("/path")
class Path(MethodView):
    """
    functions to create paths, get all paths
    """

    @blp.arguments(NewPathSchema)
    def post(self, creation_data):
        """
        create a new file or directory, follow rules of NewPathSchema. path must be a directory. specify
        only a pid or a path, not both.
        """
        # setting required parameters
        new_path = PathModel(
            file_name=creation_data["file_name"], file_type=creation_data["file_type"]
        )

        # checks for valid session details
        if (
            creation_data["session_id"] not in sessions
            or not sessions[creation_data["session_id"]]["active"]
        ):
            abort(
                409,
                message="Session ID provided does not exist or is not active, login again...",
            )

        # checking contents.
        if (
            "contents" in creation_data.keys()
            and creation_data["file_type"] == "directory"
        ):
            abort(400, "Cannot pass contents when creating a directory.")
        elif "contents" in creation_data.keys() and creation_data["file_type"] == "file":
            new_path.contents = creation_data["contents"].encode() # encoding the string into bytes object
        elif creation_data["file_type"] == "file":  
            new_path.contents = bytes(b'') # give it a default binary value

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
        

        # set file attributes not needed from user. handled by file system.
        path_type = "d" if creation_data["file_type"] == "directory" else "-"
        new_path.permissions = f"{path_type}rw-r--r--"  # default permissions
    
        new_path.hidden = True if new_path.file_name[0] == "." else False
    
        new_path.modification_time = datetime.now()
        new_path.file_size = sys.getsizeof(new_path.contents)
        
        new_path.user_id = sessions[creation_data["session_id"]]["user_id"]
        new_path.group_id = sessions[creation_data["session_id"]]["groups"][0] # add their first group id only. 

        # check to see if file_name passed already exists in cwd.
        # prevents duplicates in our entire file system.
        paths = PathModel.query.filter(PathModel.pid == new_path.pid)
        for each in paths:
            if each.file_name == creation_data["file_name"]:
                abort(
                    409,
                    message=f"Path with name - {creation_data['file_name']} already exists in this directory",
                )

        try:
            db.session.add(new_path)
            db.session.commit()

        except IntegrityError as err:
            abort(400, message=f"Error: {err}")

        except SQLAlchemyError as err:
            abort(500, message=f"Internal database error\n\n{err}")

        return {
            "Success": True,
            "message": f"Path name - {new_path.file_name} created in directory id:{new_path.pid}",
        }, 201

    @blp.response(200, PathSchema(many=True))
    def get(self):
        """
        get all paths in file system
        """
        paths = PathModel.query.all()
        paths_list = [path.__dict__ for path in paths]

        # must decode contents to send over using json.
        for path in paths_list:
            path["contents"] = path["contents"].decode()

        return paths_list
    

    @blp.arguments(UpdatePathSchema)
    def patch(self, update_data):
        '''
        update a given path using an absolute path or relative path
            from your sessions 'cwd' in the file system. more convenient function,
            you do not have to specify an ID in the url to use. Simply pass a 'path'
        '''




@blp.route("/path/<int:path_id>")
class PathSpecificID(MethodView):
    """
    defined to read, update, delete specific directories/files.
    """

    def delete(self, path_id):
        """
        delete a path by id
        """
        path = PathModel.query.get_or_404(path_id)

        db.session.delete(path)
        db.session.commit()

        return {"message": "path deleted successfully"}, 200

    @blp.arguments(UpdatePathSchema)
    def patch(self, update_data, path_id):
        """
        update a path's details by id. change permissions, content, path_location (pid), file_name
        """
        path = PathModel.query.get_or_404(path_id)

        # TODO: update session details. need last_active refresher decorator. 
        # TODO: check the user and group permissions that session has.
        # TODO: check for permissions passed, ensure they are valid octal set. if valid, add change.

        for key in update_data:
            # update the attributes passed. if attribute is contents, encode the str to bytes.
            if key == "contents":
                setattr(path, key, update_data[key].encode())
            elif key == "permissions":
                test = permission_check()
            else:
                setattr(path, key, update_data[key])

        # only place a modification time can be updated is through an update.
        path.modification_time = datetime.now()

        try:
            db.session.commit()

        except IntegrityError as err:
            abort(400, message=f"Error: {err}")

        except SQLAlchemyError as err:
            abort(500, message=f"Internal database error\n\n{err}")

        return {"Success": True}, 201

    @blp.response(200, PathSchema)
    def get(self, path_id):
        """
        get a list of paths that have the same pid (in the same directory)
        """
        return PathModel.query.filter(PathModel.pid == path_id)


class PathFiltering(MethodView):
    '''
    The routes built to do things with paths based on filtering. 
    '''

    
    def get(self, filter_data):
        '''
        Get a list of paths based on PathFilterSchema. 
        Suported operators:
            file_name
        '''