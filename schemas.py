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
    pid = fields.Int(required=True)
    file_name = fields.Str(required=True)
    file_type = fields.Str(validate=validate.OneOf(["file", "directory"]))
    contents = BytesField()
    permissions = fields.Str()

