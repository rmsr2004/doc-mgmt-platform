from datetime import timedelta
import os
import pathlib
import psycopg2
import dotenv

dotenv.load_dotenv()

BASE_DIR = pathlib.Path(__file__).resolve().parent.parent

def get_required_env(var_name: str) -> str:
    val = os.getenv(var_name)
    if not val:
        raise ValueError(f"Required environment variable '{var_name}' is missing or empty.")
    return val

DB_HOST     = get_required_env("DB_HOST")
DB_PORT     = get_required_env("DB_PORT")
DB_USER     = get_required_env("DB_USER")
DB_PASSWORD = get_required_env("DB_PASSWORD")
DB_NAME     = get_required_env("DB_NAME")

SECRET_KEY     = get_required_env("SECRET_KEY")
UPLOAD_FOLDER  = BASE_DIR / "uploads"
UPLOAD_RATE_LIMIT  = "20 per hour"
LOGIN_RATE_LIMIT   = "10 per minute"

LOCKOUT_THRESHOLD = 5
LOCKOUT_DURATION  = timedelta(minutes=12)

LOCKOUT_THRESHOLD = 5
LOCKOUT_DURATION  = timedelta(minutes=12)

def get_db():
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        dbname=DB_NAME,
    )