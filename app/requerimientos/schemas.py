"""Schemas (DTOs) del módulo de requerimientos.

Esta capa es la única que depende de Pydantic.
El dominio (dominio.py) y los servicios (servicios.py) nunca importan
nada de este módulo.

Convención:
  - Sufijo ``In``  → datos que entran al sistema (request / input).
  - Sufijo ``Out`` → datos que salen del sistema (response / output).
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

from app.compartido.dominio import RolUsuario
from app.requerimientos.dominio import (
    CategoriaIncidente,
    CategoriaSolicitud,
    EstadoRequerimiento,
    Incidente,
    Requerimiento,
    TipoEvento,
    TipoRequerimiento,
    Urgencia,
)


# ═══════════════════════════════════════════════════════════
#  SCHEMAS DE ENTRADA
# ═══════════════════════════════════════════════════════════


class IncidenteCrearIn(BaseModel):
    """Datos para abrir un nuevo incidente."""

    titulo: str
    descripcion: str
    solicitante_id: str
    urgencia: Urgencia
    categoria: CategoriaIncidente


class SolicitudCrearIn(BaseModel):
    """Datos para abrir una nueva solicitud de servicio."""

    titulo: str
    descripcion: str
    solicitante_id: str
    categoria: CategoriaSolicitud


class AsignarTecnicoIn(BaseModel):
    """Técnico a asignar a un requerimiento."""

    tecnico_id: str


class DerivarRequerimientoIn(BaseModel):
    """Datos para derivar un requerimiento a otro técnico."""

    tecnico_destino_id: str
    motivo: str


class ComentarioAgregarIn(BaseModel):
    """Contenido del comentario a agregar."""

    contenido: str


# ═══════════════════════════════════════════════════════════
#  SCHEMAS DE SALIDA
# ═══════════════════════════════════════════════════════════


class EventoOut(BaseModel):
    """Representación pública de un evento de auditoría."""

    id: str
    tipo: TipoEvento
    actor_id: str
    detalle: str
    fecha: datetime

    @classmethod
    def desde_entidad(cls, evento) -> "EventoOut":
        return cls(
            id=evento.id,
            tipo=evento.tipo,
            actor_id=evento.actor_id,
            detalle=evento.detalle,
            fecha=evento.fecha,
        )


class ComentarioOut(BaseModel):
    """Representación pública de un comentario."""

    id: str
    autor_id: str
    rol_autor: RolUsuario
    contenido: str
    fecha: datetime

    @classmethod
    def desde_entidad(cls, comentario) -> "ComentarioOut":
        return cls(
            id=comentario.id,
            autor_id=comentario.autor_id,
            rol_autor=comentario.rol_autor,
            contenido=comentario.contenido,
            fecha=comentario.fecha,
        )


class RequerimientoOut(BaseModel):
    """Representación pública de un requerimiento (incidente o solicitud).

    Los campos ``urgencia``, ``categoria_incidente`` y ``categoria_solicitud``
    son opcionales porque dependen del tipo concreto:
      - ``Incidente`` tiene ``urgencia`` y ``categoria_incidente``.
      - ``Solicitud`` tiene ``categoria_solicitud``.
    """

    id: str
    titulo: str
    descripcion: str
    tipo: TipoRequerimiento
    estado: EstadoRequerimiento
    solicitante_id: str
    operador_id: str | None
    tecnico_asignado_id: str | None
    fecha_creacion: datetime
    fecha_actualizacion: datetime
    urgencia: Urgencia | None = None
    categoria_incidente: CategoriaIncidente | None = None
    categoria_solicitud: CategoriaSolicitud | None = None
    comentarios: list[ComentarioOut] = []
    eventos: list[EventoOut] = []

    @classmethod
    def desde_entidad(cls, req: Requerimiento) -> "RequerimientoOut":
        """Mapea la entidad de dominio al DTO de salida."""
        urgencia = None
        categoria_incidente = None
        categoria_solicitud = None

        if isinstance(req, Incidente):
            urgencia = req.urgencia
            categoria_incidente = req.categoria
        else:
            # Solicitud
            categoria_solicitud = req.categoria

        return cls(
            id=req.id,
            titulo=req.titulo,
            descripcion=req.descripcion,
            tipo=req.tipo,
            estado=req.estado,
            solicitante_id=req.solicitante_id,
            operador_id=req.operador_id,
            tecnico_asignado_id=req.tecnico_asignado_id,
            fecha_creacion=req.fecha_creacion,
            fecha_actualizacion=req.fecha_actualizacion,
            urgencia=urgencia,
            categoria_incidente=categoria_incidente,
            categoria_solicitud=categoria_solicitud,
            comentarios=[ComentarioOut.desde_entidad(c) for c in req.comentarios],
            eventos=[EventoOut.desde_entidad(e) for e in req.eventos],
        )
