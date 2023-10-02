from db import db

class GroupModel(db.Model):
    __tablename__ = "group"

    id = db.Column(db.Integer, unique=True, primary_key=True)

    users = db.relationship("UserModel", back_populates="group")