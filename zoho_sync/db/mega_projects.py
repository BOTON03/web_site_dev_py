# zoho_sync/db/mega_projects.py
import json
from zoho_sync.db.connection import get_connection

def insert_mega_project(project, attributes):
    conn = get_connection()
    cursor = conn.cursor()
    insert_query = """
        INSERT INTO public."Mega_Projects" (
            id, name, address, slogan, description, attributes,
            gallery, latitude, longitude, is_public
        ) VALUES (
            %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s
        )
        ON CONFLICT (id) DO UPDATE SET
            name = EXCLUDED.name,
            address = EXCLUDED.address,
            slogan = EXCLUDED.slogan,
            description = EXCLUDED.description,
            attributes = EXCLUDED.attributes,
            gallery = EXCLUDED.gallery,
            latitude = EXCLUDED.latitude,
            longitude = EXCLUDED.longitude,
            is_public = EXCLUDED.is_public;
    """
    
    values = (
        project.get('id'),
        project.get('Name'),
        project.get('Direccion_MP'),
        project.get('Slogan_comercial', ''),
        project.get('Descripcion', ''),
        json.dumps(attributes) if attributes else None,
        json.dumps(project.get('Record_Image', '').split(',')) if project.get('Record_Image') else None,
        project.get('Latitud_MP'),
        project.get('Longitud_MP'),
        project.get('Es_Publico', False)
    )
    cursor.execute(insert_query, values)
    conn.commit()
    cursor.close()
    conn.close()
