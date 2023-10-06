import requests



def session_timer_check():
    """
    background service that is runs on a set duration in resources/sessions.py
    """
    req = requests.put("http://127.0.0.1:5000/session")


