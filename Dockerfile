# Usar una imagen base oficial de Python. Python 3.11-slim es una buena elección.
FROM python:3.11-slim

# Establecer variables de entorno
ENV PYTHONDONTWRITEBYTECODE 1  # Evita que Python escriba archivos .pyc
ENV PYTHONUNBUFFERED 1         # Fuerza a Python a no bufferizar stdout y stderr, bueno para logs en Docker

# Establecer el directorio de trabajo en el contenedor
WORKDIR /app

# Crear un usuario no root y cambiar a él
# Es importante crear el grupo primero si vas a especificar GID
RUN groupadd -r appuser && useradd --no-log-init -r -g appuser appuser
# COPY --chown=appuser:appuser . /app # Opcional: copiar con el owner correcto de una vez
# USER appuser # Cambiar a usuario no root aquí o después de copiar los archivos

# Copiar el archivo de requerimientos primero para aprovechar el cache de Docker
COPY requirements.txt .

# Instalar las dependencias
# --no-cache-dir reduce el tamaño de la imagen
# --upgrade pip asegura que tienes la última versión de pip antes de instalar
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copiar el resto del código de la aplicación al directorio de trabajo
# Si quieres que el usuario no root sea dueño de los archivos copiados:
COPY --chown=appuser:appuser . .
# Si no usaste --chown en COPY, puedes cambiar el propietario del directorio /app
# RUN chown -R appuser:appuser /app

# Cambiar al usuario no root para ejecutar la aplicación
USER appuser

# Comando para ejecutar la aplicación cuando el contenedor inicie
# Asegúrate de que main.py es el punto de entrada principal.
# Si test_conexiones.py es para una prueba inicial, puedes tener un script de entrada
# que lo ejecute y luego ejecute main.py, o usar perfiles de Docker Compose.
# Para la aplicación principal:
CMD ["python", "main.py"]

# Si quisieras mantener la opción de ejecutar test_conexiones.py, podrías hacerlo
# a través de un `docker exec` o un `docker-compose run` con un comando diferente.
# O, si es parte del arranque, un script de entrada sería mejor.
# CMD ["python", "test_conexiones.py"]