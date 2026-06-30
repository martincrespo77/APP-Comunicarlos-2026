"""Punto de entrada de la aplicación FastAPI — Mesa de Ayuda Comunicarlos.

Monta los routers y configura el handler global de excepciones no capturadas.

Arranque para desarrollo:
    uvicorn main:app --reload

Arranque para producción (Docker):
    uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
"""

from __future__ import annotations

import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request, status
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app.requerimientos.excepciones import RequerimientoError
from app.requerimientos.router import router as requerimientos_router
from app.usuarios.excepciones import UsuarioError
from app.usuarios.router import router as usuarios_router


# ── Lifespan (startup / shutdown) ─────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:  # noqa: ARG001
    """Inicializa la infraestructura al arrancar y la libera al detener.

    Startup: conecta al MongoClient y crea índices.
    Shutdown: cierra el MongoClient liberando conexiones del pool.
    """
    from app.config import get_settings
    from app.infraestructura.database import conectar, desconectar

    settings = get_settings()
    conectar(settings.MONGODB_URL, settings.MONGODB_DB_NAME)

    yield  # ← aquí corre la app

    desconectar()


# ── Aplicación ────────────────────────────────────────────────────────

app = FastAPI(
    title="Mesa de Ayuda — Cooperativa Comunicarlos",
    description=(
        "API REST para gestión de incidentes y solicitudes de servicio. "
        "Permite a solicitantes abrir requerimientos, operadores asignarlos "
        "y técnicos gestionarlos hasta su resolución."
    ),
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ── Routers ───────────────────────────────────────────────────────────

app.include_router(
    usuarios_router,
    prefix="/usuarios",
    tags=["usuarios"],
)

app.include_router(
    requerimientos_router,
    prefix="/requerimientos",
    tags=["requerimientos"],
)


# ── Handlers globales de excepciones no capturadas ───────────────────

@app.exception_handler(UsuarioError)
async def usuario_error_handler(request: Request, exc: UsuarioError) -> JSONResponse:
    """Captura cualquier UsuarioError que no haya sido atrapado en el router."""
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": str(exc)},
    )


@app.exception_handler(RequerimientoError)
async def requerimiento_error_handler(
    request: Request, exc: RequerimientoError
) -> JSONResponse:
    """Captura cualquier RequerimientoError no atrapado en el router."""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": str(exc)},
    )


# ── Health check ─────────────────────────────────────────────────────

@app.get("/health", tags=["infraestructura"], summary="Estado del servicio")
def health() -> dict:
    """Endpoint de salud para load balancers y liveness probes."""
    return {"status": "ok"}


# ── Archivos estáticos: UML, documentación, portal ──────────────────

_root = os.path.dirname(__file__)
_static_dir = os.path.join(_root, "static")
_uml_dir = os.path.join(_static_dir, "uml")
_docs_html_dir = os.path.join(_root, "docs", "build", "html")

# UML interactivo (Mermaid.js)
if os.path.isdir(_uml_dir):
    app.mount("/uml", StaticFiles(directory=_uml_dir, html=True), name="uml")

# Documentación Sphinx (si fue generada)
if os.path.isdir(_docs_html_dir):
    app.mount(
        "/documentacion",
        StaticFiles(directory=_docs_html_dir, html=True),
        name="documentacion",
    )

# Frontend (SPA) — debe ir después de /uml y /documentacion
_app_dir = os.path.join(_root, "frontend")
if os.path.isdir(_app_dir):
    app.mount("/app", StaticFiles(directory=_app_dir, html=True), name="frontend")


@app.get("/", include_in_schema=False)
def portal():
    """Portal de bienvenida con links a todos los recursos."""
    index = os.path.join(_static_dir, "index.html")
    if os.path.isfile(index):
        return FileResponse(index)
    return {"message": "Mesa de Ayuda — Comunicarlos", "docs": "/docs"}
