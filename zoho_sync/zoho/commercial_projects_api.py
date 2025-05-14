# zoho_sync/zoho/commercial_projects_api.py
import requests
import logging
from zoho_sync.config import Config

logger = logging.getLogger(__name__)

def get_zoho_commercial_projects(access_token: str, offset: int = 0, limit: int = 200):
    """
    Obtiene una página de Proyectos Comerciales desde Zoho CRM usando COQL.
    """
    url = f"{Config.ZOHO_API_BASE_URL}/coql"
    headers = {
        'Authorization': f'Zoho-oauthtoken {access_token}',
        'Content-Type': 'application/json'
    }
    # Campos basados en tu SELECT de Node.js para Proyectos_Comerciales
    query_body = {
        "select_query": f"""
            SELECT
                id, Name, Slogan, Direccion, Descripcion_corta, Descripcion_larga,
                SIG, Sala_de_ventas.Name, Cantidad_SMMLV, Descripcion_descuento,
                Precios_desde, Precios_hasta, Tipo_de_proyecto, Mega_Proyecto.id,
                Estado, Proyecto_destacado, Area_construida_desde, Area_construida_hasta,
                Habitaciones, Ba_os, Latitud, Longitud
            FROM Proyectos_Comerciales
            WHERE id is not null
            LIMIT {offset},{limit}
        """
    }

    try:
        logger.info(f"ℹ️ Obteniendo Proyectos Comerciales desde Zoho (offset: {offset}, limit: {limit})...")
        response = requests.post(url, headers=headers, json=query_body)
        response.raise_for_status()

        data_response = response.json()
        projects_data = data_response.get('data', [])
        more_records = data_response.get('info', {}).get('more_records', False)
        count = data_response.get('info', {}).get('count', 0)

        logger.info(f"✅ {len(projects_data)} Proyectos Comerciales recuperados (Zoho count: {count}). Más registros: {more_records}")
        return projects_data, more_records
    except requests.exceptions.RequestException as e:
        error_message = e.response.text if e.response else str(e)
        logger.error(f"❌ Error al obtener Proyectos Comerciales desde Zoho: {error_message}")
        raise
    except Exception as e:
        logger.error(f"❌ Error inesperado procesando respuesta de Proyectos Comerciales de Zoho: {e}")
        raise

def get_zoho_project_specific_attributes(access_token: str, parent_project_id: str):
    """
    Obtiene los atributos de un Proyecto Comercial específico desde Zoho CRM.
    Asume que el módulo de atributos se llama 'Atributos' y se relaciona por 'Parent_Id'.
    """
    # IMPORTANTE: Confirma el nombre API del módulo de atributos para Proyectos Comerciales.
    # Si es el mismo módulo 'Atributos' que para 'Project_Attributes' (Mega Proyectos),
    # esta función es muy similar a la que ya tienes, pero la mantenemos separada por claridad
    # y porque el código Node.js las tiene como funciones distintas en clases distintas.
    url = f"{Config.ZOHO_API_BASE_URL}/Atributos/search?criteria=(Parent_Id.id:equals:{parent_project_id})"
    headers = {
        'Authorization': f'Zoho-oauthtoken {access_token}'
    }

    try:
        logger.debug(f"ℹ️ Obteniendo atributos (módulo 'Atributos') para Proyecto Comercial ID {parent_project_id}...")
        response = requests.get(url, headers=headers)

        if response.status_code == 204: # No Content
            logger.debug(f"ℹ️ No se encontraron atributos (Zoho 204) para Proyecto Comercial ID {parent_project_id} (módulo 'Atributos').")
            return [] # Devuelve lista vacía

        response.raise_for_status()

        data_response = response.json()
        attributes_data = data_response.get('data', [])
        
        if not attributes_data:
            logger.debug(f"ℹ️ Atributos vacíos (Zoho 200 OK, pero sin 'data') para Proyecto Comercial ID {parent_project_id} (módulo 'Atributos').")
            return []

        logger.debug(f"✅ {len(attributes_data)} atributos (módulo 'Atributos') recuperados para Proyecto Comercial ID {parent_project_id}.")
        return attributes_data
    except requests.exceptions.RequestException as e:
        error_message = e.response.text if e.response else str(e)
        logger.error(f"❌ Error al obtener atributos (módulo 'Atributos') para Proyecto Comercial ID {parent_project_id}: {error_message}")
        raise
    except Exception as e:
        logger.error(f"❌ Error inesperado procesando respuesta de atributos (módulo 'Atributos') para Proyecto Comercial ID {parent_project_id}: {e}")
        raise

def get_zoho_project_typologies(access_token: str, parent_project_id: str):
    """
    Obtiene las tipologías de un Proyecto Comercial específico desde Zoho CRM.
    Asume que el módulo de tipologías se llama 'Tipologias' y se relaciona por 'Parent_Id'.
    """
    # IMPORTANTE: Confirma el nombre API del módulo de tipologías.
    url = f"{Config.ZOHO_API_BASE_URL}/Tipologias/search?criteria=(Parent_Id.id:equals:{parent_project_id})"
    headers = {
        'Authorization': f'Zoho-oauthtoken {access_token}'
    }

    try:
        logger.debug(f"ℹ️ Obteniendo tipologías (módulo 'Tipologias') para Proyecto Comercial ID {parent_project_id}...")
        response = requests.get(url, headers=headers)

        if response.status_code == 204: # No Content
            logger.debug(f"ℹ️ No se encontraron tipologías (Zoho 204) para Proyecto Comercial ID {parent_project_id} (módulo 'Tipologias').")
            return []

        response.raise_for_status()

        data_response = response.json()
        typologies_data = data_response.get('data', [])

        if not typologies_data:
            logger.debug(f"ℹ️ Tipologías vacías (Zoho 200 OK, pero sin 'data') para Proyecto Comercial ID {parent_project_id} (módulo 'Tipologias').")
            return []
            
        logger.debug(f"✅ {len(typologies_data)} tipologías (módulo 'Tipologias') recuperadas para Proyecto Comercial ID {parent_project_id}.")
        return typologies_data
    except requests.exceptions.RequestException as e:
        error_message = e.response.text if e.response else str(e)
        logger.error(f"❌ Error al obtener tipologías (módulo 'Tipologias') para Proyecto Comercial ID {parent_project_id}: {error_message}")
        raise
    except Exception as e:
        logger.error(f"❌ Error inesperado procesando respuesta de tipologías (módulo 'Tipologias') para Proyecto Comercial ID {parent_project_id}: {e}")
        raise