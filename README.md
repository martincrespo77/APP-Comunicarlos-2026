# Mesa de Ayuda — Cooperativa Comunicarlos

API REST para la gestión interna de requerimientos de soporte (incidentes y solicitudes de servicio) de la Cooperativa Comunicarlos. Trabajo Práctico — PP5 / FIE 2025–2026.

---

## Arquitectura

El proyecto sigue una arquitectura en capas, con separación estricta entre dominio, aplicación e infraestructura:

```
Presentación  →  router.py + schemas.py       (FastAPI, Pydantic v2)
Aplicación    →  servicios.py                 (casos de uso, orquestación)
Dominio       →  dominio.py + repositorio.py  (entidades, lógica de negocio, interfaces)
Infraestructura → infraestructura/            (pymongo, implementaciones de repositorios)
Compartido    →  compartido/dominio.py        (shared kernel: RolUsuario)
```

Las dependencias apuntan siempre hacia adentro: la infraestructura implementa las interfaces definidas en el dominio; los servicios no conocen pymongo.

---

## Módulos principales

| Módulo | Responsabilidad |
|---|---|
| `app/usuarios/` | Registro, autenticación, consulta y desactivación de usuarios (4 roles) |
| `app/requerimientos/` | Incidentes y solicitudes con ciclo de vida completo y auditoría de eventos |
| `app/notificaciones/` | Patrón Observer puro (dominio); `DespachadorEventos` + `ObservadorRequerimiento` |
| `app/compartido/` | Shared kernel: enum `RolUsuario` usado por todos los módulos |
| `app/infraestructura/` | Adaptador MongoDB, implementaciones de repositorios |
| `app/auth.py` | Generación y decodificación de JWT (python-jose) |
| `app/config.py` | Configuración tipada con pydantic-settings (lectura desde `.env`) |
| `app/deps.py` | Dependencias FastAPI: conexión MongoDB, servicios, usuario autenticado actual |
| `main.py` | Punto de entrada: instancia `FastAPI`, monta routers, gestiona lifespan MongoDB |

---

## Requisitos previos

- **Python ≥ 3.12**
- **uv** (gestor de dependencias) — o `pip` como alternativa
- **Docker ≥ 24** y **Docker Compose ≥ 2.20** (solo para ejecución en contenedor)
- **Bruno Desktop** ≥ 1.x (para la colección de requests)

---

## Variables de entorno

Copiar `.env.example` como `.env` y completar los valores:

```env
# Clave secreta para firmar los JWT (mínimo 32 caracteres aleatorios)
SECRET_KEY=<CAMBIAR-por-clave-aleatoria-de-al-menos-32-caracteres>

# Algoritmo de firma JWT
ALGORITHM=HS256

# Tiempo de expiración del token en minutos
EXPIRACION_MINUTOS=60

# URL de conexión a MongoDB
MONGODB_URL=mongodb://localhost:27017

# Nombre de la base de datos MongoDB
MONGODB_DB_NAME=mesa_de_ayuda
```

> El archivo `.env` está en `.gitignore` y nunca debe subirse al repositorio.

---

## Cómo correr localmente

```bash
# 1. Crear y activar entorno virtual
uv venv
.venv\Scripts\activate        # Windows
source .venv/bin/activate     # Linux / macOS

# 2. Instalar dependencias
uv sync

# 3. Configurar entorno
copy .env.example .env        # Windows
cp .env.example .env          # Linux / macOS
# Editar .env con los valores reales

# 4. Iniciar el servidor en modo desarrollo
uvicorn main:app --reload
```

La API queda disponible en `http://localhost:8000`.
Documentación interactiva: `http://localhost:8000/docs` (Swagger UI).

---

## Cómo correr con Docker

```bash
# 1. Configurar entorno
copy .env.example .env
# Editar .env: configurar MONGODB_URL y MONGODB_DB_NAME

# 2. Construir y levantar
docker compose up --build

# Detener
docker compose down
```

