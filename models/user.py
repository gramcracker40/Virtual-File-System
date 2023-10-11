from db import db

class UserModel(db.Model):
    __tablename__ = "user"

    id = db.Column(db.Integer, unique=True, primary_key=True)

    username = db.Column(db.String, unique=True, nullable=False)
    password = db.Column(db.String, nullable=False)

    groups = db.relationship("GroupModel", secondary="users_groups", back_populates="users")
