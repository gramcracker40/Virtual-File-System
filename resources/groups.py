from flask import request
from flask.views import MethodView
from flask_smorest import Blueprint, abort
from passlib.hash import pbkdf2_sha256
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from db import db
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from datetime import datetime, date, time

from models import GroupModel
from schemas import NewGroupSchema

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
            abort(409, message=f"User with - {err} - already exists")

        except SQLAlchemyError as err:
            abort(500, message=f"Database error occurred, error: {err}")

        return {"Success":True, "message":f"group '{group_data['name']}' has been created"}
