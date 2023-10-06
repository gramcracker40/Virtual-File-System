'''
Define all utility functions in this file. 

examples: 'change_directory', 'long_listing', etc 

'''
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


blp = Blueprint("utilities", "utilities", description="Implementing functionality for utilities")


@blp.route("/utilities/ls/<int:session_id>")
class ls(MethodView):
    '''
    implements utility functions associated with the sessions. such as 'cd',
    'ls', 
    '''
    #LS-Schema TODO
    def get(self, session_id):
        '''
        get al
        '''


#PWD

#LS

#