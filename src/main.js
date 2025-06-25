const express = require('express')
const fs = require('fs');
const path = require('path');
const MegaSync = require('./megaProyectos');
const AttributeSync = require('./projectAttributes');
const ZohoToPostgresSyncProjects = require('./projects');
const CitiesSync = require('./cities');
const app = express()
const port = process.env.PORT || 5000
 
app.get('/', (req, res) => {
  res.send('Conexion exitosa de la API')
});

app.post('/', async (req, res) => {
  console.log("==================================================================");
    console.log("🚀 INICIANDO PROCESO DE SINCRONIZACIÓN COMPLETO");
    console.log("==================================================================");

    try {
      // Instancias de sincronización
        const syncCities = new CitiesSync();
        const syncMega = new MegaSync();
        const syncAttributes = new AttributeSync();
        const syncProjects = new ZohoToPostgresSyncProjects();

        await Promise.all([
            syncCities.run(),
            syncMega.run(),
            syncAttributes.run(),
            syncProjects.run()
        ]);        
        console.log("🎉 ¡TODAS LAS SINCRONIZACIONES SE HAN EJECUTADO!");        
        res.send('Proceso de sincronización completado.');
    } catch (error) {
        console.error("\n!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!");
        console.error("🚨 ERROR CRÍTICO: El proceso de sincronización se detuvo.");
        console.error(`   Mensaje: ${error.message}`);
        
        if (error.stack) {
             console.error(`   Stack Trace: ${error.stack}`);
        }
        if (error.response?.data) {
            console.error(`   Respuesta del API (Zoho): ${JSON.stringify(error.response.data)}`);
        }
        res.status(500).send('Error en el proceso de sincronización.');
    } finally {
        // El bloque `finally` se ejecuta siempre, haya habido éxito o error.
        console.log("🏁 Proceso de sincronización finalizado.");
        // <<< SE ELIMINÓ TODA LA LÓGICA DE LECTURA Y ANÁLISIS DEL ARCHIVO DE LOG.
    }
})
 
app.listen(port, () => {
  console.log(`Example app listening on port ${port}`)
})

 