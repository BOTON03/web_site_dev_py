# zoho_sync/services/sync_project_attributes.py
import logging
from zoho_sync.zoho import auth as zoho_auth
# Renombrar la importación si el archivo se llama diferente o la función tiene otro nombre
from zoho_sync.zoho.project_attributes import get_zoho_parameter_attributes_page # O get_all_zoho_parameter_attributes si quieres todos
from zoho_sync.db import project_attributes_db as db_pa # Alias para claridad
from zoho_sync.db.connection import get_db_connection

logger = logging.getLogger(__name__)

class ProjectAttributesSyncService:
    def __init__(self):
        pass

    def run_sync(self):
        logger.info("🚀 Iniciando sincronización de Atributos de 'Parametros' (Tipo='Atributo')...")
        
        try:
            # 1. Obtener token de acceso de Zoho
            access_token = zoho_auth.get_access_token()

            # 2. Obtener atributos de Zoho (solo la primera página, como en el script Node.js)
            # El script Node.js no implementa paginación para getZohoAttributes,
            # así que llamamos a la función que obtiene una página.
            # Si quisieras TODOS los atributos y `get_all_zoho_parameter_attributes` está implementado:
            # attributes_data = get_all_zoho_parameter_attributes(access_token)
            attributes_data, _ = get_zoho_parameter_attributes_page(access_token, offset=0, limit=200)


            if not attributes_data:
                logger.info("ℹ️ No se encontraron atributos en 'Parametros' (Tipo='Atributo') en Zoho para sincronizar.")
                logger.info("✅ Sincronización de Atributos de 'Parametros' finalizada (sin datos).")
                return

            # 3. Insertar/Actualizar atributos en PostgreSQL
            with get_db_connection() as conn:
                # La función upsert_project_attributes ahora devuelve un dict
                result = db_pa.upsert_project_attributes(conn, attributes_data) 
            
            processed_count = result.get("processed_count", 0)
            # El error_count ya se loguea dentro de upsert_project_attributes

            logger.info(f"✅ Sincronización de Atributos de 'Parametros' finalizada. {processed_count} atributos procesados.")

        except ConnectionError as e:
             logger.error(f"🚨 ERROR CRÍTICO de conexión a la BD: {e}. El proceso se detendrá.")
             raise
        except Exception as e:
            logger.error(f"🚨 ERROR CRÍTICO durante la sincronización de Atributos de 'Parametros': {e}", exc_info=True)
            raise