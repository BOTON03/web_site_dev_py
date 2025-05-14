# zoho_sync/db/commercial_projects_db.py
import psycopg2
import logging
import json
from zoho_sync.zoho import commercial_projects_api # Para obtener atributos

logger = logging.getLogger(__name__)

def _parse_float(value_str, default=0.0):
    if value_str is None:
        return default
    try:
        return float(value_str)
    except (ValueError, TypeError):
        logger.debug(f"Valor flotante inválido '{value_str}', usando default {default}.")
        return default

def _parse_int(value_str, default=0):
    if value_str is None:
        return default
    try:
        # Podría ser una lista de un solo elemento si es un campo de selección múltiple que permite uno solo.
        if isinstance(value_str, list) and len(value_str) == 1:
            return int(value_str[0])
        return int(value_str)
    except (ValueError, TypeError, IndexError):
        logger.debug(f"Valor entero inválido '{value_str}', usando default {default}.")
        return default

def _handle_rooms_bathrooms(value, field_name):
    """
    Maneja la lógica de parseo para Habitaciones y Baños como en el código Node.js.
    """
    if value is None:
        return 0
    if isinstance(value, list):
        try:
            # Filtra por números válidos y toma el máximo, o 0 si no hay ninguno.
            numbers = [int(n) for n in value if str(n).isdigit()]
            return max(0, *numbers) if numbers else 0
        except (ValueError, TypeError):
            logger.debug(f"Error parseando lista para {field_name}: {value}. Usando 0.")
            return 0
    try:
        return int(value)
    except (ValueError, TypeError):
        logger.debug(f"Valor inválido para {field_name}: {value}. Usando 0.")
        return 0


def upsert_commercial_project(connection, project_data: dict, access_token: str):
    """
    Inserta o actualiza un Proyecto Comercial en la tabla public."Projects".
    Obtiene sus atributos relacionados desde Zoho.
    """
    hc_value = project_data.get('id')
    if not hc_value:
        logger.warning(f"⚠️ Se intentó procesar un Proyecto Comercial inválido o sin ID (hc): {project_data}. Omitiendo.")
        return False

    project_name_zoho = project_data.get('Name', 'Nombre Desconocido')

    try:
        # 1. Obtener atributos específicos para este proyecto comercial
        attributes_list = commercial_projects_api.get_zoho_project_specific_attributes(access_token, hc_value)
        attributes_json = json.dumps(attributes_list) if attributes_list else None

        # 2. Preparar datos para la tabla "Projects"
        # Mapeo de campos Zoho a PG:
        # id (Zoho) -> hc (PG)
        # Name (Zoho) -> name (PG)
        # Slogan (Zoho) -> slogan (PG)
        # ... y así sucesivamente según tu query de Node.js
        
        # El código Node.js usa Area_construida_hasta para private_area. ¡Verificar si esto es correcto!
        # Si 'private_area' debe venir de un campo distinto en Zoho (ej. 'Area_Privada_Comercial'),
        # debes añadir ese campo a la query COQL en get_zoho_commercial_projects y usarlo aquí.
        private_area = _parse_float(project_data.get('Area_construida_hasta'))

        rooms = _handle_rooms_bathrooms(project_data.get('Habitaciones'), 'Habitaciones')
        bathrooms = _handle_rooms_bathrooms(project_data.get('Ba_os'), 'Baños') # Ojo con 'Ba_os' vs 'Baños'
        
        estado_zoho = project_data.get('Estado')
        status_json = json.dumps(estado_zoho) if estado_zoho else None # Si Estado es lista de selección múltiple

        # is_public: El código Node.js lo pone en 'false'. Si debe venir de Zoho, ajústalo.
        is_public_pg = False

        # 3. Query UPSERT para public."Projects"
        # ON CONFLICT (hc)
        upsert_project_query = """
            INSERT INTO public."Projects" (
                hc, name, slogan, address, small_description, long_description, sic,
                sales_room_name, salary_minimum_count, discount_description, price_from_general,
                price_up_general, "type", mega_project_id, status, highlighted, built_area,
                private_area, rooms, bathrooms, latitude, longitude, is_public, "attributes"
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
            ON CONFLICT (hc) DO UPDATE SET
                name = EXCLUDED.name, slogan = EXCLUDED.slogan, address = EXCLUDED.address,
                small_description = EXCLUDED.small_description, long_description = EXCLUDED.long_description,
                sic = EXCLUDED.sic, sales_room_name = EXCLUDED.sales_room_name,
                salary_minimum_count = EXCLUDED.salary_minimum_count, discount_description = EXCLUDED.discount_description,
                price_from_general = EXCLUDED.price_from_general, price_up_general = EXCLUDED.price_up_general,
                "type" = EXCLUDED.type, mega_project_id = EXCLUDED.mega_project_id, status = EXCLUDED.status,
                highlighted = EXCLUDED.highlighted, built_area = EXCLUDED.built_area,
                private_area = EXCLUDED.private_area, rooms = EXCLUDED.rooms, bathrooms = EXCLUDED.bathrooms,
                latitude = EXCLUDED.latitude, longitude = EXCLUDED.longitude, is_public = EXCLUDED.is_public,
                "attributes" = EXCLUDED.attributes;
        """
        
        project_values = (
            hc_value,
            project_data.get('Name'),
            project_data.get('Slogan'),
            project_data.get('Direccion'),
            project_data.get('Descripcion_corta'),
            project_data.get('Descripcion_larga'),
            project_data.get('SIG'),
            project_data.get('Sala_de_ventas.Name'), # Lookup
            _parse_int(project_data.get('Cantidad_SMMLV')),
            project_data.get('Descripcion_descuento'),
            _parse_float(project_data.get('Precios_desde')),
            _parse_float(project_data.get('Precios_hasta')),
            project_data.get('Tipo_de_proyecto'),
            project_data.get('Mega_Proyecto.id'), # Lookup
            status_json,
            project_data.get('Proyecto_destacado', False), # Booleano
            _parse_float(project_data.get('Area_construida_desde')),
            private_area,
            rooms,
            bathrooms,
            _parse_float(project_data.get('Latitud')),
            _parse_float(project_data.get('Longitud')),
            is_public_pg,
            attributes_json
        )

        with connection.cursor() as cursor:
            cursor.execute(upsert_project_query, project_values)
        
        logger.info(f"✅ Proyecto Comercial HC {hc_value} ('{project_name_zoho}') procesado.")
        return True

    except psycopg2.Error as db_err:
        logger.error(f"❌ Error de DB procesando Proyecto Comercial HC {hc_value} ('{project_name_zoho}'): {db_err}")
        raise
    except requests.exceptions.RequestException as req_err: # Error obteniendo atributos
        logger.error(f"❌ Error de API (obteniendo atributos) para Proyecto HC {hc_value} ('{project_name_zoho}'): {req_err}")
        raise
    except Exception as e:
        logger.error(f"❌ Error inesperado procesando Proyecto HC {hc_value} ('{project_name_zoho}'): {e}")
        raise

