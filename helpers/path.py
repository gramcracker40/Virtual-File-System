# implements the permissioning systems for paths. 
from session_handler import sessions
from models import PathModel

permission_map = {
    0: '---', '---': 0,
    1: '--x', '--x': 1,
    2: '-w-', '-w-': 2,
    3: '-wx', '-wx': 3,
    4: 'r--', 'r--': 4,
    5: 'r-x', 'r-x': 5,
    6: 'rw-', 'rw-': 6,
    7: 'rwx', 'rwx': 7
}


def convert_digit(digit):
    if digit < 0 or digit > 7:
        raise ValueError("Invalid digit. Must be between 0 and 7.")

    return permission_map[digit]


def valid_permission_string_check(permission_string) -> bool:
    '''
    given a permission string "-rx-r--r--" return a true/false value
    to determine if the string is valid or not. 
    length of string passed must be 10
    '''
    if len(permission_string) != 10:
        return False
    else:
        path_type = permission_string[0]
        user = permission_string[1:4]
        group = permission_string[4:7]
        others = permission_string[7:10]

        if (user in permission_map
            and group in permission_map
            and others in permission_map
            and (path_type == 'd' or path_type == '-')
            ):
            return True
        else:
            return False


def valid_permission_octal_check(triple):
    return triple >= 0 and triple <= 777


def octal_to_permission_string(triple):
    if triple < 0 or triple > 777:
        raise ValueError(
            "Invalid permission triple. Must be between 0 and 777.")

    # Convert each digit of the triple to its 'rwx' equivalent
    owner = convert_digit(triple // 100)
    group = convert_digit((triple // 10) % 10)
    others = convert_digit(triple % 10)

    return owner + group + others


def permission_string_to_octal(permission_string: str):
    '''
    takes in a permission string and converts to a integer representation in base 8. 
    '''
    return int(permission_map[permission_string[1:4]]) * 100 \
        + int(permission_map[permission_string[4:7]]) * 10 \
        + int(permission_map[permission_string[7:10]])


def permissions_check(session_id: str, path: PathModel, permission_needed: str = "r") -> bool:
    '''
    pass a permission_needed char. if a function require read, pass "r" write: "w" execute "x" 

    permissions will be checked for all functionality. this function handles it

    PARAMETERS:
        session_id:        the calling sessions id, used to check the currently logged in 
                                user and the groups they belong to. 
        permission_needed: a char of the required permissions for that function. 
    '''

    # grab session details.
    session_user_id = sessions[session_id]["user_id"]
    session_groups = sessions[session_id]["groups"]

    # admin check - they can do whatever they want really
    if 2 in session_groups:
        return True

    # root check - nobody beside admins have access to root.
    if path == 0:
        return False

    # parse the permissions from stored permission string
    user_perm, group_perm, others_perm = \
        path.permissions[1:4], path.permissions[4:7], path.permissions[7:10]

    # checks to ensure the session has permissions
    if ((permission_needed in user_perm and session_user_id == path.user_id)
                or (permission_needed in group_perm and path.group_id in session_groups)
                or permission_needed in others_perm
            ):
        pass
    else:
        return False

    return True


def owner_check(session_id: str, path: PathModel):
    return True if sessions[session_id]["user_id"]\
        == path.user_id else False