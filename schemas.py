from marshmallow import Schema, fields, validate, ValidationError

class BytesField(fields.Field):
    def _validate(self, value):
        if not isinstance(value, bytes):
            raise ValidationError('Invalid input type.')

        if value is None or value == b'':
            raise ValidationError('Invalid value')
        
class NewSessionSchema(Schema):
    username = fields.Str(required=True)
    password = fields.Str(required=True, load_only=True)

class NewGroupSchema(Schema):
    session_id = fields.Str(required=True)
    name = fields.Str(required=True)

class NewUserSchema(Schema):
    session_id = fields.Str(required=True)
    username = fields.Str(required=True)
    password = fields.Str(required=True, load_only=True)

class GroupSchema(Schema):
    name = fields.Str(required=True)
    users = fields.List(fields.Nested(NewUserSchema()), dump_only=True)

class DeleteGroupSchema(Schema):
    session_id = fields.Str()
    name = fields.Str()

class UserSchema(Schema):
    id = fields.Int()
    username = fields.Str()
    groups = fields.List(fields.Nested(NewGroupSchema()), dump_only=True)

class DeleteUserSchema(Schema):
    session_id = fields.Str(required=True)
    id = fields.Int()
    username = fields.Str()

class UpdateGroupSchema(Schema):
    session_id = fields.Str(required=True)
    group_id = fields.Int()
    group_name = fields.Str()
    user_id = fields.Int()
    username = fields.Str()
    action = fields.Str(validate=validate.OneOf(["add", "remove"]), required=True
                        , description="Must be 'add' or 'remove'")

class NewPathSchema(Schema):
    file_name = fields.Str(required=True)
    file_type = fields.Str(validate=validate.OneOf(["file", "directory"]), required=True)
    session_id = fields.Str(required=True)
    path = fields.Str()
    pid = fields.Int()
    contents = fields.Str()

class UpdatePathSchema(Schema):
    session_id = fields.Str(required=True)
    permissions = fields.Int(description="pass the octal representation, '644'. The server will handle conversion to permission string. ")
    contents = fields.Str()
    file_name = fields.Str()
    path = fields.Str()
    id = fields.Int()
    group_id = fields.Int()
    user_id = fields.Int()
    group_name = fields.Str()
    username = fields.Str()

class DeletePathSchema(Schema):
    path = fields.Str()
    id = fields.Int()
    session_id = fields.Str(required=True)

class GetPathSchema(Schema):
    path = fields.Str()
    id = fields.Int()
    session_id = fields.Str(required=True)

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
    session_id = fields.Str(required=True)
    file_name = fields.Str()
    file_type = fields.Str()
    file_size = fields.Int()
    modification_time = fields.DateTime()

class UtilitySchema(Schema):
    path = fields.Str()
    session_id = fields.Str(required=True)
    
class SessionDeleteSchema(Schema):
    session_id = fields.Str(required=True)

class CopySchema(Schema):
    session_id = fields.Str(required=True)
    copy_path = fields.Str(required=True)
    destination_directory = fields.Str(required=True)


