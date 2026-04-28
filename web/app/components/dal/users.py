from . import utils

def get_user_by_id(user_id):
    return utils.query_fetch_one(
        "SELECT id, username, is_disabled FROM users WHERE id = %s",
        (user_id, )
    )

def get_user_by_username(username):  
    return utils.query_fetch_one(
        "SELECT id, username, password, is_disabled FROM users WHERE username = %s",
        (username, )
    )

def get_all_users():
    return utils.query_fetch_all(
        "SELECT id, username, is_disabled FROM users ORDER BY id ASC",
    )

def update_user_status(user_id):
    return utils.query_commit(
        "UPDATE users SET is_disabled = NOT is_disabled WHERE id = %s",
        (user_id, )
    )