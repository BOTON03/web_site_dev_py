# main.py
import logging
import sys
import os
from zoho_sync.config import Config
# ... (tus otras importaciones de servicios y close_pool) ...
from zoho_sync.services.sync_project_attributes import ProjectAttributesSyncService
from zoho_sync.services.sync_mega_projects import MegaProjectsSyncService
from zoho_sync.services.sync_commercial_projects import CommercialProjectsSyncService
from zoho_sync.db.connection import close_pool


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_FILE_PATH = os.path.join(BASE_DIR, 'sync.log')

# --- CONFIGURACIÓN DE LOGGING PERSONALIZADA ---

root_logger = logging.getLogger()
root_logger.setLevel(Config.LOG_LEVEL)

file_formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
)
console_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

# Handler para el archivo de log (con todos los detalles)
# CAMBIO AQUÍ: mode='w' para sobrescribir el archivo en cada ejecución
file_handler = logging.FileHandler(LOG_FILE_PATH, mode='w', encoding='utf-8') # <--- 'w' for write (overwrite)
file_handler.setFormatter(file_formatter)
# file_handler.setLevel(logging.DEBUG) # Opcional

console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(console_formatter)
console_handler.setLevel(logging.WARNING)

root_logger.addHandler(file_handler)
root_logger.addHandler(console_handler)

# --- FIN DE CONFIGURACIÓN DE LOGGING ---

app_logger = logging.getLogger(__name__)

# Mensaje inicial al archivo de log (ahora que se sobrescribe, es útil tenerlo al inicio del archivo)
app_logger.info(f"Logging configurado para sobrescribir. Nivel: {Config.LOG_LEVEL}. Archivo de log: {LOG_FILE_PATH}")


def main():
    print(f"{logging.Formatter('%(asctime)s').format(logging.LogRecord(None, None, '', 0, '', (), None, None))} - INFO - Iniciando proceso de sincronización general...")
    app_logger.info("🏁 Iniciando proceso de sincronización general...")

    sync_failed = False

    try:
        app_logger.info("--- Iniciando Sincronización de Mega Proyectos ---")
        mega_project_sync_service = MegaProjectsSyncService()
        mega_project_sync_service.run_sync()
        app_logger.info("--- Sincronización de Mega Proyectos completada ---")

        app_logger.info("--- Iniciando Sincronización de Atributos de 'Parametros' (Tipo='Atributo') ---")
        project_attribute_sync_service = ProjectAttributesSyncService()
        project_attribute_sync_service.run_sync()
        app_logger.info("--- Sincronización de Atributos de 'Parametros' completada ---")        

        app_logger.info("--- Iniciando Sincronización de Proyectos Comerciales y Tipologías ---")
        commercial_projects_sync_service = CommercialProjectsSyncService()
        commercial_projects_sync_service.run_sync()
        app_logger.info("--- Sincronización de Proyectos Comerciales y Tipologías completada ---")

    except Exception as e:
        app_logger.critical(f"💥 ERROR FATAL en el proceso de sincronización principal. Error: {e}", exc_info=True)
        sync_failed = True
    finally:
        app_logger.info("🧹 Limpiando recursos...")
        close_pool()
        
        final_message_level = "INFO" if not sync_failed else "ERROR"
        final_message = "Proceso de sincronización general finalizado."
        if sync_failed:
            final_message += " (CON ERRORES)"
        
        print(f"{logging.Formatter('%(asctime)s').format(logging.LogRecord(None, None, '', 0, '', (), None, None))} - {final_message_level} - {final_message}")
        app_logger.info(f"🚪 {final_message}")
        
        if sync_failed:
            sys.exit(1)
        else:
            sys.exit(0)

if __name__ == "__main__":
    main()