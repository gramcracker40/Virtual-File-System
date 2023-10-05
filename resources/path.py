import sys
from flask import request
from flask.views import MethodView
from flask_smorest import Blueprint, abort
from passlib.hash import pbkdf2_sha256
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from db import db
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from datetime import datetime, date, time

from models import PathModel
from schemas import NewPathSchema, PathSchema, UpdatePathSchema
from session_handler import sessions

blp = Blueprint("path", "path", description="Implementing functionality for paths")

@blp.route("/path")
class Path(MethodView):
    
    @blp.arguments(NewPathSchema)
    def post(self, creation_data):
        '''
        create a new file or directory, follow rules of NewPathSchema
        '''
        # setting required parameters
        new_path = PathModel(
            file_name=creation_data['file_name'],
            file_type=creation_data['file_type']
        )

        if creation_data['session_id'] not in sessions:
            abort(409, message="Session ID provided does not exist")

        # work with non required parameters if user does not clarify
        if "contents" not in creation_data.keys():
            new_path.contents = bytes(b"")

        if "permissions" not in creation_data.keys():
            init = "d" if creation_data['file_type'] == "directory" else "-"
            new_path.permissions = f"{init}rw-r--r--" # default permissions

        # set file attributes not needed from user. handled by file system. 
        new_path.hidden = True if new_path.file_name[0] == "." else False
        new_path.modification_time = datetime.now()
        new_path.file_size = sys.getsizeof(new_path.contents)
        new_path.pid = sessions[int(creation_data['session_id'])]["cwd_id"]
        new_path.user_id = sessions[int(creation_data['session_id'])]["user_id"]
        new_path.group_id = sessions[int(creation_data['session_id'])]["group_id"]
        
        # check to see if file_name passed already exists in cwd.
        paths = PathModel.query.filter(PathModel.pid == new_path.pid)
        for each in paths:
            if each.file_name == creation_data['file_name']:
                abort(409, message=f"Path with name - {creation_data['file_name']} already exists in this directory")

        # try to commit the changes. 
        try:
            db.session.add(new_path)
            db.session.commit()

        except IntegrityError as err:
            abort(400, message=f"Error: {err}")

        except SQLAlchemyError as err:
            abort(500, message=f"Internal database error\n\n{err}")

        return {"Success":True}, 201


    @blp.response(200, PathSchema(many=True))
    def get(self):
        '''
        get all paths in file system 
        '''
        paths = PathModel.query.all()
        
        # need to deconstruct in long winded fashion since contents is a bytes object
        paths_list = []
        for path in paths:
            paths_list.append({
                "id": path.id,
                "pid": path.pid,
                "file_name": path.file_name,
                "file_type": path.file_type, 
                "file_size": path.file_size, 
                "permissions": path.permissions, 
                "contents": path.contents.decode(),
                "user_id": path.user_id, 
                "group_id": path.group_id
            })

        return paths_list


@blp.route("/path/<int:path_id>")
class PathSpecific(MethodView):
    '''
    defined to read, update, delete specific paths. 
    '''
    def delete(self, path_id):
        '''
        delete a path by id
        '''
        path = PathModel.query.get_or_404(path_id)

        db.session.delete(path)
        db.session.commit()

        return {"message": "path deleted successfully"}, 200


    @blp.arguments(UpdatePathSchema)
    def patch(self, update_data, path_id):
        '''
        update a path's details by id. change permissions, content, path_location (pid), file_name
        '''
        path = PathModel.query.get_or_404(path_id)


        for key in update_data:  # update the attributes passed. if attribute is contents, encode the str to bytes. 
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

    def get(self, path_id):
        '''
        get a list of paths that have the same pid (in the same directory)
        '''




