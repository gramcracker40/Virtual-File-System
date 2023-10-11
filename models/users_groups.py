from db import db
from sqlalchemy import UniqueConstraint

class UsersGroupsModel(db.Model):
    __tablename__ = "users_groups"
    
    id = db.Column(db.Integer, unique=True, primary_key=True)
    
    group_id = db.Column(db.Integer, db.ForeignKey("group.id"), nullable=False)
    user_id =  db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    
    __table_args__ = (UniqueConstraint('group_id', 'user_id', name='_group_user_uc'),)
