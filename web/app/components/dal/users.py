from collections import namedtuple

from . import utils
from app.config import get_db

UserRow = namedtuple("UserRow", ["id", "username", "is_disabled"])

def get_user_by_username(username):
    conn = get_db()
    cur = conn.cursor()
    query = utils.prepare_query("SELECT id, username, password, is_disabled FROM users WHERE username='%s'", username)
    cur.execute(query)
    conn.commit()
    return cur.fetchone()

def get_all_users():
    conn = get_db()
    cur = conn.cursor()
    
    query = """
        SELECT id, username, is_disabled
        FROM users
        ORDER BY id ASC
    """
    cur.execute(query)
    rows = cur.fetchall()
    conn.commit()
    return [UserRow(r[0], r[1], r[2]) for r in rows]

def update_user_status(user_id):
    conn = get_db()
    cur = conn.cursor()
    
    query = """
        UPDATE users
        SET is_disabled = NOT is_disabled
        WHERE id = %s
    """
    cur.execute(query, (user_id,))
    conn.commit()
    return