def upsert_project_typologies(connection, project_hc: str, typologies_data: list):
    """
    Inserta o actualiza tipologías para un Proyecto Comercial en la tabla public."Typologies".
    """
    if not typologies_data:
        logger.debug(f"ℹ️ No hay tipologías para procesar para Proyecto HC {project_hc}.")
        return 0

    processed_count = 0
    current_typology_id_zoho = None

    # Query UPSERT para public."Typologies"
    # ON CONFLICT (id) -> 'id' es el ID de la tipología de Zoho
    upsert_typology_query = """
        INSERT INTO public."Typologies" (
            id, project_id, "name", description, price_from, price_up,
            rooms, bathrooms, built_area, private_area, plans, gallery
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (id) DO UPDATE SET
            project_id = EXCLUDED.project_id, "name" = EXCLUDED.name, description = EXCLUDED.description,
            price_from = EXCLUDED.price_from, price_up = EXCLUDED.price_up, rooms = EXCLUDED.rooms,
            bathrooms = EXCLUDED.bathrooms, built_area = EXCLUDED.built_area,
            private_area = EXCLUDED.private_area, plans = EXCLUDED.plans, gallery = EXCLUDED.gallery;
    """
    
    try:
        with connection.cursor() as cursor:
            logger.info(f"ℹ️ Iniciando procesamiento de {len(typologies_data)} tipologías para Proyecto HC {project_hc}...")
            for typology in typologies_data:
                typology_id_zoho = typology.get('id')
                if not typology_id_zoho:
                    logger.warning(f"⚠️ Tipología sin ID encontrada para Proyecto HC {project_hc}. Omitiendo: {typology}")
                    continue
                
                current_typology_id_zoho = typology_id_zoho # Para logging en caso de error

                # Mapeo de campos de Tipología de Zoho a PG
                # id (Zoho) -> id (PG)
                # project_id (PG) -> project_hc (que es el id del Proyecto Comercial)
                # Nombre (Zoho) -> name (PG)
                # ... y así sucesivamente.
                
                # price_up para tipologías: En Node.js es 0. Si debe venir de Zoho, ajústalo.
                price_up_typology = 0.0
                # plans y gallery para tipologías: En Node.js es null. Si deben venir de Zoho, ajústalo.
                plans_typology_json = None 
                gallery_typology_json = None

                typology_values = (
                    typology_id_zoho,
                    project_hc, # Clave foránea al proyecto
                    typology.get('Nombre'),
                    typology.get('Descripci_n'), # ¡Verifica el nombre exacto del campo en Zoho, especialmente la tilde!
                    _parse_float(typology.get('Precio_desde')),
                    price_up_typology,
                    _parse_int(typology.get('Habitaciones')),
                    _parse_int(typology.get('Ba_os')), # Ojo con 'Ba_os' vs 'Baños'
                    _parse_float(typology.get('Area_construida')),
                    _parse_float(typology.get('Area_privada')),
                    plans_typology_json,
                    gallery_typology_json
                )
                cursor.execute(upsert_typology_query, typology_values)
                processed_count += 1
                logger.debug(f"✅ Tipología ID {typology_id_zoho} ('{typology.get('Nombre')}') procesada para Proyecto HC {project_hc}.")
        
        logger.info(f"✅ {processed_count} tipologías procesadas para Proyecto HC {project_hc}.")
        return processed_count

    except psycopg2.Error as db_err:
        logger.error(f"❌ Error de DB procesando tipología ID Zoho {current_typology_id_zoho} para Proyecto HC {project_hc}: {db_err}")
        raise
    except Exception as e:
        logger.error(f"❌ Error inesperado procesando tipología ID Zoho {current_typology_id_zoho} para Proyecto HC {project_hc}: {e}")
        raise