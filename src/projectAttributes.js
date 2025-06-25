require('dotenv').config();
const { Pool } = require('pg');
const axios = require('axios');


class ProjectAttributesSync {
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

    // (getZohoAccessToken - sin cambios, ya lanza error)
    async getZohoAccessToken() {
        try {
            // Llamada a Zoho para refrescar token: URL y parámetros son correctos.
            const response = await axios.post( // 
                    'https://accounts.zoho.com/oauth/v2/token',
                    null, // Body es null para refresh token grant
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
            if (!token) throw new Error('Access token no recibido');
            console.log('✅ Token obtenido para sincronización de Atributos');
            return token;
        } catch (error) {
            console.error('❌ Error al obtener token para Atributos:', error.response?.data || error.message);
            throw error; // Correcto: Propaga el error
        }
    }

    // (getZohoAttributes - sin cambios, ya lanza error)
    async getZohoAttributes(accessToken) {
        const query = {
            select_query: `select id, Nombre_atributo from Parametros where Tipo ='Atributo' limit 0,200`
        };
        try {
            console.log("ℹ️ Obteniendo atributos desde Zoho...");
            const response = await axios.post(`${this.zohoConfig.baseURL}/coql`, query, {
                headers: { Authorization: `Zoho-oauthtoken ${accessToken}`, 'Content-Type': 'application/json' }
            });
            const data = response.data.data || [];
            console.log(`✅ ${data.length} atributos recuperados de Zoho.`);
            return data;
        } catch (error) {
            console.error('❌ Error al obtener atributos desde Zoho:', error.response?.data || error.message);
            throw error; // Correcto: Propaga el error
        }
    }

    // (insertAttributesIntoPostgres - sin cambios, ya lanza error)
    async insertAttributesIntoPostgres(attributes) {
        if (!attributes || attributes.length === 0) {
            console.log("ℹ️ No hay atributos para insertar en PostgreSQL.");
            return { processedCount: 0, errorCount: 0 }; // Devolver un objeto más informativo
        }

        const client = await this.pool.connect();
        let processedCount = 0;
        let errorCount = 0;
        let currentAttributeId = null; // Usar ID para logging si es más fiable

        try {
            console.log(`ℹ️ Iniciando procesamiento de ${attributes.length} atributos en PostgreSQL...`);
            for (const attr of attributes) {
                if (!attr.id || !attr.Nombre_atributo) { // Validar datos del atributo
                    console.log(`⚠️ Atributo inválido (falta id o Nombre_atributo): ${JSON.stringify(attr)}. Omitiendo.`);
                    errorCount++;
                    continue;
                }
                currentAttributeId = attr.id;

                // Query para insertar o actualizar
                const upsertQuery = `
                    INSERT INTO public."Project_Attributes" (id, "name")
                    VALUES ($1, $2)
                    ON CONFLICT (id) DO UPDATE SET
                        name = EXCLUDED.name;
                `;
                // NOTA: `res.command` podría ser 'INSERT' o 'UPDATE'.
                // `res.rowCount` será 1 si se insertó o se actualizó (incluso si el valor no cambió).

                const res = await client.query(upsertQuery, [attr.id, attr.Nombre_atributo]);

                if (res.rowCount > 0) {
                    // PostgreSQL >= 9.5, `res.command` puede ser 'INSERT' o 'UPDATE'
                    // Para versiones anteriores o si no es fiable, este log es genérico.
                    console.log(`✅ Atributo ID ${attr.id} ('${attr.Nombre_atributo}') procesado (insertado/actualizado).`);
                    processedCount++;
                } else {
                    // Este caso sería raro con la query actual si la operación ON CONFLICT se ejecuta,
                    // a menos que haya un trigger o regla que prevenga la modificación.
                    // Si el `id` no existe, es un INSERT (rowCount=1).
                    // Si el `id` existe, es un UPDATE (rowCount=1).
                    console.log(`⚠️ Atributo ID ${attr.id} ('${attr.Nombre_atributo}') no afectó filas. Comando: ${res.command}.`);
                    // Podrías o no contar esto como un error dependiendo de la causa.
                }
            }
            console.log(`✅ Procesamiento de atributos completado. ${processedCount} atributos procesados, ${errorCount} atributos inválidos omitidos.`);
            return { processedCount, errorCount };

        } catch (error) {
            console.error(`❌ Error al procesar atributo en PostgreSQL (último intento ID: ${currentAttributeId}):`, error.message);
            throw error; // Propagar el error para detener el flujo general
        } finally {
            client.release();
        }
    }
    
    // (run - sin cambios, ya lanza error)
    async run() {
        let connectionClosed = false;
        try {
            console.log('🚀 Iniciando sincronización de Atributos de Proyecto...');
            // Prueba conexión PG (implícita al obtener cliente o explícita)
            const client = await this.pool.connect();
            console.log('✅ Conexión a PostgreSQL verificada para Atributos.');
            client.release(); // Liberar cliente de prueba

            const token = await this.getZohoAccessToken(); // Lanza error si falla
            const attributes = await this.getZohoAttributes(token); // Lanza error si falla
            const insertedCount = await this.insertAttributesIntoPostgres(attributes); // Ahora lanza error si falla

            console.log(`✅ Sincronización de Atributos de Proyecto finalizada. ${insertedCount} nuevos atributos insertados.`);
            // Si llegamos aquí, todo fue exitoso

        } catch (error) {
            // --- CAMBIO AQUÍ ---
            // Este catch captura errores de: conexión PG, getToken, getAttributes, o insertAttributes.
            console.error('🚨 ERROR CRÍTICO durante la sincronización de Atributos. El proceso se detendrá.', error);
            // Re-lanzar el error para que el script que llama a run() (el IIFE) sepa que falló.
            throw error;

        } finally {
            // Asegurarse de cerrar el pool solo una vez y si existe
            if (this.pool && !connectionClosed) {
                console.log('🔌 Cerrando pool de conexiones PostgreSQL para Atributos...');
                await this.pool.end().catch(err => console.error('❌ Error al cerrar pool PG para Atributos:', err));
                connectionClosed = true;
                console.log('🔌 Pool de conexiones PostgreSQL cerrado.');
            }
        }
    }
}

module.exports = ProjectAttributesSync;


