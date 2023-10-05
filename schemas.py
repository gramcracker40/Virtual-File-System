from marshmallow import Schema, fields, validate, ValidationError

class BytesField(fields.Field):
    def _validate(self, value):
        if not isinstance(value, bytes):
            raise ValidationError('Invalid input type.')

        if value is None or value == b'':
            raise ValidationError('Invalid value')

class UserSchema(Schema):
    username = fields.Str(required=True)
    password = fields.Str(required=True, load_only=True)

class NewGroupSchema(Schema):
    name = fields.Str(required=True)

class NewPathSchema(Schema):
    file_name = fields.Str(required=True)
    file_type = fields.Str(validate=validate.OneOf(["file", "directory"]))
    session_id = fields.Int(required=True)
    contents = BytesField()
    permissions = fields.Str()

class UpdatePathSchema(Schema):
    permissions = fields.Str()
    contents = BytesField()
    file_name = fields.Str()
    pid = fields.Int()

class PathSchema(Schema):
    id = fields.Int()
    file_name = fields.Str()
    file_type = fields.Str()
    file_size = fields.Int()
    modification_time = fields.DateTime()
    contents = BytesField()
    permissions = fields.Str()
    user_id = fields.Int()
    group_id = fields.Int()
    pid = fields.Int()