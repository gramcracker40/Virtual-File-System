###
# creates the root admin user on file system creation. 
# creates the default group to throw each user in
###
from models import UserModel, GroupModel, PathModel
from dotenv import dotenv_values
from passlib.hash import pbkdf2_sha256
from db import db
from datetime import datetime

config = dotenv_values(".flaskenv")
self_url = "http://127.0.0.1:5000"


def build_initial_structure():
    '''
    creates all default layouts and entry points for file system.
    uses the ROOT_PASS environment variable in .flaskenv to set the 
        root users password. this is the only user who has access to root. 
    '''
    root_user = UserModel(username="root", 
        password=pbkdf2_sha256.hash(config["ROOT_PASS"]))
    default_group = GroupModel(name="default")
    admin_group = GroupModel(name="admin")
    
    db.session.add(root_user)
    db.session.add(default_group)
    db.session.add(admin_group)
    db.session.commit()
    
    users_folder = PathModel(
        file_name="users",
        file_type="directory",
        permissions="drwx------", 
        user_id=1, 
        group_id=1, 
        file_size=0, 
        modification_time=datetime.now(), 
        pid=0, 
        hidden=False
    )

    db.session.add(users_folder)
    admin_group.users.append(root_user)
    db.session.commit()



