# Fase 11: Dockerización y Despliegue

## 1. Objetivo de la fase
Empaquetar la totalidad del sistema (API y entorno de ejecución) en un contenedor portátil virtualizado. Aislar dependencias del Sistema Operativo Host ("Funciona en mi máquina").

## 2. Decisiones de ejecución (`Dockerfile` y `docker-compose`)
El despliegue está optimizado para construir usando `uv` puro copiando las dependencias estáticas bloqueadas en `uv.lock`. La imagen base elegida fue una `python:3.12-slim` para evitar peso inútil en imágenes ubuntu o debian gruesas. 
Se combinó con `docker-compose.yml` donde preparamos el servicio `api` permitiendo al evaluador no conocer sintaxis Docker y abriendo el puerto 8000 en escasos segundos con un solo comando `up`.

## 3. MongoDB y volumen de estado
El servicio `mongo:7` se levanta como contenedor independiente con un volumen `mongo_data` para persistir los datos entre reinicios. La API se conecta vía `MONGODB_URL` (por defecto `mongodb://mongo:27017`) y depende del healthcheck de MongoDB (`mongosh --eval 'db.runCommand("ping")'`) antes de arrancar, garantizando que la base esté lista.

## 4. Limpieza del repositorio (`.gitignore` y `.dockerignore`)
Garantizamos la pureza de GitHub impidiendo que binarios masivos de Python como `__pycache__` o las frágiles `.env` fueran pusheadas, usando su equivalente gemelo `.env.example` como plantilla para que quien instale la aplicación sepa cómo forjar sus contraseñas JWT personalizadas o su conexión DB custom.

## 5. Correcciones e iteraciones hechas en Build
Durante la migración a MongoDB, el principal ajuste fue configurar `depends_on` con `condition: service_healthy` para que la API no intentara conectarse antes de que MongoDB estuviera listo. También se eliminaron los volúmenes SQLite previos y se simplificó la configuración a un único volumen `mongo_data` para los datos de MongoDB.
