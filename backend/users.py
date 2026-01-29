import json
import os
from datetime import datetime
import secrets

USERS_FILE = "users.json"

def load_users():
    """Load users from JSON file"""
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_users(users):
    """Save users to JSON file"""
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f, indent=2)

def create_or_get_user(username: str):
    """
    Create a new user or get existing user
    Returns: (user_id, token, is_new)
    """
    users = load_users()
    
    # Normalize username
    user_id = username.lower().strip().replace(" ", "_")
    
    # Check if user exists
    if user_id in users:
        return user_id, users[user_id]["token"], False
    
    # Create new user
    token = secrets.token_urlsafe(32)
    users[user_id] = {
        "username": username,
        "token": token,
        "created_at": datetime.now().isoformat()
    }
    
    save_users(users)
    return user_id, token, True

def verify_token(token: str):
    """
    Verify token and return user_id
    Returns: user_id or None
    """
    users = load_users()
    
    for user_id, user_data in users.items():
        if user_data["token"] == token:
            return user_id
    
    return None