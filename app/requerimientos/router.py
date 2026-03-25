"""Router de requerimientos — capa HTTP delgada sobre RequerimientoService.

Responsabilidades de este módulo:
  - Recibir HTTP request, deserializar con schemas (Pydantic).
  - Llamar al servicio correspondiente.
  - Mapear excepciones de aplicación/dominio a responses HTTP.
  - Serializar entidades de dominio mediante schemas de salida.

El actor_id y rol_actor para operaciones de ciclo de vida se obtienen
de ``get_current_user`` (ver ``app.deps``).  Cuando se integre JWT,
solo cambia esa función, no los endpoints.

Mapeo de excepciones:
  ─────────────────────────────────────────────────────
  RequerimientoNoEncontrado   →  404 Not Found
  OperacionNoAutorizada       →  403 Forbidden
  TransicionEstadoInvalida    →  422 Unprocessable Entity
  RequerimientoError (base)   →  422 Unprocessable Entity
  ValueError (dominio)        →  422 Unprocessable Entity
  ─────────────────────────────────────────────────────
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.compartido.dominio import RolUsuario
from app.deps import UsuarioActual, get_current_user, get_requerimiento_service, requiere_rol
from app.requerimientos.dominio import EstadoRequerimiento
from app.requerimientos.excepciones import (
    OperacionNoAutorizada,
    RequerimientoError,
    TransicionEstadoInvalida,
)
from app.requerimientos.excepciones_aplicacion import RequerimientoNoEncontrado
from app.requerimientos.schemas import (
    AsignarTecnicoIn,
    ComentarioAgregarIn,
    DerivarRequerimientoIn,
    IncidenteCrearIn,
    RequerimientoOut,
    SolicitudCrearIn,
)
from app.requerimientos.servicios import RequerimientoService

router = APIRouter()

# ── Alias de tipo para las dependencias inyectadas ──────────────────
_Service = Annotated[RequerimientoService, Depends(get_requerimiento_service)]
_CurrentUser = Annotated[UsuarioActual, Depends(get_current_user)]# Solo OPERADOR asigna técnicos
_CurrentOperador = Annotated[UsuarioActual, Depends(requiere_rol(RolUsuario.OPERADOR))]
# Solo TECNICO ejecuta trabajo
_CurrentTecnico = Annotated[UsuarioActual, Depends(requiere_rol(RolUsuario.TECNICO))]

# ── Helper interno ────────────────────────────────────────────────────

def _raise_ciclo_vida(exc: Exception) -> None:
    """Centraliza el mapeo de excepciones comunes de ciclo de vida."""
    if isinstance(exc, RequerimientoNoEncontrado):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    if isinstance(exc, OperacionNoAutorizada):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    if isinstance(exc, (TransicionEstadoInvalida, RequerimientoError, ValueError)):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc)
        )
    raise exc  # excepción no esperada: burbujea al handler global


# ═══════════════════════════════════════════════════════════
#  Creación de requerimientos
# ═══════════════════════════════════════════════════════════


@router.post(
    "/incidentes",
    status_code=status.HTTP_201_CREATED,
    summary="Abrir incidente",
    response_description="ID del incidente creado",
)
def crear_incidente(body: IncidenteCrearIn, current: _CurrentUser, service: _Service) -> dict:
    """Abre un nuevo incidente en el sistema.

    Cualquier usuario autenticado puede abrir un incidente.
    Si el rol es SOLICITANTE, el ``solicitante_id`` se fija
    automáticamente al id del usuario autenticado (no puede
    crear tickets a nombre de otro).

    Errores posibles:
      - **422** si título o descripción están vacíos.
    """
    solicitante_id = (
        current.id
        if current.rol == RolUsuario.SOLICITANTE
        else body.solicitante_id
    )
    try:
        req_id = service.crear_incidente(
            titulo=body.titulo,
            descripcion=body.descripcion,
            solicitante_id=solicitante_id,
            urgencia=body.urgencia,
            categoria=body.categoria,
        )
        return {"id": req_id}
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc)
        )


@router.post(
    "/solicitudes",
    status_code=status.HTTP_201_CREATED,
    summary="Abrir solicitud de servicio",
    response_description="ID de la solicitud creada",
)
def crear_solicitud(body: SolicitudCrearIn, current: _CurrentUser, service: _Service) -> dict:
    """Abre una nueva solicitud de servicio.

    Igual que para incidentes: si el rol es SOLICITANTE, el
    ``solicitante_id`` se fija al id del usuario autenticado.

    Errores posibles:
      - **422** si título o descripción están vacíos.
    """
    solicitante_id = (
        current.id
        if current.rol == RolUsuario.SOLICITANTE
        else body.solicitante_id
    )
    try:
        req_id = service.crear_solicitud(
            titulo=body.titulo,
            descripcion=body.descripcion,
            solicitante_id=solicitante_id,
            categoria=body.categoria,
        )
        return {"id": req_id}
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc)
        )


# ═══════════════════════════════════════════════════════════
#  Consultas
# ═══════════════════════════════════════════════════════════


@router.get(
    "/",
    response_model=list[RequerimientoOut],
    summary="Listar requerimientos",
)
def listar(
    current: _CurrentUser,
    service: _Service,
    solicitante_id: str | None = Query(default=None, description="Filtrar por solicitante"),
    tecnico_id: str | None = Query(default=None, description="Filtrar por técnico asignado"),
    estado: EstadoRequerimiento | None = Query(default=None, description="Filtrar por estado"),
) -> list[RequerimientoOut]:
    """Retorna requerimientos con visibilidad según el rol del usuario autenticado.

    - **SOLICITANTE**: solo ve sus propios requerimientos (filtros de query ignorados).
    - **TECNICO**: solo ve los requerimientos que tiene asignados (filtros ignorados).
    - **OPERADOR / SUPERVISOR**: visibilidad total; los parámetros de query aplican
      el filtro indicado (``solicitante_id`` > ``tecnico_id`` > ``estado``; sin
      filtros retorna todos).

    Tanto SOLICITANTE como TECNICO pueden añadir el filtro ``estado`` dentro
    de su propia visibilidad.
    """
    rol = current.rol

    if rol == RolUsuario.SOLICITANTE:
        reqs = service.listar_por_solicitante(current.id)
        if estado:
            reqs = [r for r in reqs if r.estado == estado]
    elif rol == RolUsuario.TECNICO:
        reqs = service.listar_por_tecnico(current.id)
        if estado:
            reqs = [r for r in reqs if r.estado == estado]
    else:  # OPERADOR / SUPERVISOR: visibilidad total
        if solicitante_id:
            reqs = service.listar_por_solicitante(solicitante_id)
        elif tecnico_id:
            reqs = service.listar_por_tecnico(tecnico_id)
        elif estado:
            reqs = service.listar_por_estado(estado)
        else:
            reqs = service.listar()

    return [RequerimientoOut.desde_entidad(r) for r in reqs]


@router.get(
    "/{requerimiento_id}",
    response_model=RequerimientoOut,
    summary="Obtener requerimiento por ID",
)
def obtener(
    requerimiento_id: str,
    current: _CurrentUser,
    service: _Service,
) -> RequerimientoOut:
    """Retorna el detalle completo del requerimiento indicado.

    Visibilidad por rol:
      - **OPERADOR / SUPERVISOR**: acceso a cualquier requerimiento.
      - **SOLICITANTE**: solo si es el creador del requerimiento.
      - **TECNICO**: solo si tiene el requerimiento asignado.

    Errores posibles:
      - **403** el requerimiento existe pero el usuario no tiene acceso.
      - **404** si no existe un requerimiento con ese ID.
    """
    try:
        req = service.obtener(requerimiento_id)
    except RequerimientoNoEncontrado as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))

    rol = current.rol
    if rol == RolUsuario.SOLICITANTE and req.solicitante_id != current.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo puede ver sus propios requerimientos.",
        )
    if rol == RolUsuario.TECNICO and req.tecnico_asignado_id != current.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo puede ver requerimientos que tenga asignados.",
        )

    return RequerimientoOut.desde_entidad(req)


# ═══════════════════════════════════════════════════════════
#  Ciclo de vida (transiciones de estado)
# ═══════════════════════════════════════════════════════════


@router.post(
    "/{requerimiento_id}/asignar",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Asignar técnico a un requerimiento",
)
def asignar_tecnico(
    requerimiento_id: str,
    body: AsignarTecnicoIn,
    current: _CurrentOperador,
    service: _Service,
) -> None:
    """Asigna o reasigna un técnico al requerimiento.

    Solo OPERADOR puede asignar técnicos (regla del dominio y del router).

    Errores posibles:
      - **404** requerimiento no encontrado.
      - **403** el actor no tiene permiso para asignar.
      - **422** transición de estado inválida.
    """
    try:
        service.asignar_tecnico(
            requerimiento_id=requerimiento_id,
            tecnico_id=body.tecnico_id,
            actor_id=current.id,
            rol_actor=current.rol,
        )
    except Exception as exc:
        _raise_ciclo_vida(exc)


@router.post(
    "/{requerimiento_id}/iniciar",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Iniciar trabajo en un requerimiento",
)
def iniciar_trabajo(
    requerimiento_id: str,
    current: _CurrentTecnico,
    service: _Service,
) -> None:
    """El técnico asignado marca el requerimiento como en progreso.

    El ID del técnico se toma del usuario autenticado (``current.id``).

    Errores posibles:
      - **404** requerimiento no encontrado.
      - **403** el usuario no es el técnico asignado.
      - **422** transición de estado inválida.
    """
    try:
        service.iniciar_trabajo(
            requerimiento_id=requerimiento_id,
            tecnico_id=current.id,
        )
    except Exception as exc:
        _raise_ciclo_vida(exc)


@router.post(
    "/{requerimiento_id}/resolver",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Resolver un requerimiento",
)
def resolver(
    requerimiento_id: str,
    current: _CurrentTecnico,
    service: _Service,
) -> None:
    """El técnico asignado marca el requerimiento como resuelto.

    Errores posibles:
      - **404** requerimiento no encontrado.
      - **403** el usuario no es el técnico asignado.
      - **422** transición de estado inválida.
    """
    try:
        service.resolver(
            requerimiento_id=requerimiento_id,
            tecnico_id=current.id,
        )
    except Exception as exc:
        _raise_ciclo_vida(exc)


@router.post(
    "/{requerimiento_id}/derivar",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Derivar requerimiento a otro técnico",
)
def derivar(
    requerimiento_id: str,
    body: DerivarRequerimientoIn,
    current: _CurrentTecnico,
    service: _Service,
) -> None:
    """El técnico asignado deriva el requerimiento a otro técnico.

    El ID del técnico origen se toma del usuario autenticado.

    Errores posibles:
      - **404** requerimiento no encontrado.
      - **403** el usuario no es el técnico asignado.
      - **422** motivo vacío, mismo técnico, o estado no permite derivar.
    """
    try:
        service.derivar(
            requerimiento_id=requerimiento_id,
            tecnico_origen_id=current.id,
            tecnico_destino_id=body.tecnico_destino_id,
            motivo=body.motivo,
        )
    except Exception as exc:
        _raise_ciclo_vida(exc)


@router.post(
    "/{requerimiento_id}/comentarios",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Agregar comentario a un requerimiento",
)
def agregar_comentario(
    requerimiento_id: str,
    body: ComentarioAgregarIn,
    current: _CurrentUser,
    service: _Service,
) -> None:
    """Agrega un comentario al requerimiento.

    El autor y su rol se toman del usuario autenticado.
    Un comentario sobre un requerimiento resuelto puede reabrirlo
    automáticamente (lógica del dominio).

    Errores posibles:
      - **404** requerimiento no encontrado.
      - **403** el rol no tiene permiso para comentar.
      - **422** contenido vacío.
    """
    try:
        service.agregar_comentario(
            requerimiento_id=requerimiento_id,
            autor_id=current.id,
            rol_autor=current.rol,
            contenido=body.contenido,
        )
    except Exception as exc:
        _raise_ciclo_vida(exc)
