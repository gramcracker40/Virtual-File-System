'''
Define all utility functions in this file. 

examples: 'change_directory', 'long_listing', etc 

'''
from flask.views import MethodView
from flask_smorest import Blueprint, abort

# internal
from models import PathModel
from schemas import UtilitySchema, PathSchema
from session_handler import sessions
from db import db
from helpers.utilities import confirm_path, change_directory, print_working_directory

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
        change the working directory
        '''
        try:
            new_dir_path = change_directory(path=cd_params["path"], session_id=cd_params["session_id"])
        except KeyError as err:
            abort(400, message="SessionID does not exist...")


        return {"new_path": new_dir_path}, 200


@blp.route("/utilities/ls")
class ListDirectory(MethodView):
    '''
    grabs all the files from the specified directory. 
    can specify absolute or relative paths.
    path must be a valid directory or 404 will be returned. 
    '''

    @blp.response(200, PathSchema(many=True))    
    @blp.arguments(UtilitySchema)
    def get(self, ls_params):
        '''
        get all files in the directory specified.
        no params passed = return sessions 'cwd'.
        can specify absolute path or relative path from
        the sessions 'cwd' using 'path'.
        '''
        try:
            if 'path' not in ls_params.keys():
                cwd_id = sessions[ls_params['session_id']]['cwd_id']
            else:
                cwd_id = confirm_path(ls_params['path'], ls_params['session_id'])[0]
            

            path = PathModel.query.get_or_404(cwd_id) if cwd_id != 0 else 0
            
            if path == 0:
                search_id = 0
            elif path.file_type == "directory":
                search_id = path.id
            elif path.file_type == "file":
                search_id = path.pid

            all_paths = PathModel.query.filter(PathModel.pid == search_id)
            
            paths = [path.__dict__ for path in all_paths]
            for each in paths:
                del each['contents'], each['_sa_instance_state']

            return paths
        except KeyError:
            abort(404, message="SessionID does not exist")


@blp.route("/utilities/pwd")
class PrintWorkingDirectory(MethodView):
    '''
    Gets the current working directory
    '''

    @blp.arguments(UtilitySchema)
    def get(self, pwd_params):
        '''
        '''
        cwd_path = print_working_directory(pwd_params["session_id"]) \
            if pwd_params["session_id"] in sessions \
            else abort(400, message="SessionID is invalid")

        return {"cwd": cwd_path}, 200
    
