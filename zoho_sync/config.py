from dotenv import load_dotenv
import os

load_dotenv()

class Config:
    PG_HOST = os.getenv("PG_HOST")
    PG_DATABASE = os.getenv("PG_DATABASE")
    PG_USER = os.getenv("PG_USER")
    PG_PASSWORD = os.getenv("PG_PASSWORD")
    PG_PORT = os.getenv("PG_PORT")
    PG_SSLMODE = os.getenv("PG_SSLMODE", "disable")

    ZOHO_CLIENT_ID = os.getenv("ZOHO_CLIENT_ID")
    ZOHO_CLIENT_SECRET = os.getenv("ZOHO_CLIENT_SECRET")
    ZOHO_REFRESH_TOKEN = os.getenv("ZOHO_REFRESH_TOKEN")
    ZOHO_BASE_URL = os.getenv("ZOHO_BASE_URL") 
