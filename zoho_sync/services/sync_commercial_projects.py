# zoho_sync/services/sync_commercial_projects.py
import logging
from zoho_sync.zoho import auth as zoho_auth
from zoho_sync.zoho import commercial_projects_api
from zoho_sync.db import commercial_projects_db
from zoho_sync.db.connection import get_db_connection

logger = logging.getLogger(__name__)

class CommercialProjectsSyncService:
    def __init__(self):
        pass

    def run_sync(self):
        logger.info("🚀 Iniciando sincronización de Proyectos Comerciales, Atributos y Tipologías...")
        access_token = None
        total_projects_fetched = 0
        total_projects_processed_successfully = 0
        total_projects_failed_processing = 0
        
        try:
            # 1. Obtener token de acceso de Zoho
            access_token = zoho_auth.get_access_token()

            # 2. Bucle de paginación para obtener Proyectos Comerciales
            offset = 0
            limit = 200 # Límite de Zoho COQL
            more_records_exist = True

            while more_records_exist:
                projects_page_data, more_records_exist = commercial_projects_api.get_zoho_commercial_projects(
                    access_token, offset, limit
                )

                if not projects_page_data:
                    logger.info(f"ℹ️ No se encontraron más Proyectos Comerciales en Zoho (offset: {offset}). Finalizando bucle.")
                    break
                
                total_projects_fetched += len(projects_page_data)
                logger.info(f"ℹ️ Procesando lote de {len(projects_page_data)} Proyectos Comerciales (offset: {offset})...")

                # 3. Procesar cada proyecto del lote
                for project_data in projects_page_data:
                    project_hc = project_data.get('id')
                    project_name_zoho = project_data.get('Name', 'Nombre Desconocido')
                    
                    if not project_hc:
                        logger.warning(f"⚠️ Proyecto sin ID en lote de Zoho (offset: {offset}). Omitiendo: {project_data}")
                        total_projects_failed_processing +=1
                        continue
                    
                    logger.debug(f"⏳ Procesando Proyecto Comercial HC: {project_hc} ('{project_name_zoho}')...")
                    
                    try:
                        # El context manager de get_db_connection maneja commit/rollback
                        with get_db_connection() as conn:
                            # a. Insertar/Actualizar el Proyecto Comercial (esto también obtiene sus atributos)
                            project_success = commercial_projects_db.upsert_commercial_project(
                                conn, project_data, access_token
                            )
                            if not project_success: # Si upsert_commercial_project retorna False por validación
                                total_projects_failed_processing +=1
                                continue # Saltar a la siguiente iteración del bucle de proyectos

                            # b. Obtener Tipologías para este proyecto
                            typologies_list = commercial_projects_api.get_zoho_project_typologies(
                                access_token, project_hc
                            )

                            # c. Insertar/Actualizar Tipologías
                            if typologies_list:
                                commercial_projects_db.upsert_project_typologies(
                                    conn, project_hc, typologies_list
                                )
                        
                        total_projects_processed_successfully += 1
                        logger.debug(f"🏁 Proyecto Comercial HC: {project_hc} ('{project_name_zoho}') y sus tipologías procesados con éxito.")

                    except Exception as e: # Captura errores de upsert_project, get_typologies, o upsert_typologies
                        total_projects_failed_processing += 1
                        logger.error(f"🚨 Falló el procesamiento completo del Proyecto HC: {project_hc} ('{project_name_zoho}'). Error: {e}. Deteniendo sincronización general.")
                        raise # Propaga para activar el catch principal y detener run_sync
                
                if not more_records_exist:
                    logger.info("ℹ️ No hay más registros de Proyectos Comerciales indicados por Zoho.")
                    break 
                
                offset += limit

            logger.info(f"✅ Sincronización de Proyectos Comerciales y Tipologías finalizada.")
            logger.info(f"📊 Resumen: {total_projects_fetched} proyectos obtenidos de Zoho.")
            logger.info(f"  > {total_projects_processed_successfully} proyectos procesados exitosamente.")
            logger.info(f"  > {total_projects_failed_processing} proyectos fallaron o fueron omitidos antes de la detención (si ocurrió).")
            if total_projects_failed_processing > 0:
                 logger.warning(f"⚠️ La sincronización se detuvo debido a errores o algunos proyectos fueron omitidos.")


        except Exception as e:
            logger.critical(f"🚨 ERROR CRÍTICO durante la sincronización de Proyectos Comerciales. El proceso se detuvo: {e}", exc_info=True)
            raise # Re-lanzar para que el script principal sepa que falló