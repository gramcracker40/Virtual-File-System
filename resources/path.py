import sys
from flask.views import MethodView
from flask_smorest import Blueprint, abort
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from datetime import datetime

# internal
from helpers.sessions import session_timer_check
from models import PathModel
from schemas import NewPathSchema, PathSchema, UpdatePathSchema
from session_handler import sessions
from db import db

blp = Blueprint("path", "path", description="Implementing functionality for paths")

@blp.route("/path")
class Path(MethodView):
    '''
    TODO: check if the contents can be passed as str representations of the binary over JSON. 
            need to see if we can store multiple file formats... and actually retrieve the data.
    '''
    @blp.arguments(NewPathSchema)
    def post(self, creation_data):
        """
        create a new file or directory, follow rules of NewPathSchema
        """
        # setting required parameters
        new_path = PathModel(
            file_name=creation_data["file_name"], file_type=creation_data["file_type"]
        )

        if creation_data["session_id"] not in sessions or not sessions[creation_data["session_id"]]["active"]:
            abort(409, message="Session ID provided does not exist or is not active, login again...")

        # work with "non-required" parameters if user does not clarify.
        # # Check NewPathSchema for all parameters
        if "contents" in creation_data.keys() and creation_data["file_type"] == "directory":
            abort(400, "Cannot pass contents when creating a directory.")
        if "contents" not in creation_data.keys():
            new_path.contents = bytes(b"")
        else:
            new_path.contents = creation_data["contents"].encode()

        # if 'pid' is not in the JSON object, set the pid of the created file to the 
        # # sessions 'cwd'
        if "pid" not in creation_data.keys():
            new_path.pid = sessions[creation_data["session_id"]]["cwd_id"]
        else:
            new_path.pid = creation_data["pid"]


        # set file attributes not needed from user. handled by file system.
        path_type = "d" if creation_data["file_type"] == "directory" else "-"
        new_path.permissions = f"{path_type}rw-r--r--"  # default permissions
        new_path.hidden = True if new_path.file_name[0] == "." else False
        new_path.modification_time = datetime.now()
        new_path.file_size = sys.getsizeof(new_path.contents)
        new_path.user_id = sessions[creation_data["session_id"]]["user_id"]
        new_path.group_id = sessions[creation_data["session_id"]]["group_id"]

        # check to see if file_name passed already exists in cwd.
        paths = PathModel.query.filter(PathModel.pid == new_path.pid)
        for each in paths:
            if each.file_name == creation_data["file_name"]:
                abort(
                    409,
                    message=f"Path with name - {creation_data['file_name']} already exists in this directory",
                )

        # try to commit the changes.
        try:
            db.session.add(new_path)
            db.session.commit()

        except IntegrityError as err:
            abort(400, message=f"Error: {err}")

        except SQLAlchemyError as err:
            abort(500, message=f"Internal database error\n\n{err}")

        return {"Success": True}, 201

    @blp.response(200, PathSchema(many=True))
    def get(self):
        """
        get all paths in file system
        """
        paths = PathModel.query.all()
        paths_list = [path.__dict__ for path in paths]
        
        for path in paths_list:
            path["contents"] = path["contents"].decode() 

        return paths_list


@blp.route("/path/<int:path_id>")
class PathSpecific(MethodView):
    """
    defined to read, update, delete specific paths.
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

        for key in update_data:
         # update the attributes passed. if attribute is contents, encode the str to bytes.
            if key != "contents":
                setattr(path, key, update_data[key])
            else:
                setattr(path, key, update_data[key].encode())

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
        return PathModel.query.get_or_404(path_id)
