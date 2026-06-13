import time
import json
import os

SESSION_FILE = "data/sessions.json"

def _load_sessions():
    if not os.path.exists("data"):
        os.makedirs("data")
    if os.path.exists(SESSION_FILE):
        try:
            with open(SESSION_FILE, "r") as f:
                return json.load(f)
        except:
            return {}
    return {}

def _save_sessions(sessions):
    if not os.path.exists("data"):
        os.makedirs("data")
    try:
        with open(SESSION_FILE, "w") as f:
            json.dump(sessions, f)
    except:
        pass

# Session TTL in seconds (e.g. 1 hour)
SESSION_TTL = 3600

def get_session(session_id):
    """
    Retrieves session data by ID. Automatically cleans up expired sessions.
    """
    sessions = _load_sessions()
    now = time.time()
    
    # Clean up expired sessions periodically
    expired = [sid for sid, data in sessions.items() if now - data.get('_updated_at', 0) > SESSION_TTL]
    for sid in expired:
        sessions.pop(sid, None)
        
    if expired:
        _save_sessions(sessions)
        
    if session_id in sessions:
        session_data = sessions[session_id]
        session_data['_updated_at'] = now
        _save_sessions(sessions)
        return session_data
        
    # Initialize new session
    new_session = {
        'id': session_id,
        'step': 'start',
        'lang': 'en',
        '_created_at': now,
        '_updated_at': now
    }
    sessions[session_id] = new_session
    _save_sessions(sessions)
    return new_session

def save_session(session_id, session_data):
    """
    Saves session data.
    """
    sessions = _load_sessions()
    session_data['_updated_at'] = time.time()
    sessions[session_id] = session_data
    _save_sessions(sessions)

def clear_session(session_id):
    """
    Clears session data.
    """
    sessions = _load_sessions()
    if session_id in sessions:
        sessions.pop(session_id, None)
        _save_sessions(sessions)
