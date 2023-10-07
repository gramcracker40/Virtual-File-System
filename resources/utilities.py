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



def search_path(path:str, session_id:str) -> int:
    '''
    returns: pid of given path
    
    given an absolute or relative path. search for it in the file system. 
    ../../ is back two directories. ../ one, etc...
    
    /users/bench/test        --> absolute path
    cwd: /users,  bench/test --> relative path

    if '-1' is returned, path was not found. 
    0 and up are the pid of the given path
    '''

    path_type = "abs" if path[0] == "/" else "rel"
    path_parts = path.split("/")
    dir_name = path_parts[-1]

    potential_paths = PathModel.query.filter(PathModel.file_name == dir_name)

    for each in potential_paths:
        if path_type == "rel":
            pass
        else: # absolute path must end up at root, 
            #  so if you can trace the pid's back to 0 it exists
            pass







@blp.route("/utilities/cd")
class ChangeDirectory(MethodView):
    '''
    change the 'cwd' of the passed session_id. 
    can specify absolute or relative path. 
    see, CDschema for further clarity.  
    '''
    
    def post(self, cd_params):
        '''
        
        '''




@blp.route("/utilities/ls")
class ListDirectory(MethodView):
    '''
    grabs all the files from the specified directory. 
    can specify absolute or relative paths.
    can specify pid. 
    path must be a valid directory or 404 will be returned. 
    '''
    #LS-Schema TODO
    def get(self, ls_params):
        '''
        get all files in the directory specified.
        no params passed = return sessions 'cwd'.
        can specify absolute path or relative path from
        the sessions 'cwd'.
        '''


#PWD

#LS

#CD