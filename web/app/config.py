from datetime import timedelta
import os
import pathlib
import psycopg2
import dotenv

dotenv.load_dotenv()

BASE_DIR = pathlib.Path(__file__).resolve().parent.parent

DB_HOST     = os.getenv("DB_HOST", "db")
DB_PORT     = os.getenv("DB_PORT", "5432")
DB_USER     = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")
DB_NAME     = os.getenv("DB_NAME", "docdb")

SECRET_KEY     = os.getenv("SECRET_KEY", "dev-secret")
UPLOAD_FOLDER  = BASE_DIR / "uploads"
UPLOAD_RATE_LIMIT  = "5 per minute"

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