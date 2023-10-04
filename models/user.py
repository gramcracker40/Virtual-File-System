from db import db

class UserModel(db.Model):
    __tablename__ = "user"

    id = db.Column(db.Integer, unique=True, primary_key=True)

    username = db.Column(db.String, unique=True, nullable=False)
    password = db.Column(db.String, nullable=False)

    group_id = db.Column(db.Integer, db.ForeignKey("group.id"), nullable=False)
    group = db.relationship("GroupModel", back_populates="users")