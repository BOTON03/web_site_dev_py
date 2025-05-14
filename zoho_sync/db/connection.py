# zoho_sync/db/connection.py
import psycopg2
import psycopg2.pool
import logging
from contextlib import contextmanager
from zoho_sync.config import Config

logger = logging.getLogger(__name__)

# Configurar el pool de conexiones una sola vez
try:
    pool = psycopg2.pool.SimpleConnectionPool(
        minconn=1,
        maxconn=10, # Ajusta según necesidad
        host=Config.PG_HOST,
        database=Config.PG_DATABASE,
        user=Config.PG_USER,
        password=Config.PG_PASSWORD,
        port=Config.PG_PORT,
        sslmode=Config.PG_SSL_MODE
    )
    logger.info("✅ Pool de conexiones PostgreSQL inicializado.")
except Exception as e:
    logger.error(f"❌ Error al inicializar el pool de conexiones PostgreSQL: {e}")
    pool = None # Marcar que el pool no está disponible

@contextmanager
def get_db_connection():
    """
    Proporciona una conexión a la base de datos desde el pool.
    Uso: with get_db_connection() as conn:
             with conn.cursor() as cur:
                 # hacer cosas
    """
    if pool is None:
        logger.error("❌ El pool de conexiones no está disponible.")
        raise ConnectionError("Pool de conexiones PostgreSQL no inicializado.")
    
    conn = None
    try:
        conn = pool.getconn()
        logger.debug("Conexión obtenida del pool.")
        yield conn
        conn.commit() # Commit si todo fue bien dentro del 'with'
    except psycopg2.Error as e:
        logger.error(f"❌ Error de base de datos: {e}")
        if conn:
            conn.rollback() # Rollback en caso de error
        raise
    except Exception as e:
        logger.error(f"❌ Error inesperado con la conexión: {e}")
        if conn:
            conn.rollback()
        raise
    finally:
        if conn:
            pool.putconn(conn)
            logger.debug("Conexión devuelta al pool.")

def close_pool():
    """Cierra todas las conexiones en el pool."""
    if pool:
        logger.info("🔌 Cerrando pool de conexiones PostgreSQL...")
        pool.closeall()
        logger.info("🔌 Pool de conexiones PostgreSQL cerrado.")