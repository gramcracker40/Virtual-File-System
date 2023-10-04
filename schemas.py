from marshmallow import Schema, fields, validate, ValidationError

class BytesField(fields.Field):
    def _validate(self, value):
        if not isinstance(value, bytes):
            raise ValidationError('Invalid input type.')

        if value is None or value == b'':
            raise ValidationError('Invalid value')

class UserLoginSchema(Schema):
    id = fields.Int(dump_only=True)
    username = fields.Str(required=True)
    password = fields.Str(required=True, load_only=True)


class NewPathSchema(Schema):
    pid = fields.Int(required=True)
    file_name = fields.Str(required=True)
    file_type = fields.Str(validate=validate.OneOf(["file", "directory"]))
    contents = fields.BytesField()
    permissions = fields.Str()

#  # attributes
#     id = db.Column(db.Integer, unique=True, primary_key=True)
#     pid = db.Column(db.Integer, nullable=False)
    
#     file_name = db.Column(db.String, nullable=False)
#     file_type = db.Column(db.String, nullable=False)
#     file_size = db.Column(db.Integer, nullable=False)
    
#     permissions = db.Column(db.String, nullable=False)
#     modification_time = db.Column(db.DateTime, nullable=False)
#     contents = db.Column(db.LargeBinary)
#     hidden = db.Column(db.Boolean, nullable=False)

#     # file and group info
#     user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
#     group_id = db.Column(db.Integer, db.ForeignKey("group.id"), nullable=False)
    
