from db import db
import datetime

class PathModel(db.Model):
    __tablename__ = "path"

    # attributes
    id = db.Column(db.Integer, unique=True, primary_key=True)
    pid = db.Column(db.Integer, nullable=False)
    
    file_name = db.Column(db.String, nullable=False)
    file_type = db.Column(db.String, nullable=False)
    file_size = db.Column(db.Integer, nullable=False)
    
    permissions = db.Column(db.String, nullable=False)
    modification_time = db.Column(db.DateTime, nullable=False)
    contents = db.Column(db.LargeBinary)
    hidden = db.Column(db.Boolean, nullable=False)

    # file and group info
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    group_id = db.Column(db.Integer, db.ForeignKey("group.id"), nullable=False)

"""
obj = {
    "pid": 2,
    "filename": "file.txt",
    "filetype": "txt",
    "filesize": 512,
    "permissions": "-rwxrwxrwx",
    "hidden": True,
    "modification_time": datetime.datetime.now(),
    "user_id": 3,
    "group_id": 1
}

test = PathModel(**obj)
test.contents = open("file.txt", "rb").read()
"""