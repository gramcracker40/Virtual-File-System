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
    TODO: check if the contents can be passed as str representations of the binary over JSON.
            need to see if we can store multiple file formats... and actually retrieve the data.
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

        # checks for session details
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

        # if no contents, give defaults, else encode contents to bytes
        if "contents" not in creation_data.keys():
            new_path.contents = bytes(b"")
        else:
            new_path.contents = creation_data["contents"].encode()

        # determine the pid of the new path being created. this function can accept a pid, path
        # # or if they decide not to pass any of them it will use the sessions cwd.
        print("Here 1")
        if "pid" in creation_data.keys():
            new_path.pid = creation_data["pid"]
        elif "path" in creation_data.keys():
            id, path = confirm_path(creation_data["path"], creation_data["session_id"])
            temp = PathModel.query.get_or_404(
                id, description="directory does not exist"
            )
            print("Here 2")

            if temp.file_type == "directory":
                new_path.pid = id
            else:
                abort(
                    400,
                    message="'path' can not be a file. please specify a directory instead.",
                )
        else:
            new_path.pid = sessions[creation_data["session_id"]]["cwd_id"]
        
        print("Here 3")

        # really just a check to make sure the pid set exists and is a directory
        parent_directory = PathModel.query.get_or_404(new_path.pid, description="Could not find parent directory.").file_type \
            if new_path.pid != 0 else "directory" 
        
        if parent_directory == "file":
            abort(
                400,
                message="Can not create a file inside of a file. Please specify a valid directory.",
            )
        print("Here 4")

        # set file attributes not needed from user. handled by file system.
        path_type = (
            "d" if creation_data["file_type"] == "directory" else "-"
        )  
        new_path.permissions = f"{path_type}rw-r--r--"  # default permissions
        new_path.hidden = True if new_path.file_name[0] == "." else False
        new_path.modification_time = datetime.now()
        new_path.file_size = sys.getsizeof(new_path.contents)
        new_path.user_id = sessions[creation_data["session_id"]]["user_id"]
        new_path.group_id = sessions[creation_data["session_id"]]["groups"][0] # add their first group id only. 

        # check to see if file_name passed already exists in cwd.
        # prevents duplicates in our confirm_path function.
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


@blp.route("/path/<int:path_id>")
class PathSpecificID(MethodView):
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

        # TODO: update session details. need last_active refresher decorator. 
        # TODO: check the user and group permissions that session has.
        # TODO: check for permissions passed, ensure they are valid octal set. if valid, add change.

        for key in update_data:
            # update the attributes passed. if attribute is contents, encode the str to bytes.
            if key != "contents":
                setattr(path, key, update_data[key])
            else:
                setattr(path, key, update_data[key].encode())

        # only place a path can be updated. modification times are accurate.
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
        return PathModel.query.get_or_404(path_id)
