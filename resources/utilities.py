'''
UTILITY METHODS for shell sessions with the file system. 
'change_directory', 'long_listing', 'print_working_directory', etc.

'''
from flask.views import MethodView
from flask_smorest import Blueprint, abort

# internal
from models import PathModel
from schemas import UtilitySchema, PathSchema
from session_handler import sessions
from db import db
from helpers.utilities import confirm_path, change_directory, print_working_directory
from helpers.sessions import update_session_activity
from helpers.permission_system import permissions_check

blp = Blueprint("utilities", "utilities", description="Implementing functionality for utilities")

@blp.route("/utilities/cd")
class ChangeDirectory(MethodView):
    '''
    change the 'cwd' of the passed session_id. 
    can specify absolute or relative path. 
    see, CDschema for further clarity.  

    only admins can enter root. in fact, default users have no rights to anything in 
    anybody elses section that is built for them whenever they are created as a user by an admin. 

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

        update_session_activity(cd_params['session_id'])

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
                abort(400, message="Can not list the files associated with a file. Please specify a directory")

            if not permissions_check(ls_params['session_id'], path, permission_needed="r"):
                abort(400, message="the session user does not have read permissions on the desired directory ")

            all_paths = PathModel.query.filter(PathModel.pid == search_id)
            
            paths = [path.__dict__ for path in all_paths]
            for each in paths:
                del each['contents'], each['_sa_instance_state']

            update_session_activity(ls_params['session_id'])

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
        
        update_session_activity(pwd_params['session_id'])

        return {"cwd": cwd_path}, 200
