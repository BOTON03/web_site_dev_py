# zoho_sync/zoho/auth.py
import requests
import logging
from zoho_sync.config import Config

logger = logging.getLogger(__name__)

def get_access_token():
    """
    Obtiene un nuevo access token de Zoho usando el refresh token.
    """
    try:
        payload = {
            'refresh_token': Config.ZOHO_REFRESH_TOKEN,
            'client_id': Config.ZOHO_CLIENT_ID,
            'client_secret': Config.ZOHO_CLIENT_SECRET,
            'grant_type': 'refresh_token'
        }
        response = requests.post(Config.ZOHO_TOKEN_URL, params=payload)
        response.raise_for_status()  # Lanza una excepción para códigos de error HTTP
        token_data = response.json()
        access_token = token_data.get('access_token')
        if not access_token:
            logger.error("No se recibió el access_token en la respuesta de Zoho.")
            raise ValueError("Access token no recibido de Zoho.")
        logger.info("✅ Access token obtenido/refrescado exitosamente.")
        return access_token
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Error al obtener token de Zoho: {e.response.text if e.response else e}")
        raise
    except ValueError as e:
        logger.error(f"❌ Error procesando respuesta de token de Zoho: {e}")
        raise