from session_handler import sessions
from models import PathModel

# helper file for paths
permission_map = {
    0: '---',
    1: '--x',
    2: '-w-',
    3: '-wx',
    4: 'r--',
    5: 'r-x',
    6: 'rw-',
    7: 'rwx',
    '---': 0,
    '--x': 1,
    '-w-': 2,
    '-wx': 3,
    'r--': 4,
    'r-x': 5,
    'rw-': 6,
    'rwx': 7
}

def convert_digit(digit):
    if digit < 0 or digit > 7:
        raise ValueError("Invalid digit. Must be between 0 and 7.")

    return permission_map[digit]


def valid_permissions_check(permission_string) -> bool:
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


def octal_to_permission_string(triple):
    if triple < 0 or triple > 777:
        raise ValueError("Invalid permission triple. Must be between 0 and 777.")

    # Convert each digit of the triple to its 'rwx' equivalent
    owner = convert_digit(triple // 100)
    group = convert_digit((triple // 10) % 10)
    others = convert_digit(triple % 10)

    return owner + group + others


def permission_string_to_octal(permission_string:str):
    '''
    takes in a permission string and converts to a integer representation in base 8. 
    '''
    return int(permission_map[permission_string[1:4]]) * 100 \
            + int(permission_map[permission_string[4:7]]) * 10 \
            + int(permission_map[permission_string[7:10]])


def permissions_check(session_id:str,
                      path:PathModel, permission_needed:str="r") -> bool:
    '''
    pass a permission_needed str matching up to a 'rwx' requirement.
    example: rx, would be 'r-x'. so the permission the function will check for
    in the calling sessions details against the paths group and user is read and execute. 

    permissions will be checked for all functionality. this function handles it

    functionality differs between directories and files. see permission_notes.md for more info

    PARAMETERS:
        path_user_id:      the user id that the path belongs to 
        path_group_id:     the group id that the path belongs to
        session_id:        the calling sessions id, used to check the currently logged in 
                                user and the groups they belong to. 
        path_type:         either "file" or "directory" to see which permission to check on
        permission_needed: a number 1-7 to see the necessary permissions required to perform
                                the calling action
    '''

    session_user_id = sessions[session_id]["user_id"]
    session_groups = sessions[session_id]["groups"]

    user, group, others = path.permissions[1:4], path.permissions[4:7], path.permissions[7:10]

    permission_chars = (x for x in permission_needed)

    for permission in permission_chars:
        if (permission in user 
            or permission in group 
            or permission in others
        ):
            pass
        else:
            return False
        
    return True











# Example usage:
permission_triple = 125
permission_rwx = octal_to_permission_string(permission_triple)
permission_rwx_full = f"d{permission_rwx}" if valid_permissions_check(f"d{permission_rwx}") else -1

permission_string = "-rw-r--r--"
permission_octal_result = permission_string_to_octal(permission_string)
permission_valid = valid_permissions_check(permission_string)

test = octal_to_permission_string(permission_octal_result)



print(permission_rwx)
print(permission_rwx_full)  # Output: 'rw-r--r--'
print(permission_octal_result)
print(test)


# needs for resources 
    #POST: need a check for the permissions of the sessions 
            # logged in user to see if they are valid in the desired pid
    #GET: need a check for session_id
    #PATCH: update a path's attributes
    #DELETE: need to implement a check to see the right of the user over that file or directory (path). If they
            # do not have rights they cannot delete the file or directory (path)

