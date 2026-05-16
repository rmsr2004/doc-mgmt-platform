import psycopg2
import psycopg2.extras
import traceback

from app.config import get_db
from app.shared.result.Result import Error
    
def query_fetch_one(sql: str, params: tuple=()):
    try:
        with get_db() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(sql, params)
                return cur.fetchone()
    except psycopg2.OperationalError:
        traceback.print_exc()
        return Error(message="Internal Error", http_code=500)
    except psycopg2.DatabaseError:
        traceback.print_exc()
        return Error(message="Invalid SQL", http_code=400)

def query_fetch_all(sql: str, params: tuple=()):
    try:
        with get_db() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(sql, params)
                return cur.fetchall()
    except psycopg2.OperationalError:
        traceback.print_exc()
        return Error(message="Internal Error", http_code=500)
    except psycopg2.DatabaseError:
        traceback.print_exc()
        return Error(message="Invalid SQL", http_code=400)

def query_commit(sql: str, params: tuple=()):
    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, params)
                conn.commit()
                return cur.rowcount
    except psycopg2.OperationalError:
        traceback.print_exc()
        return Error(message="Internal Error", http_code=500)
    except psycopg2.DatabaseError:
        traceback.print_exc()
        return Error(message="Invalid SQL", http_code=400)
