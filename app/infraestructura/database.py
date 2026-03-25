"""Configuración del motor SQLAlchemy.

Centraliza la creación del engine, la clase Base para los modelos ORM
y la función ``init_db`` que crea tablas al arrancar.

Diseño:
  - Engine configurable vía ``DATABASE_URL`` en ``app.config``.
  - Un único ``Base`` compartido por todos los modelos ORM del proyecto.
  - ``init_db`` es idempotente: CREATE TABLE IF NOT EXISTS.
  - ``get_session_factory`` retorna un ``sessionmaker`` listo para usar.
"""

from __future__ import annotations

from sqlalchemy import create_engine as _sa_create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker


# ──────────────────────────────────────────────────────────────────────────────
#  Base ORM compartida
# ──────────────────────────────────────────────────────────────────────────────


class Base(DeclarativeBase):
    """Clase base para todos los modelos ORM del proyecto."""


# ──────────────────────────────────────────────────────────────────────────────
#  Factories
# ──────────────────────────────────────────────────────────────────────────────


def crear_engine(database_url: str | None = None) -> Engine:
    """Crea el engine SQLAlchemy a partir de la configuración.

    Args:
        database_url: URL de conexión.  Si es ``None``, se lee de
            ``app.config.get_settings().DATABASE_URL``.

    Notes:
        - Para SQLite se agrega ``check_same_thread=False`` para que el
          engine pueda usarse desde múltiples threads (necesario en FastAPI).
        - ``echo=False`` en producción; cambiar a ``True`` para depurar SQL.
    """
    if database_url is None:
        from app.config import get_settings
        database_url = get_settings().DATABASE_URL

    connect_args: dict = {}
    if database_url.startswith("sqlite"):
        connect_args["check_same_thread"] = False

    return _sa_create_engine(database_url, connect_args=connect_args, echo=False)


def init_db(engine: Engine) -> None:
    """Crea todas las tablas definidas en los modelos ORM (idempotente).

    Debe llamarse al arrancar la aplicación (lo hace el lifespan de main.py).

    Estrategia MVP — ``create_all``:
        Esta función usa ``Base.metadata.create_all``, que crea las tablas
        si NO existen pero NO modifica columnas, índices ni restricciones
        existentes.  Es correcta para desarrollo y para el primer deploy.

        LIMITACIÓN IMPORTANTE:
        Ante cualquier cambio de esquema posterior (nueva columna, renombrado,
        cambio de tipo) ``create_all`` no ejecuta nada.  Para producción con
        datos persistentes se debe instalar Alembic y reemplazar esta función
        por ``alembic upgrade head``.

        Pasos para migrar a Alembic cuando sea necesario:
            pip install alembic
            alembic init alembic
            # apuntar env.py a app.infraestructura.database.Base
            alembic revision --autogenerate -m "initial"
            alembic upgrade head

        Ver: https://alembic.sqlalchemy.org/en/latest/tutorial.html
    """
    # Importar para registrar los modelos en Base.metadata
    from app.infraestructura import modelos_orm  # noqa: F401
    Base.metadata.create_all(bind=engine)


def get_session_factory(engine: Engine) -> sessionmaker[Session]:
    """Retorna un factory de sesiones ligado al engine dado."""
    return sessionmaker(bind=engine, autocommit=False, autoflush=False)
