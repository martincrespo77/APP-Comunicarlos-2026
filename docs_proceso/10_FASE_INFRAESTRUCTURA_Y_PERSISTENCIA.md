# Fase 10: Infraestructura y Persistencia

## 1. Objetivo de la fase
Traducir, guardar y reconstruir la memoria abstracta de nuestro proyecto mediante un adaptador real de persistencia, conectando todas nuestras entidades de Pura a Persistente.

> **Nota de actualización:** Esta fase se implementó originalmente con SQLAlchemy/SQLite. Posteriormente se migró completamente a **MongoDB/pymongo**, demostrando que la arquitectura hexagonal (repositorios abstractos) cumplió su propósito. Solo se tocaron archivos de infraestructura; dominio y servicios quedaron intactos.

## 2. Por qué esta fase se hizo después
Construir bases de datos antes de comprender íntimamente las complejas validaciones de nuestro negocio (como separar `Incidente` de `Solicitud`) lleva al diseño *DataBase-Driven*, con tablas llenas de parches (campos booleanos extraños como "is_incidente") y comportamientos raros. Hacerla al final nos permitió mapear la persistencia con claridad milimétrica acorde a lo que las Entidades pedían, no al revés.

## 3. Implementación de los Repositorios Concretos
En las subcarpetas `app/infraestructura/` instanciamos las clases que implementan formalmente la palabra clave `ABC` exigida en la Fase 5:
- `RepositorioRequerimientoMongo`: Adquiere el objeto puro de Dominio, lo serializa a un diccionario con `_dominio_a_doc()` (UUIDs como strings, enums como `.value`, eventos y comentarios embebidos) y lo persiste con `replace_one(upsert=True)`.
- `RepositorioUsuarioMongo`: Análogamente convierte `Usuario` a documento MongoDB y viceversa con `_doc_a_dominio()`.

## 4. `config.py` y dependencias cruzadas en `deps.py`
Para erradicar mágicos Hardcodings, importamos `pydantic-settings` de forma que nuestra persistencia exija al ambiente real que informe `MONGODB_URL` y `MONGODB_DB_NAME`, así como Secret Keys para JWT. El archivo `deps.py` organiza elegantemente el proveedor: `get_database()` obtiene la instancia de la base MongoDB conectada en el lifespan, y las funciones `get_*_service()` inyectan los repositorios concretos.

## 5. Inicialización de DB y MVP
En el Lifespan de la App (`main.py`) se invoca `conectar()` al arrancar y `desconectar()` al cerrar. La función `conectar()` establece la conexión MongoClient y ejecuta `_crear_indices()` para generar índices únicos (email en usuarios, número de requerimiento). MongoDB no requiere migraciones de esquema como Alembic, lo cual simplifica el despliegue académico.
