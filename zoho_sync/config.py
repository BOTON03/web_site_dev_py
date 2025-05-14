# zoho_sync/config.py
import os
from dotenv import load_dotenv

load_dotenv() # Carga variables desde el archivo .env

class Config:
    # Zoho Configuration
    ZOHO_CLIENT_ID = os.getenv('ZOHO_CLIENT_ID')
    ZOHO_CLIENT_SECRET = os.getenv('ZOHO_CLIENT_SECRET')
    ZOHO_REFRESH_TOKEN = os.getenv('ZOHO_REFRESH_TOKEN')
    ZOHO_TOKEN_URL = os.getenv('ZOHO_TOKEN_URL', 'https://accounts.zoho.com/oauth/v2/token') # o .eu, .in, etc.
    ZOHO_API_BASE_URL = os.getenv('ZOHO_API_BASE_URL', 'https://www.zohoapis.com/crm/v2') # o .eu, .in, etc.

    # PostgreSQL Configuration
    PG_HOST = os.getenv('PG_HOST')
    PG_DATABASE = os.getenv('PG_DATABASE')
    PG_USER = os.getenv('PG_USER')
    PG_PASSWORD = os.getenv('PG_PASSWORD')
    PG_PORT = os.getenv('PG_PORT', 5432)
    PG_SSL_MODE = os.getenv('PG_SSL_MODE', 'prefer') # 'disable', 'allow', 'prefer', 'require', 'verify-ca', 'verify-full'

    # General
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO').upper()