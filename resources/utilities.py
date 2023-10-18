'''
UTILITY METHODS for shell sessions with the file system. 
'change_directory', 'long_listing', 'print_working_directory', etc.

'''
from flask.views import MethodView
from flask_smorest import Blueprint, abort
from datetime import datetime
from pprint import pprint

# internal
from models import PathModel, UserModel
from schemas import UtilitySchema, PathSchema, UserSchema, CopySchema
from session_handler import sessions
from db import db
from helpers.utilities import confirm_path, change_directory, commit_copied_structure,\
        print_working_directory, copy_directory_structure
from helpers.sessions import update_session_activity, session_id_check
from helpers.permission_system import permissions_check

blp = Blueprint("utilities", "utilities", description="Implementing functionality for utilities")

@blp.route("/utilities/cd")
class ChangeDirectory(MethodView):

    @blp.arguments(UtilitySchema)
    def post(self, cd_params):
        '''
        change the 'cwd' of the passed session_id. 
        can specify absolute or relative path. 
        see, CDschema for further clarity.  

        only admins can enter root. in fact, default users have no rights to anything in 
        anybody elses section that is built for them whenever they are created as a user by an admin. 
        '''
        try:
            if not session_id_check(cd_params["session_id"]):
                abort(409, message="Session ID provided does not exist or is not active, login again...")

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
            if not session_id_check(ls_params["session_id"]):
                abort(409, message="Session ID provided does not exist or is not active, login again...")

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
        if not session_id_check(pwd_params["session_id"]):
            abort(409, message="Session ID provided does not exist or is not active, login again...")


        cwd_path = print_working_directory(pwd_params["session_id"]) \
            if pwd_params["session_id"] in sessions \
            else abort(400, message="SessionID is invalid")
        
        update_session_activity(pwd_params['session_id'])

        return {"cwd": cwd_path}, 200


@blp.route("/utilities/sort")
class SortedPathContents(MethodView):
    '''
    returns the sorted contents of the path specified. 
    can only specify a valid file in the file system.
    '''
    @blp.arguments(UtilitySchema)
    def get(self, sort_params):
        '''
        Get a files sorted content by passing the path 
        '''

        if not session_id_check(sort_params["session_id"]):
            abort(409, message="Session ID provided does not exist or is not active, login again...")

        if "path" in sort_params.keys():
            id = confirm_path(sort_params['path'], sort_params['session_id'])[0]
            if id == -1:
                abort(400, message="specified path was not found.")
        else:
            abort(400, message="please pass a valid 'path'. can be absolute or relative.")

        if id != 0:
            file = PathModel.query.get_or_404(id, description="id returned from confirm path not valid")
        else:
            abort(400, message="can not specify root to sort")
        
        if file.file_type != "file": 
            abort(400, "directories have no contents. sort a file.")

        return sorted(file.contents.decode().split("\n")), 200


@blp.route("/utilities/whoami")
class WhoAmI(MethodView):
    '''
    return logged in user information about the calling session
    '''
    @blp.arguments(UtilitySchema)
    @blp.response(200, UserSchema)
    def get(self, sort_params):
        '''
        Get a files sorted content by passing the path 
        '''
        if not session_id_check(sort_params["session_id"]):
            abort(409, message="Session ID provided does not exist or is not active, login again...")

        return UserModel.query.get_or_404(sessions[sort_params['session_id']]['user_id'])

@blp.route("/utilities/copy")
class CopyPathToDir(MethodView):
    '''
    copies a path into an existing directory. 
    '''
    @blp.arguments(CopySchema)
    def post(self, copy_data):
        '''
        copy an existing directory or file, into an existing directory. 
        '''

        copy_id, copy_path_str = confirm_path(copy_data["copy_path"], copy_data["session_id"])
        dest_id, dest_dir_str = confirm_path(copy_data["destination_directory"], copy_data["session_id"])

        if copy_id == -1:
            abort(400, message="'copy_path' was not found")

        if dest_id == -1:
            abort(400, message="'destination_directory' was not found")

        if copy_id == 0:
            abort(400, message="can not copy root. '/' error")

        copy_path = PathModel.query.get_or_404(copy_id, description="could not find copy_id")
        dest_dir = PathModel.query.get_or_404(dest_id, description="could not find dest_id")\
            if dest_id != 0 else 0
        
        if dest_dir != 0 and dest_dir.file_type == "file": # short circuit
            abort(400, f"The 'destination_directory' must be a directory Path. can not be a file")

        # create the copied Path and commit it to the database at the destination
        copied_path = PathModel(
            pid=dest_dir if type(dest_dir) == int else dest_dir.id, # change the pid of the newly create path to the destination path
            file_name=copy_path.file_name,
            file_type=copy_path.file_type,
            file_size=copy_path.file_size,
            permissions=copy_path.permissions,
            modification_time=datetime.now(),
            contents=copy_path.contents,
            hidden=copy_path.hidden,
            user_id=copy_path.user_id,
            group_id=copy_path.group_id,
        )

        # same name check
        paths_in_dir = PathModel.query.filter(PathModel.pid == copied_path.pid) \
            if copied_path.file_type == "file" else\
            PathModel.query.filter(PathModel.pid == copied_path.id)
        for each in paths_in_dir:
            if each.file_name == copied_path.file_name:
                abort(
                    409,
                    message=f"Path with name - {copied_path.file_name} already exists in this directory",
                )

        db.session.add(copied_path)
        db.session.commit()

        # if the path is a directory, go and get its children Paths and copy them too to be moved 
        if copy_path.file_type == "directory":

            # run recursive helper function to build the original copy_directory structure.
            dir_counter = 0
            dir_structure = {}
            
            dir_structure_complete = {
                "directory": copied_path,
                "sub_directories": copy_directory_structure(copy_path, dir_counter, dir_structure)
            }
            
            # run recursive function to commit the copied structure at the destination directory. 
            commit_copied_structure(dir_structure_complete, dest_id)
            
        return {"Success" : True}, 201


            


            

