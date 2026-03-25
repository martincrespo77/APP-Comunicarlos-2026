"""Fábricas de dependencias para FastAPI.

Centraliza la construcción de servicios y el contexto de usuario actual.

Contiene:
  - Engine SQLAlchemy (inicialización diferida para no crear DB en tests).
  - ``get_db()`` generador que provee una sesión por request.
  - Hasher / verificador de passwords vía bcrypt.
  - ``get_usuario_service()`` y ``get_requerimiento_service()`` para ``Depends()``.
  - ``get_current_user()`` con JWT real.

Regla de sustitución:
    Solo este módulo debe cambiar cuando cambie el backend de persistencia o auth.
    Servicios, routers y dominio permanecen intactos.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Generator, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
from sqlalchemy.orm import Session, sessionmaker

from app.auth import TokenError, decodificar_token
from app.compartido.dominio import RolUsuario
from app.notificaciones.dominio import DespachadorEventos
from app.requerimientos.dominio import EstadoRequerimiento, Requerimiento
from app.requerimientos.repositorio import RepositorioRequerimiento
from app.requerimientos.servicios import RequerimientoService
from app.usuarios.dominio import Usuario
from app.usuarios.repositorio import RepositorioUsuario
from app.usuarios.servicios import UsuarioService


# ═══════════════════════════════════════════════════════════
#  Engine SQLAlchemy (inicialización diferida)
# ═══════════════════════════════════════════════════════════

# Se inicializan la primera vez que se llama a get_db(),
# no al importar el módulo: evita efectos en tests unitarios.
_engine = None
_SessionFactory: Optional[sessionmaker] = None


def _set_engine(engine) -> None:  # type: ignore[no-untyped-def]
    """Permite que el lifespan de main.py inyecte el engine en el módulo.

    Al llamarse desde el lifespan el engine ya tiene las tablas creadas,
    evitando que ``get_db()`` las recree en cada arranque.
    """
    global _engine, _SessionFactory
    from app.infraestructura.database import get_session_factory
    _engine = engine
    _SessionFactory = get_session_factory(engine)


def _ensure_engine() -> None:
    """Inicializa el engine de forma diferida si el lifespan no lo hizo.

    Ruta de fallback: cubre tests de integración que no pasan por lifespan
    y cualquier uso del módulo fuera del servidor FastAPI.
    """
    global _engine, _SessionFactory
    if _engine is None:
        from app.infraestructura.database import (
            crear_engine,
            get_session_factory,
            init_db,
        )
        _engine = crear_engine()
        init_db(_engine)
        _SessionFactory = get_session_factory(_engine)


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency: provee una sesión SQLAlchemy por request."""
    _ensure_engine()
    if _SessionFactory is None:
        raise RuntimeError(
            "_SessionFactory no fue inicializado. "
            "Verificar que _ensure_engine() se ejecutó correctamente "
            "o que _set_engine() fue llamado desde el lifespan."
        )
    db = _SessionFactory()
    try:
        yield db
    finally:
        db.close()


_despachador: DespachadorEventos = DespachadorEventos()


# ═══════════════════════════════════════════════════════════
#  Hashing de contraseñas (bcrypt via passlib)
# ═══════════════════════════════════════════════════════════

_crypt = CryptContext(schemes=["bcrypt"], deprecated="auto")


def _hasher(password: str) -> str:
    """Genera un hash bcrypt de la contraseña."""
    return _crypt.hash(password)


def _verificador(password: str, hash_: str) -> bool:
    """Verifica una contraseña contra su hash bcrypt."""
    return _crypt.verify(password, hash_)


# ═══════════════════════════════════════════════════════════
#  FastAPI dependency factories
# ═══════════════════════════════════════════════════════════


def get_usuario_service(db: Session = Depends(get_db)) -> UsuarioService:
    """Retorna el servicio de usuarios con repositorio SQL inyectado."""
    from app.infraestructura.repo_usuarios import RepositorioUsuarioSQL
    return UsuarioService(RepositorioUsuarioSQL(db), _hasher, _verificador)


def get_requerimiento_service(db: Session = Depends(get_db)) -> RequerimientoService:
    """Retorna el servicio de requerimientos con repositorio SQL inyectado."""
    from app.infraestructura.repo_requerimientos import RepositorioRequerimientoSQL
    return RequerimientoService(RepositorioRequerimientoSQL(db), _despachador)


# ═══════════════════════════════════════════════════════════
#  Contexto de usuario autenticado (auth placeholder → JWT)
# ═══════════════════════════════════════════════════════════


@dataclass
class UsuarioActual:
    """Contexto del usuario autenticado disponible en cada request.

    Los campos se extraen de los claims del JWT (``sub`` → id, ``rol`` → rol).
    """

    id: str
    rol: RolUsuario


# ─── OAuth2 scheme ────────────────────────────────────────────────────────────
# tokenUrl apunta al endpoint de login usado por Swagger UI.
_oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/usuarios/autenticar")


def get_current_user(
    token: str = Depends(_oauth2_scheme),
    service: UsuarioService = Depends(get_usuario_service),
) -> UsuarioActual:
    """Extrae y valida el token JWT del header ``Authorization: Bearer``.

    Flujo:
      1. ``OAuth2PasswordBearer`` extrae el token del header.
      2. ``decodificar_token`` verifica firma y expiración.
      3. Se carga el usuario desde el repositorio con el ``sub`` del token.
      4. Se verifica que el usuario esté activo.

    Raises (HTTP)
    -------------
    401
        Token inválido, expirado, o ``sub`` no corresponde a ningún usuario.
        Se devuelve 401 (no 403) porque en los tres casos el cliente debe
        re-autenticarse con credenciales válidas.
    403
        Usuario existente y token válido, pero la cuenta está desactivada.
        Se usa 403 —no 401— porque re-autenticarse no cambiará el estado
        de la cuenta: la identidad está confirmada pero el acceso prohibido.
    """
    from app.usuarios.excepciones import UsuarioNoEncontrado

    try:
        payload = decodificar_token(token)
    except TokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o expirado.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        usuario = service.obtener(payload["sub"])
    except UsuarioNoEncontrado:
        # sub no corresponde a ningún usuario (ej.: usuario eliminado tras emitir el token)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o expirado.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not usuario.activo:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cuenta desactivada.",
        )

    return UsuarioActual(id=usuario.id, rol=usuario.rol)


def requiere_rol(*roles_permitidos: RolUsuario) -> Callable[..., UsuarioActual]:
    """Factoría de dependencias FastAPI que verifica el rol del usuario.

    Uso en un endpoint::

        @router.get("/", dependencies=[Depends(requiere_rol(RolUsuario.SUPERVISOR))])

    O para obtener el usuario verificado::

        @router.delete("/{id}")
        def borrar(current: Annotated[UsuarioActual, Depends(requiere_rol(RolUsuario.SUPERVISOR))]):
            ...

    Raises (HTTP)
    -------------
    403
        Si el rol del usuario autenticado no está en ``roles_permitidos``.
    """

    def verificar(
        current: UsuarioActual = Depends(get_current_user),
    ) -> UsuarioActual:
        if current.rol not in roles_permitidos:
            nombres = [r.value for r in roles_permitidos]
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Rol insuficiente. Requerido: {nombres}.",
            )
        return current

    return verificar
