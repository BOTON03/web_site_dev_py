# zoho_sync/db/project_attributes_db.py
import psycopg2
import logging

logger = logging.getLogger(__name__)

def upsert_project_attributes(connection, attributes: list):
    """
    Inserta o actualiza atributos en la tabla public."Project_Attributes".
    Espera que cada 'attr' en 'attributes' sea un diccionario con 'id' y 'Nombre_atributo'.
    Retorna un diccionario con processed_count y error_count.
    """
    if not attributes:
        logger.info("ℹ️ No hay atributos (de Parametros) para insertar/actualizar en PostgreSQL.")
        return {"processed_count": 0, "error_count": 0}

    upsert_query = """
        INSERT INTO public."Project_Attributes" (id, name)
        VALUES (%s, %s)
        ON CONFLICT (id) DO UPDATE SET
            name = EXCLUDED.name;
    """
    
    processed_count = 0
    error_count = 0
    current_attribute_id_zoho = None

    try:
        with connection.cursor() as cursor:
            logger.info(f"ℹ️ Iniciando procesamiento de {len(attributes)} atributos (de Parametros) en PostgreSQL...")
            for attr in attributes:
                attr_id_zoho = attr.get('id')
                attr_name_zoho = attr.get('Nombre_atributo')

                if not attr_id_zoho or attr_name_zoho is None: 
                    logger.warning(f"⚠️ Atributo (de Parametros) inválido (falta id o Nombre_atributo): {attr}. Omitiendo.")
                    error_count += 1
                    continue
                
                current_attribute_id_zoho = attr_id_zoho
                try:
                    cursor.execute(upsert_query, (attr_id_zoho, attr_name_zoho))
                    # cursor.rowcount puede no ser fiable en todos los casos con ON CONFLICT para psycopg2 < 2.7
                    # pero para UPSERT, si no hay error, se considera procesado.
                    # if cursor.rowcount > 0:
                    logger.debug(f"✅ Atributo (de Parametros) ID {attr_id_zoho} ('{attr_name_zoho}') procesado (insertado/actualizado).")
                    processed_count += 1
                    # else:
                    #     logger.warning(f"⚠️ Atributo (de Parametros) ID {attr_id_zoho} ('{attr_name_zoho}') no afectó filas. Status: {cursor.statusmessage}")
                except psycopg2.Error as db_err:
                    logger.error(f"❌ Error de DB al procesar atributo (de Parametros) ID {attr_id_zoho}: {db_err}")
                    error_count += 1
                    # connection.rollback() # El context manager lo hará si hay error general

        logger.info(f"✅ Procesamiento de atributos (de Parametros) completado. {processed_count} procesados, {error_count} con errores/omitidos.")
        return {"processed_count": processed_count, "error_count": error_count}

    except Exception as e:
        logger.error(f"❌ Error general al procesar atributos (de Parametros) en PostgreSQL (último intento ID Zoho: {current_attribute_id_zoho}): {e}")
        raise