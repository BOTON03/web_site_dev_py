import os
import psycopg2
import requests
from dotenv import load_dotenv

load_dotenv()

def test_connections():
    # Configuración de PostgreSQL
    pg_config = {
        'host': os.getenv('PG_HOST'),
        'dbname': os.getenv('PG_DATABASE'),
        'user': os.getenv('PG_USER'),
        'password': os.getenv('PG_PASSWORD'),
        'port': os.getenv('PG_PORT'),
        'sslmode': 'require' if os.getenv('PG_SSL', 'false').lower() == 'true' else 'disable'
    }

    # Configuración de Zoho CRM
    zoho_config = {
        'client_id': os.getenv('ZOHO_CLIENT_ID'),
        'client_secret': os.getenv('ZOHO_CLIENT_SECRET'),
        'refresh_token': os.getenv('ZOHO_REFRESH_TOKEN'),
        'base_url': os.getenv('ZOHO_BASE_URL', 'https://www.zohoapis.com/crm/v2')
    }

    # Probar conexión a PostgreSQL
    try:
        print("🔌 Conectando a PostgreSQL...")
        conn = psycopg2.connect(**pg_config)
        with conn.cursor() as cur:
            cur.execute("SELECT NOW()")
            result = cur.fetchone()
            print("✅ PostgreSQL conectado. Hora actual:", result[0])
        conn.close()
    except psycopg2.OperationalError as e:
        print("❌ Error al conectar a PostgreSQL:", e)
        return

    # Obtener token de acceso de Zoho
    try:
        print("🔐 Solicitando token a Zoho...")
        url = 'https://accounts.zoho.com/oauth/v2/token'
        params = {
            'refresh_token': zoho_config['refresh_token'],
            'client_id': zoho_config['client_id'],
            'client_secret': zoho_config['client_secret'],
            'grant_type': 'refresh_token'
        }
        response = requests.post(url, params=params)
        data = response.json()
        access_token = data.get('access_token')
        if not access_token:
            print("❌ No se recibió access token:", data)
            return
        print("✅ Token recibido. Expira en:", data.get('expires_in', '?'), "segundos")
    except Exception as e:
        print("❌ Error al obtener el token de Zoho:", e)
        return

    # Probar conexión a Zoho CRM
    try:
        print("📡 Ejecutando consulta COQL en Zoho CRM...")
        query = "SELECT id FROM Proyectos_Inmobiliarios WHERE id is not null LIMIT 200"
        headers = {
            'Authorization': f'Zoho-oauthtoken {access_token}',
            'Content-Type': 'application/json'
        }
        response = requests.post(
            f"{zoho_config['base_url']}/coql",
            json={'select_query': query},
            headers=headers
        )
        data = response.json()
        results = data.get('data', [])
        print(f"✅ {len(results)} proyectos encontrados")
    except Exception as e:
        print("❌ Error al consultar Zoho CRM:", e)
        return

    print("\n🎉 Pruebas completadas con éxito")
