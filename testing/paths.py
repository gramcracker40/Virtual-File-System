import requests, json, datetime

url = "http://127.0.0.1:5000"
path_url = f"{url}/path"
session_id = 1

def create_path(url:str, path_data:dict):
    '''
    creates a path in the virtual file system
    '''

    req = requests.post(url, json=path_data)
    req_data = json.loads(req.content)

    print(json.dumps(req_data, indent=2))


test_path_data = {
    "session_id": session_id,
    "file_name": "file.txt",
    "file_type": "file" 
}

new_path = create_path(path_url, test_path_data)