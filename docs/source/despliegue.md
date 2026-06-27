# Despliegue

## Docker (producción)

### Arquitectura de contenedores

```
┌─────────────┐     ┌─────────────┐
│   Caddy     │────▶│   API       │
│  (HTTPS)    │     │  (FastAPI)  │
│  :443       │     │  :8000      │
└─────────────┘     └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │   MongoDB   │
                    │   :27017    │
                    └─────────────┘
```

### Inicio rápido

```bash
# Solo HTTP (desarrollo)
docker compose up -d --build

# Con HTTPS (Caddy reverse proxy)
docker compose -f docker-compose.yml -f docker-compose.https.yml up -d --build
```

O simplemente: **doble clic en `INICIAR.bat`**

### Dockerfile: Multi-stage

1. **Builder** (uv): instala dependencias en venv aislado
2. **Runtime** (python:3.13-slim): copia venv + código, usuario non-root

Tamaño estimado: **~190 MB**

### Seguridad

- Usuario non-root (`app`)
- SECRET_KEY configurable vía `.env`
- Healthcheck nativo
- 4 workers uvicorn

## Variables de entorno

| Variable | Default | Descripción |
|----------|---------|-------------|
| `SECRET_KEY` | dev-insecure... | Clave JWT (cambiar en prod) |
| `MONGODB_URL` | mongodb://localhost:27017 | URL MongoDB |
| `MONGODB_DB_NAME` | mesa_de_ayuda | Nombre de BD |

## Certificados HTTPS (local)

Para HTTPS local, generar certificados con [mkcert](https://github.com/FiloSottile/mkcert):

```bash
mkcert -install
mkcert -cert-file infra/certs/localhost.pem -key-file infra/certs/localhost-key.pem localhost 127.0.0.1
```
