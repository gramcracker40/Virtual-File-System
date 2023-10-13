from models.path import PathModel
from session_handler import sessions
import requests, json



# Should add a bool param to check if we should create a new dir/file if it doesn't exist
def confirm_path(path:str, session_id:str) -> (int, str):
    '''
    returns: id of given path
    
    given an absolute or relative path. search for it in the file system. 
    ../../ is back two directories. ../ one, etc...
    
    /users/bench/test        --> absolute path
    cwd: /users,  bench/test --> relative path

    if '-1' is returned, path was not found. 
    0 and up are the pid of the given path
    '''
  
    # root check
    if path == "/":
        return (0, "/")


    path_type = "abs" if path[0] == "/" else "rel"
    path_parts = path.split("/")
    path_parts = [i for i in path_parts if i != ""]

    print(f"PATH PARTS{path_parts}")

    if path_type == "rel":
        cwd_id = sessions[session_id]["cwd_id"]

        # grab the starting point IDs
        if cwd_id != 0:
            curr_dir = PathModel.query.get(cwd_id)
            last_id = curr_dir.id
        else:
            curr_dir, last_id = 0, 0


        for path in path_parts:
            print(f"curr_dir: {curr_dir}, last_id: {last_id}")

            if path == "..": # try to query back one. will error if no more room.
                curr_dir = PathModel.query.filter(PathModel.id == last_id)
                last_id = curr_dir.id
            else: # reset curr_dir
                curr_dir = PathModel.query\
                    .filter(PathModel.pid == last_id, PathModel.file_name == path)
                last_id = curr_dir.id

            print(f"curr_dir: {curr_dir}, last_id: {last_id}")

            if isinstance(curr_dir, None):
                return (-1, "")
            
        return (curr_dir.id, path)

    else: # abs
        pass
       
   

session_data = json.loads(requests.post(f"http://127.0.0.1:5000/session", json={"username": "test", "password": "easy"}).content)

session_id = session_data['session_id']

print(session_data)
path1 = "test/test2/"
path2 = "/test1"
path3 = "../../" # must be two directories in, test while in root as well.

test = confirm_path(path1, session_id)
print(test)
