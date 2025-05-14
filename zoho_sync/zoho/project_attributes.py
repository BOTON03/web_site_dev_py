# zoho_sync/zoho/project_attributes.py
import requests
import logging
from zoho_sync.config import Config

logger = logging.getLogger(__name__)

def get_zoho_parameter_attributes_page(access_token: str, offset: int = 0, limit: int = 200):
    """
    Obtiene una página de atributos desde el módulo 'Parametros' de Zoho CRM
    filtrando por Tipo = 'Atributo'.
    Devuelve los datos y un booleano indicando si hay más registros.
    """
    url = f"{Config.ZOHO_API_BASE_URL}/coql"
    headers = {
        'Authorization': f'Zoho-oauthtoken {access_token}',
        'Content-Type': 'application/json'
    }
    query_body = {
        # La query del Node.js es: select id, Nombre_atributo from Parametros where Tipo ='Atributo' limit 0,200
        "select_query": f"select id, Nombre_atributo from Parametros where Tipo = 'Atributo' limit {offset},{limit}"
    }

    try:
        logger.info(f"ℹ️ Obteniendo atributos de 'Parametros' desde Zoho (offset: {offset}, limit: {limit})...")
        response = requests.post(url, headers=headers, json=query_body)
        response.raise_for_status() 
        
        data_response = response.json()
        attributes = data_response.get('data', [])
        more_records = data_response.get('info', {}).get('more_records', False)
        
        logger.info(f"✅ {len(attributes)} atributos de 'Parametros' recuperados de Zoho. Más registros: {more_records}")
        return attributes, more_records # Devuelve también more_records por si se quiere paginar en el futuro
    except requests.exceptions.RequestException as e:
        error_message = e.response.text if e.response else str(e)
        logger.error(f"❌ Error al obtener atributos de 'Parametros' desde Zoho: {error_message}")
        raise
    except Exception as e:
        logger.error(f"❌ Error inesperado al procesar respuesta de atributos de 'Parametros' de Zoho: {e}")
        raise

# Si quisieras paginar y obtener TODOS los atributos:
def get_all_zoho_parameter_attributes(access_token: str):
    """
    Obtiene todos los atributos de 'Parametros' (Tipo='Atributo'), manejando la paginación.
    """
    all_attributes = []
    offset = 0
    limit = 200
    
    while True:
        attributes_page, more_records = get_zoho_parameter_attributes_page(access_token, offset, limit)
        if attributes_page:
            all_attributes.extend(attributes_page)
        
        if not more_records:
            break
        offset += limit
            
    logger.info(f"✅ Total de {len(all_attributes)} atributos de 'Parametros' (Tipo='Atributo') recuperados de Zoho.")
    return all_attributes