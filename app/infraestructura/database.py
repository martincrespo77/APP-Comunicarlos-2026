"""Conexión MongoDB centralizada.

Gestiona el ciclo de vida del ``MongoClient`` y expone la base de datos
a los repositorios concretos.

Diseño:
  - ``conectar()`` se llama una sola vez desde el lifespan de ``main.py``.
  - ``get_database()`` es el punto de acceso para dependencias y repos.
  - ``desconectar()`` se llama al detener el servidor.
  - ``_crear_indices()`` crea índices idempotentes al arrancar.
"""

from __future__ import annotations

from pymongo import MongoClient
from pymongo.database import Database

_client: MongoClient | None = None
_db: Database | None = None


def conectar(mongodb_url: str, db_name: str) -> Database:
    """Crea el MongoClient y selecciona la base de datos.

    Debe llamarse una sola vez al arrancar (lifespan de main.py).
    Retorna la instancia ``Database`` para conveniencia del caller.
    """
    global _client, _db
    _client = MongoClient(mongodb_url)
    _db = _client[db_name]
    _crear_indices(_db)
    return _db


def desconectar() -> None:
    """Cierra el MongoClient liberando conexiones del pool."""
    global _client, _db
    if _client is not None:
        _client.close()
    _client = None
    _db = None


def get_database() -> Database:
    """Retorna la base de datos activa.

    Raises ``RuntimeError`` si ``conectar()`` no fue invocado.
    """
    if _db is None:
        raise RuntimeError(
            "Base de datos no inicializada. "
            "Llamar a conectar() desde el lifespan antes de usar get_database()."
        )
    return _db


def _crear_indices(db: Database) -> None:
    """Crea índices necesarios (idempotente)."""
    db["usuarios"].create_index("email", unique=True)
    db["requerimientos"].create_index("solicitante_id")
    db["requerimientos"].create_index("tecnico_asignado_id")
    db["requerimientos"].create_index("estado")
