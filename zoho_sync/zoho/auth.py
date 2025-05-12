# zoho_sync/zoho/auth.py
import requests
from zoho_sync.config import Config

def get_access_token():
    url = 'https://accounts.zoho.com/oauth/v2/token'
    params = {
        'refresh_token': Config.ZOHO_REFRESH_TOKEN,
        'client_id': Config.ZOHO_CLIENT_ID,
        'client_secret': Config.ZOHO_CLIENT_SECRET,
        'grant_type': 'refresh_token'
    }
    response = requests.post(url, params=params)
    response.raise_for_status()
    return response.json()['access_token']
