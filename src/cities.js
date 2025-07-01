require('dotenv').config();
const { Pool } = require('pg');
const axios = require('axios');

class CitiesSync {
    constructor() {
        this.pool = new Pool({
            host: process.env.PG_HOST,
            database: process.env.PG_DATABASE,
            user: process.env.PG_USER,
            password: process.env.PG_PASSWORD,
            port: process.env.PG_PORT || 5432,
            ssl: process.env.PG_SSL === 'true' ? { rejectUnauthorized: false } : false
        });

        this.zohoConfig = {
            clientId: process.env.ZOHO_CLIENT_ID,
            clientSecret: process.env.ZOHO_CLIENT_SECRET,
            refreshToken: process.env.ZOHO_REFRESH_TOKEN,
            baseURL: 'https://www.zohoapis.com/crm/v2'
        };
    }

    async getZohoAccessToken() {
        try {
            const response = await axios.post(
                'https://accounts.zoho.com/oauth/v2/token',
                null,
                {
                    params: {
                        refresh_token: this.zohoConfig.refreshToken,
                        client_id: this.zohoConfig.clientId,
                        client_secret: this.zohoConfig.clientSecret,
                        grant_type: 'refresh_token'
                    }
                }
            );
            const token = response.data.access_token;
            if (!token) throw new Error('Access token no recibido de Zoho');
            console.log('✅ Token obtenido para sincronización de Ciudades');
            return token;
        } catch (error) {
            console.error('❌ Error al obtener token para Ciudades:', error.response?.data || error.message);
            throw error;
        }
    }

    async getZohoCities(accessToken) {
        const query = {
            select_query: "SELECT Ciudad.Name, Ciudad.id FROM Proyectos_Comerciales WHERE Ciudad is not null limit 0, 200"
        };
        try {
            console.log("ℹ️ Obteniendo ciudades desde Zoho...");
            const response = await axios.post(`${this.zohoConfig.baseURL}/coql`, query, {
                headers: { Authorization: `Zoho-oauthtoken ${accessToken}`, 'Content-Type': 'application/json' }
            });
            const data = response.data.data || [];
            console.log(`✅ ${data.length} registros de ciudad recuperados de Zoho.`);
            return data;
        } catch (error) {
            console.error('❌ Error al obtener ciudades desde Zoho:', error.response?.data || error.message);
            throw error;
        }
    }
    
    async insertCitiesIntoPostgres(cities) {
        if (!cities || cities.length === 0) {
            console.log("ℹ️ No hay ciudades para insertar en PostgreSQL.");
            return { processedCount: 0, errorCount: 0 };
        }

        const citiesMap = new Map();
        for (const city of cities) {
            if (city['Ciudad.id']) {
                 citiesMap.set(city['Ciudad.id'], city);
            }
        }
        const uniqueCities = Array.from(citiesMap.values());
        console.log(`ℹ️ Se encontraron ${uniqueCities.length} ciudades únicas de un total de ${cities.length} registros.`);

        const client = await this.pool.connect();
        let processedCount = 0;
        let errorCount = 0;
        let currentCityId = null;

        try {
            console.log(`ℹ️ Iniciando procesamiento de ${uniqueCities.length} ciudades en PostgreSQL...`);
            for (const city of uniqueCities) {
                const cityId = city['Ciudad.id'];
                const fullCityName = city['Ciudad.Name'];

                if (!cityId || !fullCityName) {
                    console.log(`⚠️ Registro de ciudad inválido (falta id o nombre): ${JSON.stringify(city)}. Omitiendo.`);
                    errorCount++;
                    continue;
                }
                currentCityId = cityId;
                
                const cityName = fullCityName.split('/')[0].trim();
                
                if (!cityName) { // Validación extra por si el nombre queda vacío
                    console.log(`⚠️ Nombre de ciudad vacío después de limpiar: "${fullCityName}". Omitiendo.`);
                    errorCount++;
                    continue;
                }

                // Query para insertar o actualizar (UPSERT) en la tabla "Cities"
                const upsertQuery = `
                    INSERT INTO public."Cities" (id, "name", is_public)
                    VALUES ($1, $2, $3)
                    ON CONFLICT (id) DO UPDATE SET
                        "name" = EXCLUDED.name,
                        is_public = EXCLUDED.is_public;
                `;
                
                const res = await client.query(upsertQuery, [cityId, cityName, true]);

                if (res.rowCount > 0) {
                    console.log(`✅ Ciudad ID ${cityId} ('${cityName}') procesada (insertada/actualizada).`);
                    processedCount++;
                } else {
                     // Esto puede pasar si los datos en Zoho son idénticos a los de la DB, por lo que el UPDATE no afecta filas.
                    console.log(`ℹ️ Ciudad ID ${cityId} ('${cityName}') sin cambios en la base de datos.`);
                }
            }
            console.log(`✅ Procesamiento de ciudades completado. ${processedCount} ciudades procesadas, ${errorCount} registros inválidos omitidos.`);
            return { processedCount, errorCount };

        } catch (error) {
            if (error.code === '23505' && error.constraint === 'Cities_name_key') {
                 console.error(`❌ Error de unicidad al procesar en PostgreSQL. Es posible que un ID de ciudad diferente intente usar un nombre que ya existe: ${error.detail}`);
            } else {
                console.error(`❌ Error al procesar ciudad en PostgreSQL (último intento ID: ${currentCityId}):`, error.message);
            }
            throw error;
        } finally {
            client.release();
        }
    }
    
    async run() {
        // El pool se cierra en el bloque de ejecución final para evitar cerrarlo prematuramente.
        try {
            console.log('🚀 Iniciando sincronización de Ciudades...');
            const client = await this.pool.connect();
            console.log('✅ Conexión a PostgreSQL verificada para Ciudades.');
            client.release();

            const token = await this.getZohoAccessToken();
            const citiesFromZoho = await this.getZohoCities(token);
            await this.insertCitiesIntoPostgres(citiesFromZoho);

        } catch (error) {
            console.error('🚨 ERROR CRÍTICO durante la sincronización de Ciudades. El proceso se detendrá.');
            throw error; // Propagar el error para que lo capture el bloque de ejecución
        }
    }
}

// Exportar la clase para poder usarla en otros archivos si es necesario
module.exports = CitiesSync;
