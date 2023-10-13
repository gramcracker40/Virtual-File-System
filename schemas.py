from marshmallow import Schema, fields, validate, ValidationError

class BytesField(fields.Field):
    def _validate(self, value):
        if not isinstance(value, bytes):
            raise ValidationError('Invalid input type.')

        if value is None or value == b'':
            raise ValidationError('Invalid value')

class NewGroupSchema(Schema):
    name = fields.Str(required=True)

class NewUserSchema(Schema):
    username = fields.Str(required=True)
    password = fields.Str(required=True, load_only=True)

class GroupSchema(Schema):
    name = fields.Str(required=True)
    users = fields.List(fields.Nested(NewUserSchema()), dump_only=True)

class DeleteGroupSchema(Schema):
    session_id = fields.Str()
    name = fields.Str()
    id = fields.Int()

class UserSchema(Schema):
    id = fields.Int()
    username = fields.Str()
    groups = fields.List(fields.Nested(NewGroupSchema()), dump_only=True)

class DeleteUserSchema(Schema):
    session_id = fields.Str(required=True)
    id = fields.Int()
    username = fields.Str()

class UpdateGroupSchema(Schema):
    group_id = fields.Int()
    group_name = fields.Str()
    user_id = fields.Int()
    username = fields.Str()
    action = fields.Str(validate=validate.OneOf(["add", "remove"]), required=True)


class NewPathSchema(Schema):
    file_name = fields.Str(required=True)
    file_type = fields.Str(validate=validate.OneOf(["file", "directory"]), required=True)
    session_id = fields.Str(required=True)
    path = fields.Str()
    pid = fields.Int()
    contents = fields.Str()

class UpdatePathSchema(Schema):
    session_id = fields.Str(required=True)
    permissions = fields.Str()
    contents = fields.Str()
    file_name = fields.Str()
    path = fields.Str(required=True)
    group_id = fields.Int()

class UpdatePathIDSchema(Schema):
    session_id = fields.Str(required=True)
    permissions = fields.Str()
    contents = fields.Str()
    file_name = fields.Str()
    pid = fields.Int()
    group_id = fields.Int()

class PathSchema(Schema):
    id = fields.Int()
    file_name = fields.Str()
    file_type = fields.Str()
    file_size = fields.Int()
    modification_time = fields.DateTime()
    contents = fields.Str()
    permissions = fields.Str()
    user_id = fields.Int()
    group_id = fields.Int()
    pid = fields.Int()

class PathFilterSchema(Schema):
    file_name = fields.Str()
    file_type = fields.Str()
    file_size = fields.Int()
    modification_time = fields.DateTime()

class UtilitySchema(Schema):
    path = fields.Str()
    session_id = fields.Str(required=True)
    
class SessionDeleteSchema(Schema):
    session_id = fields.Str(required=True)
