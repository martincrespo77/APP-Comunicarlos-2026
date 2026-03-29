"""Fábricas de dependencias para FastAPI.

Centraliza la construcción de servicios y el contexto de usuario actual.

Contiene:
  - ``get_usuario_service()`` y ``get_requerimiento_service()`` para ``Depends()``.
  - Hasher / verificador de passwords vía bcrypt.
  - ``get_current_user()`` con JWT real.

Regla de sustitución:
    Solo este módulo debe cambiar cuando cambie el backend de persistencia o auth.
    Servicios, routers y dominio permanecen intactos.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext

from app.auth import TokenError, decodificar_token
from app.compartido.dominio import RolUsuario
from app.infraestructura.database import get_database
from app.notificaciones.dominio import DespachadorEventos
from app.requerimientos.dominio import EstadoRequerimiento, Requerimiento
from app.requerimientos.repositorio import RepositorioRequerimiento
from app.requerimientos.servicios import RequerimientoService
from app.usuarios.dominio import Usuario
from app.usuarios.repositorio import RepositorioUsuario
from app.usuarios.servicios import UsuarioService


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


def get_usuario_service() -> UsuarioService:
    """Retorna el servicio de usuarios con repositorio MongoDB inyectado."""
    from app.infraestructura.repo_usuarios import RepositorioUsuarioMongo
    db = get_database()
    return UsuarioService(RepositorioUsuarioMongo(db), _hasher, _verificador)


def get_requerimiento_service() -> RequerimientoService:
    """Retorna el servicio de requerimientos con repositorio MongoDB inyectado."""
    from app.infraestructura.repo_requerimientos import RepositorioRequerimientoMongo
    db = get_database()
    return RequerimientoService(RepositorioRequerimientoMongo(db), _despachador)


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
