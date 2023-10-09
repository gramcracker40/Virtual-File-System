from models.path import PathModel
from flask_smorest import abort
from session_handler import sessions
from errors import InsufficientParamaters

def construct_path(id:int) -> str:
    path = ""

    # Check if we are already at the root directory
    if id == 0:
        path = "/"
        return path

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

# Should add a bool param to check if we should create a new dir/file if it doesn't exist
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
        original_cwd_id = sessions[session_id]["cwd_id"]
        temp_cwd_id = original_cwd_id

        for potential_path in potential_paths:
            initial_id = potential_path.id
            if path_type == "rel":
                path_parts.reverse()
                for part in path_parts:
                    # TODO: Create exception handling for TypeError when the PathModel returned from a query results in a None type
                    # TODO: Check for when the path has no dir_name at the end, for example: ../
                    if part == dir_name:
                        candidate_path = PathModel.query.filter(PathModel.file_name == dir_name and PathModel.pid == temp_cwd_id).first()
                        # if candidate_path == None:
                            # raise TypeError
                        reconstructed_path = construct_path(candidate_path.id)
                        return (candidate_path.id, reconstructed_path) if candidate_path != None else (-1, "")
                    
                    if part == "..":
                        current_dir = PathModel.query.filter(PathModel.id == temp_cwd_id).first()
                        temp_cwd_id = current_dir.pid
                    else:
                        child_dir = PathModel.query.filter(PathModel.file_name == part and PathModel.pid == temp_cwd_id).first()
                        temp_cwd_id = child_dir.id
                    
            else: 
                # absolute path must end up at root, 
                #  so if you can trace the pid's back to 0 it exists
                # Save the initial file/path id

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

def confirm_path_by_id(id:int = None, session_id:str = None) -> tuple((int, str)):
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