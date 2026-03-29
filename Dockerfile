# ─────────────────────────────────────────────────────────────────────────────
#  Dockerfile — Mesa de Ayuda Comunicarlos
#
#  Estrategia: imagen única, multi-stage.
#    Stage 1 (builder): instala dependencias con uv en un virtualenv aislado.
#    Stage 2 (runtime): copia solo el venv y el código; sin compiladores ni uv.
#
#  Tamaño estimado imagen final: ~190 MB (python:3.13-slim + deps).
# ─────────────────────────────────────────────────────────────────────────────

# ── Stage 1: builder ─────────────────────────────────────────────────────────
FROM python:3.13-slim AS builder

# uv es el gestor de paquetes del proyecto (ver uv.lock)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /build

# Copiar solo los archivos de dependencias primero (cache layer)
COPY pyproject.toml uv.lock ./

# Instalar dependencias de producción en /build/.venv
# --no-dev:              excluye pytest, httpx y otras dev-only
# --frozen:             respeta uv.lock exactamente (reproducibilidad)
# --no-install-project: no intenta instalar el proyecto como paquete;
#                       el código se copia como módulos en el stage runtime
#                       y se usa directamente. Sin esta opción uv busca el
#                       código fuente en el builder (no disponible) y falla.
RUN uv sync --frozen --no-dev --no-install-project

# ── Stage 2: runtime ─────────────────────────────────────────────────────────
FROM python:3.13-slim AS runtime

# Usuario no-root por seguridad (OWASP: least privilege)
RUN addgroup --system app && adduser --system --ingroup app app

WORKDIR /app

# Copiar el virtualenv construido en el stage anterior
COPY --from=builder /build/.venv /app/.venv

# Copiar el código fuente de la aplicación
COPY app/ ./app/
COPY main.py ./

# El venv se activa poniendo su bin/ primero en PATH
# Los comentarios inline dentro de un bloque ENV multilínea no son válidos
# en Docker: cada variable se declara por separado para mayor claridad.
# Evita que Python genere .pyc en el contenedor
ENV PYTHONDONTWRITEBYTECODE=1
# Output sin buffer: los logs llegan a Docker inmediatamente
ENV PYTHONUNBUFFERED=1
# Activar el venv construido en el stage builder
ENV PATH="/app/.venv/bin:$PATH"
# Fallback de configuración — DEBE sobreescribirse via .env o variable de entorno
# en docker-compose. Nunca usar estos valores en un deploy real.
ENV SECRET_KEY="CAMBIAR-EN-PRODUCCION"
# MONGODB_URL y MONGODB_DB_NAME se inyectan desde .env o docker-compose.
# Ejemplo: MONGODB_URL=mongodb://mongo:27017  MONGODB_DB_NAME=mesa_de_ayuda

# Cambiar al usuario no-root antes de exponer el puerto
USER app

EXPOSE 8000

# Healthcheck: Docker comprueba que el servidor responde cada 30 s
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"

# Comando de producción.
# MongoDB soporta múltiples workers concurrentes; ajustar según cores disponibles.
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
