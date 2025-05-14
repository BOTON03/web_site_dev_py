# zoho_sync/zoho/mega_projects_api.py
import requests
import logging
from zoho_sync.config import Config

logger = logging.getLogger(__name__)

def get_zoho_mega_projects(access_token: str, offset: int = 0, limit: int = 200):
    """
    Obtiene una página de Mega Proyectos desde Zoho CRM usando COQL.
    """
    url = f"{Config.ZOHO_API_BASE_URL}/coql"
    headers = {
        'Authorization': f'Zoho-oauthtoken {access_token}',
        'Content-Type': 'application/json'
    }
    # Campos basados en tu SELECT de Node.js
    # IMPORTANTE: Si necesitas 'Es_Publico' de Zoho, añádelo aquí.
    #             Actualmente, el INSERT en Node.js lo pone como 'false' por defecto.
    query_body = {
        "select_query": f"""
            SELECT
                id, Name, Direccion_MP, Slogan_comercial, Descripcion,
                Record_Image, Latitud_MP, Longitud_MP
            FROM Mega_Proyectos
            WHERE id is not null
            LIMIT {offset},{limit}
        """
    }

    try:
        logger.info(f"ℹ️ Obteniendo Mega Proyectos desde Zoho (offset: {offset}, limit: {limit})...")
        response = requests.post(url, headers=headers, json=query_body)
        response.raise_for_status()  # Lanza HTTPError para respuestas 4xx/5xx

        data_response = response.json()
        projects_data = data_response.get('data', [])
        more_records = data_response.get('info', {}).get('more_records', False)
        count = data_response.get('info', {}).get('count', 0)

        logger.info(f"✅ {len(projects_data)} Mega Proyectos recuperados (total en esta página: {count}). Más registros: {more_records}")
        return projects_data, more_records
    except requests.exceptions.RequestException as e:
        error_message = e.response.text if e.response else str(e)
        logger.error(f"❌ Error al obtener Mega Proyectos desde Zoho: {error_message}")
        raise
    except Exception as e:
        logger.error(f"❌ Error inesperado procesando respuesta de Mega Proyectos de Zoho: {e}")
        raise

def get_zoho_mega_project_attributes(access_token: str, parent_project_id: str):
    """
    Obtiene los atributos de un Mega Proyecto específico desde Zoho CRM.
    El módulo en Zoho se llama 'Atributos_Mega_Proyecto'.
    """
    # Asegúrate que 'Atributos_Mega_Proyecto' es el nombre API correcto del módulo relacionado.
    # Y 'Parent_Id' es el nombre API correcto del campo lookup en 'Atributos_Mega_Proyecto'
    # que apunta a 'Mega_Proyectos'.
    url = f"{Config.ZOHO_API_BASE_URL}/Atributos_Mega_Proyecto/search?criteria=(Parent_Id.id:equals:{parent_project_id})"
    headers = {
        'Authorization': f'Zoho-oauthtoken {access_token}'
    }

    try:
        logger.debug(f"ℹ️ Obteniendo atributos para Mega Proyecto ID {parent_project_id} desde Zoho...")
        response = requests.get(url, headers=headers)

        if response.status_code == 204: # No Content
            logger.debug(f"ℹ️ No se encontraron atributos (Zoho 204) para Mega Proyecto ID {parent_project_id}.")
            return [] # Devuelve lista vacía si no hay atributos

        response.raise_for_status() # Lanza error para otros códigos 4xx/5xx

        data_response = response.json()
        attributes_data = data_response.get('data', [])
        
        if not attributes_data:
            logger.debug(f"ℹ️ Atributos vacíos (Zoho 200 OK, pero sin 'data') para Mega Proyecto ID {parent_project_id}.")
            return []

        logger.debug(f"✅ {len(attributes_data)} atributos recuperados para Mega Proyecto ID {parent_project_id}.")
        return attributes_data
    except requests.exceptions.RequestException as e:
        error_message = e.response.text if e.response else str(e)
        # No relanzar si es un 404 o similar que pueda ser "normal" si un proyecto no tiene atributos.
        # Sin embargo, el código Node.js relanza, así que mantendremos esa lógica.
        logger.error(f"❌ Error al obtener atributos para Mega Proyecto ID {parent_project_id}: {error_message}")
        raise
    except Exception as e:
        logger.error(f"❌ Error inesperado procesando respuesta de atributos para Mega Proyecto ID {parent_project_id}: {e}")
        raise