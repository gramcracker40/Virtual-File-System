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
        if path == "/":
            return (0, "/")


        path_type = "abs" if path[0] == "/" else "rel"
        path_parts = path.split("/")
        path_parts = [i for i in path_parts if i != ""]
        dir_name = path_parts[-1]
        print(dir_name)
        path_parts.reverse()
        original_cwd_id = sessions[session_id]["cwd_id"]
        temp_cwd_id = original_cwd_id
        path_ids = {}
        
        if dir_name != "..":
            print("dir_name != '..'")
            potential_paths = PathModel.query.filter(PathModel.file_name == dir_name)
        

            for potential_path in potential_paths:
                if potential_path.file_type != "directory":
                    continue
                initial_id = potential_path.id
                if path_type == "rel":
                    path_parts.reverse()
                    for part in path_parts:
                        # TODO: Create exception handling for TypeError when the PathModel returned from a query results in a None type
                        # TODO: Check for when the path has no dir_name at the end, for example: ../
                        # TODO: Fix the issue with skipping the path and going straight to an existing directory we aren't connected to
                        if part == dir_name: # Check for NoneType before returning 
                            candidate_path = PathModel.query.filter(PathModel.file_name == dir_name and PathModel.pid == temp_cwd_id).first()
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
            return (-1, "")
        if dir_name == "..":
            print("dir_name == '..'")
            if path_type == "rel":
                for part in path_parts:
                    if part == "..":
                        current_dir = PathModel.query.filter(PathModel.id == temp_cwd_id).first()
                        if current_dir != None:
                            print(current_dir.id)
                            print(current_dir.pid)
                            # if current_dir.pid != 0:
                            temp_cwd_id = current_dir.pid
                    else:
                        child_dir = PathModel.query.filter(PathModel.file_name == part and PathModel.pid == temp_cwd_id).first()
                        if child_dir != None:
                            temp_cwd_id = child_dir.id
                if temp_cwd_id < 0:
                    return (-1, "")
                if temp_cwd_id == 0:
                    reconstructed_path = construct_path(0)
                    return (0, reconstructed_path)
                candidate_path = PathModel.query.filter(PathModel.id == temp_cwd_id).first()
                reconstructed_path = construct_path(candidate_path.id)
                return (candidate_path.id, reconstructed_path) if candidate_path != None else (-1, "")

            # candidate_path = PathModel.query.filter(PathModel.id == temp_cwd_id).first()
            # reconstructed_path = construct_path(candidate_path.id)
            # print(candidate_path)
            # print(reconstructed_path)
            # return (candidate_path.id, reconstructed_path) if candidate_path != None else (-1, "")
    except TypeError as err:
        abort(404, message=f"{err}")

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