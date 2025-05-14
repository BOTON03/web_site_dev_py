# zoho_sync/db/mega_projects_db.py
import psycopg2
import logging
import json
from zoho_sync.zoho import mega_projects_api # Para obtener atributos

logger = logging.getLogger(__name__)

def upsert_mega_project(connection, project_data: dict, access_token: str):
    """
    Inserta o actualiza un Mega Proyecto en la tabla public."Mega_Projects".
    Obtiene los atributos relacionados desde Zoho antes de la inserción/actualización.
    """
    if not project_data or not project_data.get('id'):
        logger.warning(f"⚠️ Se intentó procesar un Mega Proyecto inválido o sin ID: {project_data}. Omitiendo.")
        return False # Indica que no se procesó

    project_id = project_data['id']
    project_name = project_data.get('Name', 'Nombre Desconocido')

    try:
        # 1. Obtener atributos para este proyecto desde Zoho
        # Esta llamada se hace aquí para replicar la lógica del Node.js donde
        # getAttributesFromZoho se llama dentro de insertMegaProjectIntoPostgres.
        attributes_list = mega_projects_api.get_zoho_mega_project_attributes(access_token, project_id)
        attributes_json = json.dumps(attributes_list) if attributes_list else None

        # 2. Preparar otros datos para la base de datos
        # Campos de Zoho: id, Name, Direccion_MP, Slogan_comercial, Descripcion,
        #                 Record_Image, Latitud_MP, Longitud_MP
        # Campos de PG: id, name, address, slogan, description, "attributes",
        #                 gallery, latitude, longitude, is_public
        
        latitude_str = project_data.get('Latitud_MP')
        longitude_str = project_data.get('Longitud_MP')
        
        try:
            latitude = float(latitude_str) if latitude_str else 0.0
        except (ValueError, TypeError):
            logger.warning(f"Latitud inválida '{latitude_str}' para proyecto ID {project_id}. Usando 0.0.")
            latitude = 0.0
            
        try:
            longitude = float(longitude_str) if longitude_str else 0.0
        except (ValueError, TypeError):
            logger.warning(f"Longitud inválida '{longitude_str}' para proyecto ID {project_id}. Usando 0.0.")
            longitude = 0.0

        gallery_raw = project_data.get('Record_Image', '')
        gallery_list = []
        if gallery_raw and isinstance(gallery_raw, str):
            gallery_list = [item.strip() for item in gallery_raw.split(',') if item.strip()]
        gallery_json = json.dumps(gallery_list)

        # El campo 'is_public' se establece en 'false' en el código Node.js.
        # Si este valor debe venir de Zoho, asegúrate de que la query COQL
        # en get_zoho_mega_projects() lo incluya y lo uses aquí.
        is_public = False 

        # 3. Construir y ejecutar la query UPSERT
        # Asegúrate que los nombres de columna coincidan con tu tabla en PostgreSQL.
        # Especialmente si usaste comillas dobles al crearla: public."Mega_Projects", "attributes".
        upsert_query = """
            INSERT INTO public."Mega_Projects" (
                id, name, address, slogan, description, "attributes",
                gallery, latitude, longitude, is_public
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
            ON CONFLICT (id) DO UPDATE SET 
                name = EXCLUDED.name,
                address = EXCLUDED.address,
                slogan = EXCLUDED.slogan,
                description = EXCLUDED.description,
                "attributes" = EXCLUDED."attributes",
                gallery = EXCLUDED.gallery,
                latitude = EXCLUDED.latitude,
                longitude = EXCLUDED.longitude,
                is_public = EXCLUDED.is_public;
        """
        
        values = (
            project_id,
            project_data.get('Name'),
            project_data.get('Direccion_MP'),
            project_data.get('Slogan_comercial'),
            project_data.get('Descripcion'),
            attributes_json,
            gallery_json,
            latitude,
            longitude,
            is_public
        )

        with connection.cursor() as cursor:
            cursor.execute(upsert_query, values)
        
        # connection.commit() # El commit se maneja en el context manager de get_db_connection
        logger.info(f"✅ Mega Proyecto ID {project_id} ('{project_name}') procesado (insertado/actualizado).")
        return True # Indica que se procesó exitosamente

    except psycopg2.Error as db_err:
        logger.error(f"❌ Error de base de datos al procesar Mega Proyecto ID {project_id} ('{project_name}'): {db_err}")
        # connection.rollback() # El rollback se maneja en el context manager
        raise # Relanzar para que el servicio lo capture y detenga el proceso
    except requests.exceptions.RequestException as req_err: # Error al obtener atributos
        logger.error(f"❌ Error de API (obteniendo atributos) para Mega Proyecto ID {project_id} ('{project_name}'): {req_err}")
        raise # Relanzar para que el servicio lo capture y detenga el proceso
    except Exception as e:
        logger.error(f"❌ Error inesperado al procesar Mega Proyecto ID {project_id} ('{project_name}'): {e}")
        raise # Relanzar para que el servicio lo capture y detenga el proceso