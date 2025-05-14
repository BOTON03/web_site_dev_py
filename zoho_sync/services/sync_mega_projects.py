# zoho_sync/services/sync_mega_projects.py
import logging
from zoho_sync.zoho import auth as zoho_auth
from zoho_sync.zoho import mega_projects_api
from zoho_sync.db import mega_projects_db
from zoho_sync.db.connection import get_db_connection

logger = logging.getLogger(__name__)

class MegaProjectsSyncService:
    def __init__(self):
        # La configuración se accede a través de Config directamente en los módulos.
        pass

    def run_sync(self):
        logger.info("🚀 Iniciando sincronización de Mega Proyectos...")
        access_token = None
        total_projects_processed_successfully = 0
        total_projects_fetched = 0
        
        try:
            # 1. Obtener token de acceso de Zoho
            access_token = zoho_auth.get_access_token()

            # 2. Bucle de paginación para obtener Mega Proyectos
            offset = 0
            limit = 200 # Límite de Zoho COQL por página
            more_records = True

            while more_records:
                projects_page, more_records = mega_projects_api.get_zoho_mega_projects(
                    access_token, offset, limit
                )

                if not projects_page:
                    logger.info(f"ℹ️ No se encontraron más Mega Proyectos en Zoho (offset: {offset}). Finalizando bucle.")
                    break
                
                total_projects_fetched += len(projects_page)
                logger.info(f"ℹ️ Procesando lote de {len(projects_page)} Mega Proyectos (offset: {offset})...")

                # 3. Procesar cada proyecto del lote
                for project_data in projects_page:
                    try:
                        # El context manager de get_db_connection maneja commit/rollback
                        with get_db_connection() as conn:
                            success = mega_projects_db.upsert_mega_project(conn, project_data, access_token)
                            if success:
                                total_projects_processed_successfully +=1
                        # Si upsert_mega_project lanza una excepción, se propagará y
                        # el catch externo la manejará, deteniendo la sincronización.
                    except Exception as project_error:
                        # Error ya logueado en upsert_mega_project
                        logger.error(f"🚨 Falló el procesamiento del Mega Proyecto ID: {project_data.get('id', 'ID desconocido')}. Deteniendo sincronización general.")
                        raise project_error # Propaga para activar el catch principal y detener 'run_sync'.
                
                if not more_records:
                    logger.info("ℹ️ No hay más registros de Mega Proyectos indicados por Zoho.")
                    break 
                
                offset += limit

            logger.info(f"✅ Sincronización de Mega Proyectos finalizada. {total_projects_processed_successfully} de {total_projects_fetched} proyectos procesados exitosamente.")
            if total_projects_fetched > total_projects_processed_successfully:
                 logger.warning(f"{total_projects_fetched - total_projects_processed_successfully} proyectos no se procesaron debido a errores previos antes de la detención.")


        except Exception as e:
            logger.error(f"🚨 ERROR CRÍTICO durante la sincronización de Mega Proyectos. El proceso se detuvo: {e}")
            raise # Re-lanzar para que el script principal sepa que falló
        # finally:
            # El pool se cierra en main.py