from models.path import PathModel
from flask_smorest import abort
from session_handler import sessions
from errors import InsufficientParamaters

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
        abort(404, message=f"{err}")

def confirm_pid(id:int = None, session_id:str = None) -> tuple((int, str)):
    try:
        if not session_id and not id:
            raise InsufficientParamaters
        path = construct_path(sessions[session_id]["cwd_id"]) if session_id else construct_path(id)
        return (id, path)
    except InsufficientParamaters as e:
        print(e.message)
