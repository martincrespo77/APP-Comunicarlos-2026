# Colección de Requests — Mesa de Ayuda

Archivo único `.http` compatible con la extensión **REST Client** de VS Code.

## Requisitos

| Herramienta | Versión mínima |
|---|---|
| VS Code | Cualquiera |
| Extensión **REST Client** (ID: `humao.rest-client`) | 0.25+ |
| App corriendo en `http://localhost:8000` | — |

Instalar la extensión:

```
Ctrl+Shift+X → buscar "REST Client" → Install
```

## Iniciar la app

### Opción A — desarrollo local

```bash
# activar entorno virtual
.venv\Scripts\activate        # Windows
source .venv/bin/activate     # Linux/Mac

uvicorn main:app --reload
```

### Opción B — Docker

```bash
cp .env.example .env          # editar SECRET_KEY antes de subir a producción
docker compose up --build
```

## Flujo de demostración

El archivo `mesa_de_ayuda.http` está ordenado para ejecutarse de arriba a abajo:

```
01 — Health check                  (sin auth)
02 — Crear usuarios                (sin auth — endpoint público)
03 — Autenticar / obtener tokens   (copiar los JWT en las variables @token_...)
04 — Consultar usuarios            (operador, supervisor)
05 — Crear requerimientos          (solicitante crea incidente y solicitud)
06 — Consultar requerimientos      (filtros por estado, solicitante, rol)
07 — Asignar técnico               (operador asigna)
08 — Iniciar trabajo               (técnico inicia)
09 — Agregar comentarios           (cualquier rol autenticado)
10 — Derivar a otro técnico        (técnico deriva)
11 — Resolver                      (técnico cierra)
12 — Gestión de usuarios           (supervisor lista / desactiva)
13 — Errores de autenticación      (tokens inválidos, sin token)
```

## Variables a actualizar

Después de correr los requests de creación (02) y autenticación (03),
editar estas variables al inicio del archivo `.http`:

```http
@token_operador    = <pegar el access_token del 03.01>
@token_tecnico     = <pegar el access_token del 03.02>
@token_solicitante = <pegar el access_token del 03.03>
@token_supervisor  = <pegar el access_token del 03.04>

@id_usuario_operador    = <pegar el id del 02.01>
@id_usuario_tecnico     = <pegar el id del 02.02>
@id_usuario_solicitante = <pegar el id del 02.03>
@id_incidente           = <pegar el id del 05.01>
@id_solicitud           = <pegar el id del 05.02>
```

## Documentación de la API

Con la app corriendo, acceder a `http://localhost:8000/docs` para ver el Swagger UI completo.
