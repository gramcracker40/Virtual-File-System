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


blp = Blueprint("utilities", "utilities", description="Implementing functionality for utilities")

def construct_path(id:int) -> str:
    path = ""

    # Starting point of the path based on the id
    path_itr = PathModel.query.filter(PathModel.id == id)
    
    # Iterate over every parent directory and add the name to the path
    while path_itr.pid != 0:
        path = f"{path_itr.file_name}/" + path

    return path


def confirm_path(path:str, session_id:str) -> tuple((int, str)):
    '''
    returns: id of given path
    
    given an absolute or relative path. search for it in the file system. 
    ../../ is back two directories. ../ one, etc...
    
    /users/bench/test        --> absolute path
    cwd: /users,  bench/test --> relative path

    if '-1' is returned, path was not found. 
    0 and up are the pid of the given path
    '''
    try:
        path_type = "abs" if path[0] == "/" else "rel"
        path_parts = path.split("/")
        dir_name = path_parts[-1]
        path_parts.reverse()
        potential_paths = PathModel.query.filter(PathModel.file_name == dir_name)

        for potential_path in potential_paths:
            if path_type == "rel":
                pass
            else: # absolute path must end up at root, 
                #  so if you can trace the pid's back to 0 it exists
                # Save the initial file/path id
                initial_id = potential_path.id

                for part in path_parts:
                    # Check the file name, if it matches the path part, move up to the parent and get the name. Repeat until at root(id of 0)
                    if potential_path.pid == 0:
                        return (initial_id, path)
                    
                    # Decides if we move on to the next pid
                    if potential_path.file_name == part:
                        potential_path = PathModel.query.filter(PathModel.id == potential_path.pid).first()
                    else:
                        return (-1, "")
    except TypeError as err:
        # print("Something went wrong")
        abort(404, message=f"{err}")

def confirm_pid(id:int = None, session_id:str = None) -> tuple((int, str)):
    try:
        if not session_id and not id:
            raise InsufficientParamaters
        path = construct_path(sessions[session_id]["cwd_id"]) if session_id else construct_path(id)
        return (id, path)
    except InsufficientParamaters as e:
        print(e.message)



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




@blp.route("/utilities/ls")
class ListDirectory(MethodView):
    '''
    grabs all the files from the specified directory. 
    can specify absolute or relative paths.
    can specify pid. 
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
        if "path" in pwd_params.keys():
            id,path = confirm_path(pwd_params["path"], pwd_params["session_id"])
            return {"id": id, "path": path}, 200
        
        # id,path = confirm_pid(pwd_params["session_id"])
        try:
            id,path = confirm_pid()
            return {"id": id, "path": path}, 200
        except TypeError as e:
            print("TypeError: cannot unpack non-iterable NoneType object")
#PWD

#LS

#CD