El servicio expone el puerto `8000`. Los datos de MongoDB se persisten en el volumen `mongo_data`.

> `docker compose up` levanta automáticamente MongoDB 7 + la API. No se requiere configuración adicional.

---

## Cómo ejecutar los tests

```bash
# Todos los tests
pytest

# Con verbose
pytest -v

# Solo un módulo
pytest tests/test_requerimientos_dominio.py

# Ver tests disponibles sin ejecutar
pytest --collect-only -q
```

Los tests usan `httpx` como cliente ASGI (sin levantar servidor real). Los tests de dominio, servicios y routers no requieren base de datos real (usan repositorios en memoria). Los tests de infraestructura (`test_infraestructura.py`) usan MongoDB en memoria mediante `mongomock`.

**Cobertura actual: 394 tests en 13 archivos — todos passing.**

| Archivo | Tests |
|---|---|
| `test_requerimientos_dominio.py` | 115 |
| `test_requerimientos_router.py` | 53 |
| `test_requerimientos_servicios.py` | 30 |
| `test_requerimientos_schemas.py` | 26 |
| `test_usuarios_router.py` | 29 |
| `test_usuarios_dominio.py` | 26 |
| `test_infraestructura.py` | 23 |
| `test_auth.py` | 18 |
| `test_usuarios_servicios.py` | 17 |
| `test_usuarios_schemas.py` | 15 |
| `test_notificaciones_dominio.py` | 13 |
| `test_requerimientos_excepciones.py` | 9 |
| `test_compartido_dominio.py` | 10 |

---

## Cómo autenticar

Todos los endpoints (salvo `POST /usuarios` y `POST /usuarios/autenticar`) requieren un token JWT en el header:

```
Authorization: Bearer <token>
```

**Obtener un token:**

```http
POST /usuarios/autenticar
Content-Type: application/json

{
  "email": "operador@comunicarlos.com.ar",
  "password": "Pass1234!"
}
```

**Respuesta:**
```json
{
  "access_token": "eyJ...",
  "token_type": "bearer"
}
```

Los tokens expiran según `EXPIRACION_MINUTOS` (por defecto 60 min).

**Roles disponibles:** `solicitante`, `operador`, `tecnico`, `supervisor`

---

## Endpoints principales

### Usuarios

| Método | Ruta | Roles permitidos | Descripción |
|---|---|---|---|
| `POST` | `/usuarios` | — (público) | Registrar nuevo usuario |
| `POST` | `/usuarios/autenticar` | — (público) | Login → JWT |
| `GET` | `/usuarios` | operador, supervisor | Listar todos los usuarios |
| `GET` | `/usuarios/{id}` | operador, supervisor, propio | Ver perfil de un usuario |
| `DELETE` | `/usuarios/{id}` | supervisor | Desactivar cuenta |

### Requerimientos

| Método | Ruta | Roles permitidos | Descripción |
|---|---|---|---|
| `POST` | `/requerimientos/incidentes` | solicitante | Crear incidente |
| `POST` | `/requerimientos/solicitudes` | solicitante | Crear solicitud de servicio |
| `GET` | `/requerimientos` | todos (filtrado por rol) | Listar requerimientos |
| `GET` | `/requerimientos/{id}` | todos (con restricción) | Ver detalle + eventos |
| `POST` | `/requerimientos/{id}/asignar` | operador | Asignar técnico |
| `POST` | `/requerimientos/{id}/iniciar` | tecnico | Iniciar trabajo |
| `POST` | `/requerimientos/{id}/comentarios` | operador, tecnico | Agregar comentario |
| `POST` | `/requerimientos/{id}/derivar` | tecnico | Derivar a otro técnico |
| `POST` | `/requerimientos/{id}/resolver` | tecnico | Marcar como resuelto |

### Ciclo de vida de un requerimiento

```
NUEVO → (asignar) → ASIGNADO → (iniciar) → EN_PROGRESO
    → (resolver) → RESUELTO → (comentario de operador) → REABIERTO
```

