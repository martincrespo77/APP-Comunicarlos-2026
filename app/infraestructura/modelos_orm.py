"""Modelos ORM (tablas SQLAlchemy).

Estos modelos son la representación de persistencia de las entidades de dominio.
No contienen lógica de negocio: solo definen el esquema relacional.

Separación deliberada:
  - ``UsuarioORM`` ≠ ``Usuario`` de dominio.
  - ``RequerimientoORM`` ≠ ``Requerimiento`` de dominio.
  Los repositorios son los únicos responsables de traducir entre ambas capas.

Esquema:
  ┌─────────────┐       ┌──────────────────────┐
  │  usuarios   │       │   requerimientos     │
  └─────────────┘       └──────────────────────┘
                                    │
                       ┌────────────┴────────────┐
                       ▼                         ▼
                  ┌─────────┐           ┌──────────────┐
                  │ eventos │           │ comentarios  │
                  └─────────┘           └──────────────┘
"""

from __future__ import annotations

import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column

from app.infraestructura.database import Base


# ──────────────────────────────────────────────────────────────────────────────
#  Tabla: usuarios
# ──────────────────────────────────────────────────────────────────────────────


class UsuarioORM(Base):
    """Mapa relacional de la entidad Usuario."""

    __tablename__ = "usuarios"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    nombre: Mapped[str] = mapped_column(String, nullable=False)
    email: Mapped[str] = mapped_column(String, nullable=False, unique=True, index=True)
    rol: Mapped[str] = mapped_column(String, nullable=False)
    password_hash: Mapped[str] = mapped_column(String, nullable=False)
    activo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    fecha_creacion: Mapped[datetime.datetime] = mapped_column(DateTime, nullable=False)
    ultimo_acceso: Mapped[Optional[datetime.datetime]] = mapped_column(
        DateTime, nullable=True
    )

    def __repr__(self) -> str:
        return f"UsuarioORM(id={self.id!r}, email={self.email!r})"


# ──────────────────────────────────────────────────────────────────────────────
#  Tabla: requerimientos
# ──────────────────────────────────────────────────────────────────────────────


class RequerimientoORM(Base):
    """Mapa relacional del agregado Requerimiento.

    ``tipo`` discrimina entre Incidente y Solicitud.
    ``urgencia`` es NULL para solicitudes.
    ``categoria`` almacena la categoría de incidente O de solicitud;
    el tipo correcto se determina por ``tipo``.
    """

    __tablename__ = "requerimientos"
    __table_args__ = (
        Index("ix_req_solicitante", "solicitante_id"),
        Index("ix_req_tecnico", "tecnico_asignado_id"),
    )

    id: Mapped[str] = mapped_column(String, primary_key=True)
    tipo: Mapped[str] = mapped_column(String, nullable=False)
    titulo: Mapped[str] = mapped_column(String, nullable=False)
    descripcion: Mapped[str] = mapped_column(String, nullable=False)
    estado: Mapped[str] = mapped_column(String, nullable=False)
    solicitante_id: Mapped[str] = mapped_column(String, nullable=False)
    operador_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    tecnico_asignado_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    urgencia: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    categoria: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    fecha_creacion: Mapped[datetime.datetime] = mapped_column(DateTime, nullable=False)
    fecha_actualizacion: Mapped[datetime.datetime] = mapped_column(
        DateTime, nullable=False
    )

    def __repr__(self) -> str:
        return (
            f"RequerimientoORM(id={self.id!r}, tipo={self.tipo!r}, "
            f"estado={self.estado!r})"
        )


# ──────────────────────────────────────────────────────────────────────────────
#  Tabla: eventos  (append-only — auditoría)
# ──────────────────────────────────────────────────────────────────────────────


class EventoORM(Base):
    """Registro de auditoría de un paso en el ciclo de vida."""

    __tablename__ = "eventos"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    requerimiento_id: Mapped[str] = mapped_column(
        String, ForeignKey("requerimientos.id", ondelete="CASCADE"), nullable=False, index=True
    )
    tipo: Mapped[str] = mapped_column(String, nullable=False)
    actor_id: Mapped[str] = mapped_column(String, nullable=False)
    detalle: Mapped[str] = mapped_column(String, nullable=False)
    fecha: Mapped[datetime.datetime] = mapped_column(DateTime, nullable=False)


# ──────────────────────────────────────────────────────────────────────────────
#  Tabla: comentarios  (append-only)
# ──────────────────────────────────────────────────────────────────────────────


class ComentarioORM(Base):
    """Comentario registrado sobre un requerimiento."""

    __tablename__ = "comentarios"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    requerimiento_id: Mapped[str] = mapped_column(
        String, ForeignKey("requerimientos.id", ondelete="CASCADE"), nullable=False, index=True
    )
    autor_id: Mapped[str] = mapped_column(String, nullable=False)
    rol_autor: Mapped[str] = mapped_column(String, nullable=False)
    contenido: Mapped[str] = mapped_column(String, nullable=False)
    fecha: Mapped[datetime.datetime] = mapped_column(DateTime, nullable=False)
