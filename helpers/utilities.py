from models.path import PathModel
from flask_smorest import abort
from session_handler import sessions
from db import db
from helpers.permission_system import permissions_check
from datetime import datetime

def construct_path(id:int) -> str:
    path = ""

    # Check if we are already at the root directory
    if id == 0:
        return "/"
         
    # Starting point of the path based on the id
    temp_id = id

    # Iterate over every parent directory and add the name to the path
    while temp_id != 0:
        current_dir = PathModel.query.filter(PathModel.id == temp_id).first()
        path = f"{current_dir.file_name}/" + path
        temp_id = current_dir.pid
    
    path = "/" + path
    path = path[0:-1]

    return path

    
def confirm_path(path:str, session_id:str) -> (int, str):
    '''
    returns:
        id: int --> returns the id of the given path that is to be confirmed
        path: str --> full path to the newly confirmed path. 
    
    given an absolute or relative path. search for it in the file system. 
    
    .. can only be used in relative paths

    ../../ is back two directories. ../ one, etc...
    
    /users/bench/test        --> absolute path
    cwd: /users,  bench/test --> relative path

    if '-1' is returned, path was not found. 

    relative paths uses the passed session id to search for their 'cwd'
      in the system. And is able to handle the '..' pretty much infinitely.
      
      example: cwd: "/" ,  users/bench/test/../../bench/test/../ will
            end up in users/bench/test

    absolute paths must be perfectly structured paths in the system. 

    '/users/bench/test' will work fine
    '''
    # initial parsing of path
    if path == "":
        return (-1, "invalid")

    path_type = "abs" if path[0] == "/" else "rel"
    path_parts = path.split("/")
    path_parts = [i for i in path_parts if i != ""]

    if path_type == "rel":
        cwd_id = sessions[session_id]["cwd_id"]

        if cwd_id != 0:
            curr_dir = PathModel.query.get(cwd_id)
            last_id = curr_dir.id
            last_pid = curr_dir.pid
        else:
            curr_dir, last_id, last_pid = 0, 0, 0

        for path_ in path_parts:
            if path_ == "..":
                if last_pid != 0 and last_pid != -1:
                    curr_dir = PathModel.query.filter(PathModel.id == last_pid).first()
                    last_id = curr_dir.id
                    last_pid = curr_dir.pid
                else:
                    last_pid = -1
                    last_id = 0
                
            else:
                curr_dir = PathModel.query\
                    .filter(PathModel.pid == last_id, PathModel.file_name == path_).first()

                if curr_dir != None:
                    last_pid = curr_dir.pid
                    last_id = curr_dir.id
                
            if curr_dir == None: # only runs if query finds no matching path. 
                return (-1, "invalid")
        
        if last_id == 0:
            return (0, "/")

        return (curr_dir.id, construct_path(curr_dir.id))

    else: # abs
        last_id = 0
        for path_ in path_parts:
            temp = PathModel.query\
                .filter(PathModel.file_name == path_, 
                        PathModel.pid == last_id).first()
            
            if temp == None:
                return (-1, "invalid")

            last_id = temp.id

        return (last_id, construct_path(last_id))


def change_directory(path:str = None, session_id:str = None) -> str:
    id,path = confirm_path(path, session_id)
    
    if id == -1:
        return "Directory does not exist."
        
    model = PathModel.query.filter(PathModel.id == id).first_or_404(description="Path not found") \
        if id != 0 else 0

    if model == 0:
        if 2 in sessions[session_id]["groups"]: # only admin can be inside of root.
            sessions[session_id]["cwd_id"] = id 
            return f"/"
        else:
            return f"Non admin users can not change into root."
    elif model.file_type == "file":
        return model.file_name +  " is not a directory..."

    if not permissions_check(session_id, model, permission_needed="x"):
        return f"the logged in session does not have the necessary rights to change into this directory"

    sessions[session_id]["cwd_id"] = id
    return construct_path(id)

def print_working_directory(session_id:str = None) -> str:
    cwd_id = sessions[session_id]["cwd_id"]
    path = construct_path(cwd_id)
    return path


def copy_directory_structure(copy_directory:PathModel, dir_counter:int, dir_structure:dict):
    '''
    recursively copy the sub-structure of the directory being copied
    '''
    for path in PathModel.query.filter(PathModel.pid == copy_directory.id).all():
        dir_counter += 1
        if path.file_type == "file":
            dir_structure[dir_counter] = path
        else:
            dir_structure[dir_counter] = {
                "directory": path,
                "sub_directories": copy_directory_structure(path, path.pid, dir_structure)
            }
    print(f"dir_structure: {dir_structure}")
 
    return dir_structure

def commit_copied_structure(dir_structure:dict, dest_pid:int):
    '''
    recursively commit the copied structure and rebuild the exact same structure on the destination path
    '''
    # dir structure fully replicated.

    for dir_num in dir_structure['sub_directories']:
        if type(dir_structure['sub_directories'][dir_num]) == PathModel:
            temp = PathModel(
                    pid=dest_pid, # change the pid of the newly create path to the destination path
                    file_name=dir_structure['sub_directories'][dir_num].file_name,
                    file_type=dir_structure['sub_directories'][dir_num].file_type,
                    file_size=dir_structure['sub_directories'][dir_num].file_size,
                    permissions=dir_structure['sub_directories'][dir_num].permissions,
                    modification_time=datetime.now(),
                    contents=dir_structure['sub_directories'][dir_num].contents,
                    hidden=dir_structure['sub_directories'][dir_num].hidden,
                    user_id=dir_structure['sub_directories'][dir_num].user_id,
                    group_id=dir_structure['sub_directories'][dir_num].group_id,
                )
            db.session.add(temp)
            db.session.commit()
        
        else: # subdirectories

            temp = PathModel(
                    pid=dest_pid, # change the pid of the newly create path to the destination path
                    file_name=dir_structure['sub_directories'][dir_num]['directory'].file_name,
                    file_type=dir_structure['sub_directories'][dir_num]['directory'].file_type,
                    file_size=dir_structure['sub_directories'][dir_num]['directory'].file_size,
                    permissions=dir_structure['sub_directories'][dir_num]['directory'].permissions,
                    modification_time=datetime.now(),
                    contents=dir_structure['sub_directories'][dir_num]['directory'].contents,
                    hidden=dir_structure['sub_directories'][dir_num]['directory'].hidden,
                    user_id=dir_structure['sub_directories'][dir_num]['directory'].user_id,
                    group_id=dir_structure['sub_directories'][dir_num]['directory'].group_id,
                )
            db.session.add(temp)
            db.session.commit()

            commit_copied_structure(dir_structure['sub_directories'][dir_num], temp.id)

    return dest_pid