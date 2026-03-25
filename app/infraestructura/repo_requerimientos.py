"""Implementación SQLAlchemy del repositorio de requerimientos.

Traduce entre las entidades de dominio (``Incidente``, ``Solicitud``, value
objects ``Evento``, ``Comentario``) y los modelos ORM correspondientes.

Decisión de diseño — Anti-corrupción layer:
    El dominio usa entidades con atributos privados (``_eventos``,
    ``_comentarios``, ``_eventos_dominio``).  Para reconstruir la entidad
    desde la base de datos sin contaminar el dominio (no se agrega ningún
    método al dominio), el repositorio asigna directamente esos atributos
    privados tras construir la entidad con ``registrar_creacion=False``.

    Python no obliga el acceso privado en tiempo de ejecución para atributos
    con un único guión (``_attr``); es solo una convención.  Esto es una
    técnica estándar en capas de persistencia que deben reconstruir objetos
    ricos sin duplicar eventos de auditoría.

    Se evita el uso de ``__setattr__`` o ``__dict__`` directamente:
    la asignación ``obj._attr = valor`` es Python idiomático para esto.

Guarantía de consistencia:
    Al guardar, la tabla ``requerimientos`` se actualiza con ``merge()``
    y las tablas ``eventos`` / ``comentarios`` se sincronizan con un
    delete-and-reinsert.  Es seguro porque el dominio garantiza que
    eventos y comentarios son append-only (nunca se modifican ni borran).
    La re-inserción es idempotente respecto a la vista de negocio.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Optional

from sqlalchemy.orm import Session

from app.compartido.dominio import RolUsuario
from app.infraestructura.modelos_orm import ComentarioORM, EventoORM, RequerimientoORM
from app.requerimientos.dominio import (
    CategoriaIncidente,
    CategoriaSolicitud,
    Comentario,
    EstadoRequerimiento,
    Evento,
    Incidente,
    Requerimiento,
    Solicitud,
    TipoEvento,
    TipoRequerimiento,
    Urgencia,
)
from app.requerimientos.repositorio import RepositorioRequerimiento


# ──────────────────────────────────────────────────────────────────────────────
#  Helpers de traducción  ORM → Dominio
# ──────────────────────────────────────────────────────────────────────────────


def _evento_orm_a_dominio(row: EventoORM) -> Evento:
    return Evento(
        tipo=TipoEvento(row.tipo),
        actor_id=row.actor_id,
        detalle=row.detalle,
        id=row.id,
        fecha=row.fecha,
    )


def _comentario_orm_a_dominio(row: ComentarioORM) -> Comentario:
    return Comentario(
        autor_id=row.autor_id,
        rol_autor=RolUsuario(row.rol_autor),
        contenido=row.contenido,
        id=row.id,
        fecha=row.fecha,
    )


def _requerimiento_orm_a_dominio(
    row: RequerimientoORM,
    eventos_rows: list[EventoORM],
    comentarios_rows: list[ComentarioORM],
) -> Requerimiento:
    """Reconstruye el agregado Requerimiento desde sus filas ORM.

    Usa ``registrar_creacion=False`` para evitar duplicar el evento CREACION.
    Luego restaura los atributos privados de historial directamente.
    """
    estado = EstadoRequerimiento(row.estado)

    if TipoRequerimiento(row.tipo) == TipoRequerimiento.INCIDENTE:
        req: Requerimiento = Incidente(
            titulo=row.titulo,
            descripcion=row.descripcion,
            solicitante_id=row.solicitante_id,
            urgencia=Urgencia(row.urgencia),
            categoria=CategoriaIncidente(row.categoria),
            id=row.id,
            estado=estado,
            operador_id=row.operador_id,
            tecnico_asignado_id=row.tecnico_asignado_id,
            fecha_creacion=row.fecha_creacion,
            fecha_actualizacion=row.fecha_actualizacion,
            registrar_creacion=False,  # no duplicar en reconstrucción
        )
    else:
        req = Solicitud(
            titulo=row.titulo,
            descripcion=row.descripcion,
            solicitante_id=row.solicitante_id,
            categoria=CategoriaSolicitud(row.categoria),
            id=row.id,
            estado=estado,
            operador_id=row.operador_id,
            tecnico_asignado_id=row.tecnico_asignado_id,
            fecha_creacion=row.fecha_creacion,
            fecha_actualizacion=row.fecha_actualizacion,
            registrar_creacion=False,
        )

    # Restaurar historial de auditoría (atributos privados convencionales)
    req._eventos = [_evento_orm_a_dominio(e) for e in eventos_rows]
    req._comentarios = [_comentario_orm_a_dominio(c) for c in comentarios_rows]
    req._eventos_dominio = []  # ya fueron despachados al persistir

    return req


# ──────────────────────────────────────────────────────────────────────────────
#  Helpers de traducción  Dominio → ORM
# ──────────────────────────────────────────────────────────────────────────────


def _requerimiento_dominio_a_orm(req: Requerimiento) -> RequerimientoORM:
    """Crea el ORM raíz a partir de la entidad de dominio."""
    es_incidente = req.tipo == TipoRequerimiento.INCIDENTE

    return RequerimientoORM(
        id=req.id,
        tipo=req.tipo.value,
        titulo=req.titulo,
        descripcion=req.descripcion,
        estado=req.estado.value,
        solicitante_id=req.solicitante_id,
        operador_id=req.operador_id,
        tecnico_asignado_id=req.tecnico_asignado_id,
        urgencia=req.urgencia.value if es_incidente else None,  # type: ignore[attr-defined]
        categoria=(
            req.categoria.value  # type: ignore[attr-defined]
        ),
        fecha_creacion=req.fecha_creacion,
        fecha_actualizacion=req.fecha_actualizacion,
    )


def _eventos_dominio_a_orm(req: Requerimiento) -> list[EventoORM]:
    return [
        EventoORM(
            id=ev.id,
            requerimiento_id=req.id,
            tipo=ev.tipo.value,
            actor_id=ev.actor_id,
            detalle=ev.detalle,
            fecha=ev.fecha,
        )
        for ev in req.eventos
    ]


def _comentarios_dominio_a_orm(req: Requerimiento) -> list[ComentarioORM]:
    return [
        ComentarioORM(
            id=co.id,
            requerimiento_id=req.id,
            autor_id=co.autor_id,
            rol_autor=co.rol_autor.value,
            contenido=co.contenido,
            fecha=co.fecha,
        )
        for co in req.comentarios
    ]


# ──────────────────────────────────────────────────────────────────────────────
#  Repositorio concreto
# ──────────────────────────────────────────────────────────────────────────────


class RepositorioRequerimientoSQL(RepositorioRequerimiento):
    """Repositorio de requerimientos respaldado por SQLAlchemy.

    Estrategia de persistencia de colecciones:
        eventos y comentarios son append-only en el dominio, pero por
        simplicidad se re-sincronizan completos en cada ``guardar``:
        se borran los hijos del requerimiento y se reinsertan todos.
        Esto es seguro porque:
        - El dominio nunca elimina ni modifica eventos/comentarios.
        - La operación es idempotente.
        - Con CASCADE DELETE, los hijos se eliminan automáticamente.
    """

    def __init__(self, session: Session) -> None:
        self._session = session

    # ── Escritura ──────────────────────────────────────────────────────────

    def guardar(self, requerimiento: Requerimiento) -> None:
        # 1. Upsert del requerimiento raíz
        orm_req = _requerimiento_dominio_a_orm(requerimiento)
        self._session.merge(orm_req)

        # 2. Sincronizar eventos (re-insertar)
        self._session.query(EventoORM).filter(
            EventoORM.requerimiento_id == requerimiento.id
        ).delete(synchronize_session=False)
        for ev_orm in _eventos_dominio_a_orm(requerimiento):
            self._session.add(ev_orm)

        # 3. Sincronizar comentarios (re-insertar)
        self._session.query(ComentarioORM).filter(
            ComentarioORM.requerimiento_id == requerimiento.id
        ).delete(synchronize_session=False)
        for co_orm in _comentarios_dominio_a_orm(requerimiento):
            self._session.add(co_orm)

        self._session.commit()

    # ── Lecturas individuales ──────────────────────────────────────────────

    def obtener_por_id(self, requerimiento_id: str) -> Optional[Requerimiento]:
        row = self._session.get(RequerimientoORM, requerimiento_id)
        if row is None:
            return None
        return _requerimiento_orm_a_dominio(
            row,
            self._cargar_eventos(requerimiento_id),
            self._cargar_comentarios(requerimiento_id),
        )

    # ── Lecturas en lote ───────────────────────────────────────────────────

    def listar(self) -> list[Requerimiento]:
        return self._listar_filas(
            self._session.query(RequerimientoORM).all()
        )

    def listar_por_solicitante(self, solicitante_id: str) -> list[Requerimiento]:
        rows = (
            self._session.query(RequerimientoORM)
            .filter(RequerimientoORM.solicitante_id == solicitante_id)
            .all()
        )
        return self._listar_filas(rows)

    def listar_por_tecnico(self, tecnico_id: str) -> list[Requerimiento]:
        rows = (
            self._session.query(RequerimientoORM)
            .filter(RequerimientoORM.tecnico_asignado_id == tecnico_id)
            .all()
        )
        return self._listar_filas(rows)

    def listar_por_estado(self, estado: EstadoRequerimiento) -> list[Requerimiento]:
        rows = (
            self._session.query(RequerimientoORM)
            .filter(RequerimientoORM.estado == estado.value)
            .all()
        )
        return self._listar_filas(rows)

    # ── Helpers privados ───────────────────────────────────────────────────

    def _cargar_eventos(self, req_id: str) -> list[EventoORM]:
        return (
            self._session.query(EventoORM)
            .filter(EventoORM.requerimiento_id == req_id)
            .order_by(EventoORM.fecha)
            .all()
        )

    def _cargar_comentarios(self, req_id: str) -> list[ComentarioORM]:
        return (
            self._session.query(ComentarioORM)
            .filter(ComentarioORM.requerimiento_id == req_id)
            .order_by(ComentarioORM.fecha)
            .all()
        )

    def _listar_filas(self, rows: list[RequerimientoORM]) -> list[Requerimiento]:
        """Carga eventos y comentarios en batch para evitar N+1."""
        if not rows:
            return []

        ids = [r.id for r in rows]

        # Batch load de eventos
        eventos_map: dict[str, list[EventoORM]] = defaultdict(list)
        for ev in (
            self._session.query(EventoORM)
            .filter(EventoORM.requerimiento_id.in_(ids))
            .order_by(EventoORM.fecha)
        ):
            eventos_map[ev.requerimiento_id].append(ev)

        # Batch load de comentarios
        comentarios_map: dict[str, list[ComentarioORM]] = defaultdict(list)
        for co in (
            self._session.query(ComentarioORM)
            .filter(ComentarioORM.requerimiento_id.in_(ids))
            .order_by(ComentarioORM.fecha)
        ):
            comentarios_map[co.requerimiento_id].append(co)

        return [
            _requerimiento_orm_a_dominio(
                row,
                eventos_map[row.id],
                comentarios_map[row.id],
            )
            for row in rows
        ]
