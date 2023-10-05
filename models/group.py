from db import db

class GroupModel(db.Model):
    __tablename__ = "group"
    id = db.Column(db.Integer, unique=True, primary_key=True)
    name = db.Column(db.String, unique=True, nullable=False)
    
    users = db.relationship("UserModel", back_populates="group")
