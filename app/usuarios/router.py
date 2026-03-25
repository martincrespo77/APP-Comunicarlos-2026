"""Router de usuarios — capa HTTP delgada sobre UsuarioService.

Responsabilidades de este módulo:
  - Recibir HTTP request, deserializar con schemas (Pydantic).
  - Llamar al servicio correspondiente.
  - Mapear excepciones de aplicación/dominio a responses HTTP.
  - Serializar la entidad de dominio mediante schemas de salida.

Lo que NO hace este módulo:
  - Lógica de negocio (vive en dominio).
  - Lógica de aplicación (vive en servicios).
  - Hashing de contraseñas (vive en deps.py).
  - Validaciones duplicadas de las que ya hace el dominio.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.auth import crear_token
from app.compartido.dominio import RolUsuario
from app.deps import UsuarioActual, get_current_user, get_usuario_service, requiere_rol
from app.usuarios.excepciones import (
    CredencialesInvalidas,
    EmailDuplicado,
    UsuarioNoEncontrado,
)
from app.usuarios.schemas import TokenOut, UsuarioAutenticarIn, UsuarioCrearIn, UsuarioOut
from app.usuarios.servicios import UsuarioService

router = APIRouter()

# ── Alias de tipo para las dependencias inyectadas ──────────────────
_Service = Annotated[UsuarioService, Depends(get_usuario_service)]
_CurrentUser = Annotated[UsuarioActual, Depends(get_current_user)]# Solo SUPERVISOR u OPERADOR pueden listar todos los usuarios
_CurrentSuperOper = Annotated[
    UsuarioActual,
    Depends(requiere_rol(RolUsuario.SUPERVISOR, RolUsuario.OPERADOR)),
]
# Solo SUPERVISOR puede desactivar
_CurrentSupervisor = Annotated[UsuarioActual, Depends(requiere_rol(RolUsuario.SUPERVISOR))]

# ═══════════════════════════════════════════════════════════
#  Endpoints públicos (sin autenticación requerida)
# ═══════════════════════════════════════════════════════════


@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    summary="Registrar nuevo usuario",
    response_description="ID del usuario creado",
)
def registrar(body: UsuarioCrearIn, service: _Service) -> dict:
    """Registra un nuevo usuario en el sistema.

    Errores posibles:
      - **409** si ya existe un usuario con el mismo email.
      - **422** si los datos violan invariantes del dominio
                (nombre vacío, email sin @, etc.).
    """
    try:
        usuario_id = service.registrar(
            nombre=body.nombre,
            email=body.email,
            rol=body.rol,
            password_plano=body.password,
        )
        return {"id": usuario_id}
    except EmailDuplicado as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc)
        )


@router.post(
    "/autenticar",
    response_model=TokenOut,
    summary="Autenticar usuario",
)
def autenticar(body: UsuarioAutenticarIn, service: _Service) -> TokenOut:
    """Verifica credenciales y retorna un JWT Bearer.

    El token contiene los claims mínimos: sub (id), rol, iat, exp.
    No expone ningún dato personal en la respuesta.

    Errores posibles:
      - **401** si el email no existe o la contraseña no coincide.
        El mensaje es idéntico en ambos casos (no se discrimina cuál
        campo es incorrecto, por seguridad).
    """
    try:
        usuario = service.autenticar(
            email=body.email,
            password_plano=body.password,
        )
        token = crear_token(usuario.id, usuario.rol)
        return TokenOut(access_token=token)
    except CredencialesInvalidas as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
            headers={"WWW-Authenticate": "Bearer"},
        )


# ═══════════════════════════════════════════════════════════
#  Endpoints protegidos (requieren usuario autenticado)
# ═══════════════════════════════════════════════════════════


@router.get(
    "/",
    response_model=list[UsuarioOut],
    summary="Listar todos los usuarios",
)
def listar(_current: _CurrentSuperOper, service: _Service) -> list[UsuarioOut]:
    """Retorna la lista completa de usuarios registrados.

    Requiere rol SUPERVISOR u OPERADOR: sólo el personal de mesa
    de ayuda necesita ver el padrón completo de usuarios.
    """
    return [UsuarioOut.desde_entidad(u) for u in service.listar()]


@router.get(
    "/{usuario_id}",
    response_model=UsuarioOut,
    summary="Obtener usuario por ID",
)
def obtener(
    usuario_id: str,
    current: _CurrentUser,
    service: _Service,
) -> UsuarioOut:
    """Retorna el detalle del usuario indicado.

    Acceso permitido a:
      - El propio usuario (cualquier rol puede ver su propio perfil).
      - SUPERVISOR y OPERADOR (gestión y asignación de tickets).

    Errores posibles:
      - **403** si el usuario intenta ver el perfil de otro sin tener rol suficiente.
      - **404** si no existe un usuario con ese ID.
    """
    _roles_con_acceso_total = (RolUsuario.SUPERVISOR, RolUsuario.OPERADOR)
    if current.id != usuario_id and current.rol not in _roles_con_acceso_total:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene permiso para ver el perfil de otro usuario.",
        )
    try:
        return UsuarioOut.desde_entidad(service.obtener(usuario_id))
    except UsuarioNoEncontrado as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.delete(
    "/{usuario_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Desactivar usuario",
)
def desactivar(
    usuario_id: str,
    _current: _CurrentSupervisor,
    service: _Service,
) -> None:
    """Desactiva el usuario indicado (baja lógica, no elimina).

    Solo SUPERVISOR puede desactivar cuentas: es una operación
    administrativa que no debe delegarse a roles operativos.

    Errores posibles:
      - **403** si el rol del usuario autenticado no es SUPERVISOR.
      - **404** si no existe un usuario con ese ID.
    """
    try:
        service.desactivar(usuario_id)
    except UsuarioNoEncontrado as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
