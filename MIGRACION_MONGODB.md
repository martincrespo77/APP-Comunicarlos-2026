# Migración a MongoDB-Only — Registro de transición

Este documento registra la decisión, el estado y el progreso de la migración
del sistema de persistencia, de SQLAlchemy/SQLite a MongoDB exclusivamente.

---

## Decisión

La aplicación usa MongoDB como **única** base de datos permitida.

Quedan explícitamente prohibidos:
- SQLite (en cualquier variante: archivo, `:memory:`, volumen Docker)
- PostgreSQL
- MySQL
- SQLAlchemy como ORM o capa de abstracción
- Alembic como motor de migraciones

Driver objetivo: **`pymongo>=4.7`** (sync, oficial MongoDB Inc.)

---

## Justificación arquitectónica

La arquitectura hexagonal del proyecto ya garantiza que el dominio, los
servicios, los routers y los schemas Pydantic son **completamente agnósticos
a la base de datos**. El acoplamiento a SQLAlchemy siempre estuvo confinado
a 6 archivos de la capa de infraestructura.

Esto convierte la migración en un reemplazo de adaptador, no en un refactor
de negocio. Las reglas de dominio, los flujos de ciclo de vida, los permisos
por rol y la estructura de eventos no cambian.

---

## Estado por fase

| Fase | Descripción | Estado |
|------|-------------|--------|
| Fase 1 | Limpieza de configuración, Docker y documentación | ✅ Completado |
| Fase 2 | Adaptador MongoDB: `database.py` + eliminación de `modelos_orm.py` | ✅ Completado |
| Fase 3 | Repositorios concretos MongoDB (`repo_usuarios`, `repo_requerimientos`) | ✅ Completado |
| Fase 4 | Ajuste de `deps.py`, `main.py` y `config.py` | ✅ Completado |
| Fase 5 | Refactor de `test_infraestructura.py` con `mongomock` | ✅ Completado |
| Fase 6 | Activar servicio `mongo` en `docker-compose.yml` | ✅ Completado |
| Fase 7 | Actualización de `docs_proceso/` | ✅ Completado |
| Fase 8 | Validación final (grep, pytest, Bruno, Docker) | ✅ Completado |

---

## Fase 1 — Detalle de cambios realizados

### Archivos modificados

| Archivo | Cambio |
|---------|--------|
| `.env.example` | Eliminado bloque `DATABASE_URL` (SQLite + PostgreSQL). Reemplazado por placeholder `MONGODB_URL` / `MONGODB_DB_NAME`. |
| `Dockerfile` | Eliminado `ENV DATABASE_URL`, `RUN mkdir /data`. Actualizado workers de 1 a 4. Eliminado comentario sobre limitación SQLite. |
| `docker-compose.yml` | Eliminado volumen `sqlite_data` y su referencia en el servicio `api`. Eliminado bloque PostgreSQL comentado. Sustituido por bloque MongoDB comentado listo para Fase 6. |
| `.gitignore` | Eliminadas entradas `*.db` y `*.sqlite3`. Agregado `dump/` para backups MongoDB locales. |
| `README.md` | Actualizado stack en arquitectura, tabla de módulos, sección de variables de entorno, instrucciones Docker, descripción de tests y nota final de base de datos. |
| `app/infraestructura/__init__.py` | Eliminadas referencias a "engine SQLAlchemy", "Base ORM", "implementación SQL". Documentado estado de transición y módulos objetivo. |

### Archivos intencionalmente NO modificados en esta fase

Los siguientes archivos siguen referenciando SQLAlchemy. Es el estado
correcto para esta fase: se modifican en fases posteriores de forma atómica
para evitar romper el arranque de la aplicación.

| Archivo | Motivo |
|---------|--------|
| `app/config.py` | Contiene `DATABASE_URL`; se reemplaza en Fase 4 junto con `deps.py` |
| `pyproject.toml` | Contiene `sqlalchemy>=2.0`; se elimina en Fase 2 junto con `pymongo` |
| `app/infraestructura/database.py` | Reescritura completa en Fase 2 |
| `app/infraestructura/modelos_orm.py` | Eliminación en Fase 2/3 |
| `app/infraestructura/repo_usuarios.py` | Reescritura en Fase 3 |
| `app/infraestructura/repo_requerimientos.py` | Reescritura en Fase 3 |
| `app/deps.py` | Refactor en Fase 4 |
| `main.py` | Lifespan se actualiza en Fase 4 |
| `conftest.py` | Actualización en Fase 5 |
| `tests/test_infraestructura.py` | Reescritura en Fase 5 |

---

## Diseño objetivo de colecciones MongoDB

### Colección `usuarios`
```
{
  "_id": "<uuid-string>",
  "nombre": "...",
  "email": "...",
  "rol": "operador",
  "password_hash": "...",
  "activo": true,
  "fecha_creacion": ISODate,
  "ultimo_acceso": ISODate | null
}
```
Índices: `email` (unique)

### Colección `requerimientos`
Documento único por requerimiento. Eventos y comentarios se **embeben**
como arrays — no hay colecciones separadas.

```
{
  "_id": "<uuid-string>",
  "tipo": "incidente | solicitud",
  "titulo": "...",
  "descripcion": "...",
  "estado": "abierto | asignado | en_progreso | resuelto | reabierto",
  "solicitante_id": "<uuid>",
  "operador_id": "<uuid> | null",
  "tecnico_asignado_id": "<uuid> | null",
  "urgencia": "critica | importante | menor | null",
  "categoria": "...",
  "fecha_creacion": ISODate,
  "fecha_actualizacion": ISODate,
  "eventos": [
    {
      "id": "<uuid>",
      "tipo": "creacion | asignacion | ...",
      "actor_id": "<uuid>",
      "detalle": "...",
      "fecha": ISODate
    }
  ],
  "comentarios": [
    {
      "id": "<uuid>",
      "autor_id": "<uuid>",
      "rol_autor": "operador | tecnico | ...",
      "contenido": "...",
      "fecha": ISODate
    }
  ]
}
```
Índices: `solicitante_id`, `tecnico_asignado_id`, `estado`

---

## Criterios de aceptación finales (Fase 8)

El proyecto estará correcto solo si:

- [ ] `grep -ri "sqlalchemy" app/ tests/ main.py conftest.py` → 0 resultados
- [ ] `grep -ri "sqlite" app/ tests/ main.py conftest.py Dockerfile docker-compose.yml` → 0 resultados
- [ ] `grep -r "DATABASE_URL" app/ tests/ main.py conftest.py .env.example` → 0 resultados
- [ ] `sqlalchemy` no aparece en `pyproject.toml` ni en `uv.lock`
- [ ] `modelos_orm.py` no existe
- [ ] `pytest` pasa al 100%
- [ ] `docker compose up --build` levanta API + MongoDB sin errores
- [ ] Colección Bruno responde correctamente contra MongoDB
- [ ] `README.md` no menciona SQLAlchemy, SQLite ni PostgreSQL como opciones válidas
