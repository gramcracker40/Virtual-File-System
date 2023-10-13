import requests, random, string
from session_handler import sessions

def session_timer_check():
    """
    background service that runs on a set duration defined in app.py
    """
    req = requests.put("http://127.0.0.1:5000/session")


def rand_string(size=6, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))
