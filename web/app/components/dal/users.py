from datetime import datetime, timezone


from . import utils

from app.config import LOCKOUT_DURATION, LOCKOUT_THRESHOLD

def get_user_by_id(user_id):
    return utils.query_fetch_one(
        "SELECT id, username, is_disabled FROM users WHERE id = %s",
        (user_id, )
    )

def get_user_by_username(username):  
    return utils.query_fetch_one(
        "SELECT id, username, password, is_disabled, locked_until FROM users WHERE username = %s",
        (username, )
    )

def get_all_users():
    return utils.query_fetch_all(
        "SELECT id, username, is_disabled FROM users ORDER BY id ASC",
    )

def update_user_status(user_id, is_disabled):
    return utils.query_commit(
        "UPDATE users SET is_disabled = %s WHERE id = %s",
        (is_disabled, user_id, )
    )
    
def increment_failed_attempts(username):
    return utils.query_commit(
        """
        UPDATE users
        SET failed_attempts = failed_attempts + 1,
            locked_until = CASE
                WHEN failed_attempts + 1 >= %s THEN %s
                ELSE locked_until
            END
        WHERE username = %s
        """,
        (LOCKOUT_THRESHOLD, datetime.now(timezone.utc) + LOCKOUT_DURATION, username, )
    )

def reset_failed_attempts(username):
    return utils.query_commit(
        """
        UPDATE users SET failed_attempts = 0, locked_until = NULL
        WHERE username = %s
        """,
        (username, )
    )