### Utilidades

| Método | Ruta | Descripción |
|---|---|---|
| `GET` | `/health` | Estado del servidor |
| `GET` | `/docs` | Swagger UI |
| `GET` | `/redoc` | ReDoc |

---

## Colección Bruno

La colección está en `bruno/` y cubre todos los endpoints con casos felices y escenarios de error.

**Estructura:**

```
bruno/
├── bruno.json
├── environments/
│   └── Local.bru              ← variables de entorno
├── 01 - Health/               (1 request)
├── 02 - Usuarios Creacion/    (6 requests)
├── 03 - Autenticacion/        (6 requests)
├── 04 - Usuarios Consultas/   (6 requests)
├── 05 - Requerimientos Creacion/ (4 requests)
├── 06 - Requerimientos Consultas/(7 requests)
├── 07 - Ciclo de Vida/        (19 requests)
├── 08 - Supervisor/           (5 requests)
└── 09 - Errores Auth/         (3 requests)
```

**Total: 57 requests.**

**Pasos para usar:**

1. Abrir Bruno Desktop → *Open Collection* → seleccionar la carpeta `bruno/`
2. Activar el environment `Local`
3. Ejecutar en orden: primero `02 - Usuarios Creacion` para crear los usuarios, luego `03 - Autenticacion` para obtener los tokens
4. Copiar cada `access_token` en la variable correspondiente del environment (`token_operador`, `token_tecnico`, etc.)
5. Copiar los IDs de usuario retornados en las variables `id_usuario_*`
6. Continuar con las carpetas en orden numérico

**Variables definidas en `Local.bru`:**

| Variable | Descripción |
|---|---|
| `base_url` | URL base (`http://localhost:8000`) |
| `token_operador` | JWT del operador (secreto) |
| `token_tecnico` | JWT del técnico (secreto) |
| `token_solicitante` | JWT del solicitante (secreto) |
| `token_supervisor` | JWT del supervisor (secreto) |
| `id_usuario_operador` | UUID del operador creado |
| `id_usuario_tecnico` | UUID del técnico creado |
| `id_usuario_solicitante` | UUID del solicitante creado |
| `id_incidente` | UUID del incidente creado |
| `id_solicitud` | UUID de la solicitud creada |
| `id_usuario_tecnico2` | UUID del segundo técnico (para prueba de derivación) |

---

## Nota sobre la base de datos

La aplicación usa **MongoDB** como única base de datos.
La conexión se establece al arrancar la aplicación mediante `pymongo.MongoClient`.
Los índices necesarios se crean automáticamente si no existen.

No se usa ningún ORM relacional ni motor de migraciones (SQLAlchemy, Alembic, PostgreSQL, SQLite).
El úmico cambio necesario para apuntar a una instancia distinta de MongoDB es modificar `MONGODB_URL` en el `.env`.
- La variable `DATABASE_URL` es el único punto de cambio necesario en el código

---

## Limitaciones conocidas

- **SQLite no es apta para producción concurrente.** El parámetro `check_same_thread=False` permite su uso con FastAPI en un entorno de un único worker; con múltiples workers se producirían conflictos de acceso.
- **No hay sistema de notificaciones externas.** El módulo `notificaciones/` implementa el patrón Observer en el dominio puro, pero no hay integración con email, webhooks ni colas de mensajería.
- **Sin paginación.** Los endpoints `GET /usuarios` y `GET /requerimientos` devuelven todos los registros. En un volumen real se requeriría paginación con `limit`/`offset` o cursor-based.
- **Sin rate limiting.** Los endpoints públicos (`/usuarios`, `/usuarios/autenticar`) no tienen protección contra fuerza bruta más allá del hashing bcrypt.
- **Los tokens JWT no son revocables.** No existe lista negra ni mecanismo de logout; un token válido lo es hasta su expiración.

   uv sync
   ```
2. Correr la suite de pruebas del dominio:
   ```bash
   pytest tests/ -v
   ```
