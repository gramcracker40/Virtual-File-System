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


def convert_permission(triple):
    if triple < 0 or triple > 777:
        raise ValueError("Invalid permission triple. Must be between 0 and 777.")

    # Convert each digit of the triple to its 'rwx' equivalent
    owner = convert_digit(triple // 100)
    group = convert_digit((triple // 10) % 10)
    others = convert_digit(triple % 10)

    return owner + group + others


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


# Example usage:
permission_triple = 125
permission_rwx = convert_permission(permission_triple)
permission_rwx_full = f"d{permission_rwx}" if valid_permissions_check(f"d{permission_rwx}") else -1

permission_string = "-rw-r--r--"
permission_octal_result = valid_permissions_check(permission_string)

print(permission_rwx)
print(permission_rwx_full)  # Output: 'rw-r--r--'
print(permission_octal_result)


# needs for resources
    #POST: need a check for the permissions of the sessions 
            # logged in user to see if they are valid in the desired pid
    #GET: need a check for session_id
    #PATCH: update a path's attributes
    #DELETE: need to implement a check to see the right of the user over that file or directory (path). If they
            # do not have rights they cannot delete the file or directory (path)