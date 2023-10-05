from flask import request
from flask.views import MethodView
from flask_smorest import Blueprint, abort
from passlib.hash import pbkdf2_sha256
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from db import db
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from datetime import datetime, date, time

from models import PathModel
from schemas import NewPathSchema

blp = Blueprint("path", "path", description="Implementing functionality for paths")

@blp.route("/path")
class Path(MethodView):
    
    @blp.arguments(NewPathSchema)
    def post(self, creation_data):
        '''
        create a new file or directory
        '''
        new_model = PathModel(**creation_data)
        if "contents" not in creation_data.keys():
            new_model.contents = bytes("")

        if "permissions" not in creation_data.keys():
            init = "d" if creation_data.file_type == "directory" else "-"
            new_model.permissions = f"{init}rw-r--r--" # default permissions

        new_model.hidden = True if new_model.file_name[0] == "." else False
        
        try:
            db.session.add(new_model)
            db.session.commit()

        except IntegrityError as err:
            abort(400)

        except SQLAlchemyError as err:
            abort(500, message=f"Internal database error\n\n{err}")

        return 201, {"Success":True}



    def delete(self, path_id):
        '''
        delete a path
        '''


    def get(self, path_id):
        '''
        get a path by id
        '''


    def patch(self, path_id):
        '''
        update a path's details
        '''


