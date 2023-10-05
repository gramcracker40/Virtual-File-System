import requests, json, datetime

url = "http://127.0.0.1:5000"
path_url = f"{url}/path"


def create_path(url:str, path_data:dict):
    '''
    creates a path in the virtual file system
    '''

    req = requests.post(url, json=path_data)
    req_data = json.loads(req.content)

    print(json.dumps(req_data, indent=2))




test_path_data = {
    "pid": 2,
    "file_name": "file.txt",
    "file_type": "file",
    "permissions": "-rwxrwxrwx",
    #"user_id": 3,   add whenever sessions are implemented
    #"group_id": 1
}

new_path = create_path(path_url, test_path_data)