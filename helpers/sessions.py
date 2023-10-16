import requests, random, string
from session_handler import sessions
from datetime import datetime

def session_timer_check():
    """
    background service that runs on a set duration defined in app.py
    """
    req = requests.put("http://127.0.0.1:5000/session")


def rand_string(size=6, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))


def session_id_check(session_id) -> bool:
    '''
    returns true if the session is valid
    returns false if the session is invalid
    '''
    try:
        return session_id in sessions or \
            sessions[session_id]["active"]
    except KeyError:
        return False


def update_session_activity(session_id):
    '''
    update the sessions last known activity. 
    ensure the sessions validity has been checked before using this function
    '''
    sessions[session_id]["last_active"] = datetime.now()

    