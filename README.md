# Zoho Sync

Aplicación para sincronizar datos de Mega Proyectos entre Zoho y PostgreSQL.

## Estructura del Proyecto

```
zoho_sync/
│
├── zoho_sync/                   # Módulo principal
│   ├── __init__.py              # Indica que es un paquete Python
│   ├── config.py                # Gestión de configuraciones y variables de entorno
│   │
│   ├── zoho/                    # Interacción con API de Zoho
│   │   ├── __init__.py
│   │   ├── auth.py              # Autenticación y tokens de acceso
│   │   └── megaProjects.py      # Obtención de datos de Mega Proyectos
│   │
│   ├── db/                      # Operaciones con PostgreSQL
│   │   ├── __init__.py
│   │   ├── connection.py        # Gestión de conexiones a la BD
│   │   └── mega_projects.py     # Operaciones CRUD para Mega Proyectos
│   │
│   └── services/                # Lógica de negocio
│       ├── __init__.py
│       └── sync.py              # Orquestación del proceso de sincronización
│
├── tests/                       # Pruebas unitarias e integración
│   ├── __init__.py
│   ├── test_auth.py             # Pruebas de autenticación
│   ├── test_projects.py         # Pruebas de obtención de datos
│   └── test_sync.py             # Pruebas del proceso completo de sincronización
│
├── .env                         # Variables de entorno y credenciales
├── .gitignore                   # Archivos a ignorar por Git
├── requirements.txt             # Dependencias del proyecto
├── README.md                    # Documentación y guía de uso
└── main.py                      # Punto de entrada para ejecución
```

## Instalación

1. Clonar el repositorio:
   ```
   git clone [URL_DEL_REPOSITORIO]
   cd zoho_sync
   ```

2. Crear un entorno virtual e instalar dependencias:
   ```
   python -m venv venv
   source venv/bin/activate  # En Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. Configurar el archivo `.env` con tus credenciales:
   ```
   ZOHO_CLIENT_ID=tu_client_id
   ZOHO_CLIENT_SECRET=tu_client_secret
   ZOHO_REDIRECT_URI=tu_redirect_uri
   
   DB_HOST=localhost
   DB_PORT=5432
   DB_NAME=nombre_bd
   DB_USER=usuario
   DB_PASSWORD=contraseña
   ```

## Uso

Para ejecutar la sincronización:

```
python main.py
```

## Pruebas

Para ejecutar las pruebas:

```
pytest tests/
```

## Contribución

1. Hacer fork del repositorio
2. Crear una rama para tu feature (`git checkout -b feature/nueva-caracteristica`)
3. Commit de tus cambios (`git commit -m 'Añadir nueva característica'`)
4. Push a la rama (`git push origin feature/nueva-caracteristica`)
5. Crear un Pull Request