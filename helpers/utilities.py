from models.path import PathModel
from flask_smorest import abort
from session_handler import sessions
from errors import InsufficientParamaters
import requests, json

def construct_path(id:int) -> str:
    path = ""

    # Check if we are already at the root directory
    if id == 0:
        return "/"
         

    # Starting point of the path based on the id
    # path_itr = PathModel.query.filter(PathModel.id == id).first()
    # pid = path_itr.pid
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
                elif last_pid == 0 or last_pid == -1:
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


def confirm_path_by_id(id:int = None, session_id:str = None) -> (int, str):
    try:
        if not session_id and not id:
            raise InsufficientParamaters
        path = construct_path(sessions[session_id]["cwd_id"]) if session_id else construct_path(id)
        return (id, path)
    except InsufficientParamaters as e:
        print(e.message)


def change_directory(path:str = None, session_id:str = None) -> str:
    id,path = confirm_path(path, session_id)

    if id == -1:
        return "Directory does not exist."
    
    sessions[session_id]["cwd_id"] = id
    new_dir_path = construct_path(id)
    return new_dir_path

def print_working_directory(session_id:str = None) -> str:
    cwd_id = sessions[session_id]["cwd_id"]
    path = construct_path(cwd_id)
    return path