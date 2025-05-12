import psycopg2
from zoho_sync.config import Config

def get_connection():
    conn = psycopg2.connect(
        host=Config.PG_HOST,
        database=Config.PG_DATABASE,
        user=Config.PG_USER,
        password=Config.PG_PASSWORD,
        port=Config.PG_PORT,
        sslmode=Config.PG_SSLMODE
    )
    return conn

