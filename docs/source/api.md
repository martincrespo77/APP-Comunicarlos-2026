# API REST

## Autenticación

Todos los endpoints protegidos requieren un header `Authorization: Bearer <token>`.

El token se obtiene con `POST /usuarios/autenticar` enviando email y password.

Claims del JWT: `sub` (user_id), `rol`, `iat`, `exp`.

## Endpoints

### Usuarios (`/usuarios`)

| Método | Ruta | Rol requerido | Descripción |
|--------|------|---------------|-------------|
| `POST` | `/usuarios/` | Público | Registrar nuevo usuario |
| `POST` | `/usuarios/autenticar` | Público | Login → JWT |
| `GET` | `/usuarios/` | Supervisor, Operador | Listar usuarios |
| `GET` | `/usuarios/{id}` | Autenticado | Obtener usuario por ID |
| `DELETE` | `/usuarios/{id}` | Supervisor | Desactivar usuario |

### Requerimientos (`/requerimientos`)

| Método | Ruta | Rol requerido | Descripción |
|--------|------|---------------|-------------|
| `POST` | `/requerimientos/incidentes` | Autenticado | Crear incidente |
| `POST` | `/requerimientos/solicitudes` | Autenticado | Crear solicitud |
| `GET` | `/requerimientos/` | Supervisor, Operador | Listar (con filtros) |
| `GET` | `/requerimientos/{id}` | Autenticado | Obtener detalle |
| `POST` | `/requerimientos/{id}/asignar-tecnico` | Operador, Supervisor | Asignar técnico |
| `POST` | `/requerimientos/{id}/iniciar-trabajo` | Técnico | Marcar en progreso |
| `POST` | `/requerimientos/{id}/resolver` | Técnico, Supervisor | Resolver |
| `POST` | `/requerimientos/{id}/derivar` | Operador, Supervisor | Derivar a otro técnico |
| `POST` | `/requerimientos/{id}/comentarios` | Autenticado | Agregar comentario |

### Infraestructura

| Método | Ruta | Descripción |
|--------|------|-------------|
| `GET` | `/health` | Health check |

## DTOs (Schemas Pydantic)

### Convención de nombres
- **`*In`** — datos de entrada (request body)
- **`*Out`** — datos de salida (response)

### Schemas de entrada
- `UsuarioCrearIn` (nombre, email, rol, password)
- `UsuarioAutenticarIn` (email, password)
- `IncidenteCrearIn` (titulo, descripcion, solicitante_id, urgencia, categoria)
- `SolicitudCrearIn` (titulo, descripcion, solicitante_id, categoria)
- `AsignarTecnicoIn` (tecnico_id)
- `DerivarRequerimientoIn` (tecnico_destino_id, motivo)
- `ComentarioAgregarIn` (contenido)

### Schemas de salida
- `UsuarioOut` (id, nombre, email, rol, activo, fechas)
- `TokenOut` (access_token, token_type)
- `RequerimientoOut` (todos los campos + comentarios + eventos anidados)
- `ComentarioOut`, `EventoOut`

## Documentación interactiva

- **Swagger UI**: `/docs`
- **ReDoc**: `/redoc`
