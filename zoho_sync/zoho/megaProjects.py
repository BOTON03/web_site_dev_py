# zoho_sync/zoho/megaProjects.py
import requests
from zoho_sync.config import Config

def get_mega_projects(access_token, offset=0):
    url = f"{Config.ZOHO_BASE_URL}/coql"
    headers = {
        'Authorization': f'Zoho-oauthtoken {access_token}',
        'Content-Type': 'application/json'
    }
    query = {
        "select_query": f"""
            SELECT id, Name, Direccion_MP, Slogan_comercial, Descripcion, Record_Image, Latitud_MP, Longitud_MP 
            FROM Mega_Proyectos 
            WHERE id is not null 
            LIMIT {offset}, 200
        """
    }
    response = requests.post(url, headers=headers, json=query)
    response.raise_for_status()
    data = response.json()
    return data.get('data', []), data.get('info', {}).get('more_records', False)

def get_attributes(access_token, parent_id):
    url = f"{Config.ZOHO_BASE_URL}/Atributos_Mega_Proyecto/search?criteria=Parent_Id.id:equals:{parent_id}"
    headers = {
        'Authorization': f'Zoho-oauthtoken {access_token}'
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 204:
        return None
    response.raise_for_status()
    return response.json().get('data', [])
