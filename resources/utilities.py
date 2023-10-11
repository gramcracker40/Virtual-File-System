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
from models import PathModel
from schemas import UtilitySchema
from session_handler import sessions
from db import db
from errors import InsufficientParamaters
from helpers.utilities import confirm_path, confirm_path_by_id, construct_path, change_directory, print_working_directory

blp = Blueprint("utilities", "utilities", description="Implementing functionality for utilities")


@blp.route("/utilities/cd")
class ChangeDirectory(MethodView):
    '''
    change the 'cwd' of the passed session_id. 
    can specify absolute or relative path. 
    see, CDschema for further clarity.  
    '''
    @blp.arguments(UtilitySchema)
    def post(self, cd_params):
        '''
        
        '''
        new_dir_path = change_directory(cd_params["path"], cd_params["session_id"])
        return {"new_path": new_dir_path}, 200


@blp.route("/utilities/ls")
class ListDirectory(MethodView):
    '''
    grabs all the files from the specified directory. 
    can specify absolute or relative paths.
    path must be a valid directory or 404 will be returned. 
    '''
    @blp.arguments(UtilitySchema)
    def get(self, ls_params):
        '''
        get all files in the directory specified.
        no params passed = return sessions 'cwd'.
        can specify absolute path or relative path from
        the sessions 'cwd'.
        '''


@blp.route("/utilities/pwd")
class PrintWorkingDirectory(MethodView):
    '''
    Gets the current working directory
    '''

    @blp.arguments(UtilitySchema)
    def get(self, pwd_params):
        '''
        '''
        cwd_path = print_working_directory(pwd_params["session_id"])

        return {"cwd": cwd_path}, 200
    
