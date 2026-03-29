"""Implementación MongoDB del repositorio de requerimientos.

Traduce entre las entidades de dominio (``Incidente``, ``Solicitud``, value
objects ``Evento``, ``Comentario``) y documentos MongoDB.

Decisión de diseño — Documento embebido:
    Cada requerimiento se almacena como un único documento con los arrays
    ``eventos`` y ``comentarios`` incrustados.  Esto garantiza escrituras
    atómicas sin necesidad de transacciones multi-documento.

Anti-corrupción layer:
    El dominio usa atributos privados (``_eventos``, ``_comentarios``,
    ``_eventos_dominio``).  Para reconstruir la entidad desde la base de
    datos sin contaminar el dominio, el repositorio asigna directamente
    esos atributos tras construir la entidad con ``registrar_creacion=False``.
"""

from __future__ import annotations

from typing import Any, Optional

from pymongo.database import Database

from app.compartido.dominio import RolUsuario
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

_COLECCION = "requerimientos"


# ──────────────────────────────────────────────────────────────────────────────
#  Helpers de traducción  Documento → Dominio
# ──────────────────────────────────────────────────────────────────────────────


def _evento_doc_a_dominio(d: dict[str, Any]) -> Evento:
    return Evento(
        tipo=TipoEvento(d["tipo"]),
        actor_id=d["actor_id"],
        detalle=d["detalle"],
        id=d["id"],
        fecha=d["fecha"],
    )


def _comentario_doc_a_dominio(d: dict[str, Any]) -> Comentario:
    return Comentario(
        autor_id=d["autor_id"],
        rol_autor=RolUsuario(d["rol_autor"]),
        contenido=d["contenido"],
        id=d["id"],
        fecha=d["fecha"],
    )


def _doc_a_dominio(doc: dict[str, Any]) -> Requerimiento:
    """Reconstruye el agregado Requerimiento desde un documento MongoDB.

    Usa ``registrar_creacion=False`` para evitar duplicar el evento CREACION.
    Luego restaura los atributos privados de historial directamente.
    """
    estado = EstadoRequerimiento(doc["estado"])

    if TipoRequerimiento(doc["tipo"]) == TipoRequerimiento.INCIDENTE:
        req: Requerimiento = Incidente(
            titulo=doc["titulo"],
            descripcion=doc["descripcion"],
            solicitante_id=doc["solicitante_id"],
            urgencia=Urgencia(doc["urgencia"]),
            categoria=CategoriaIncidente(doc["categoria"]),
            id=doc["_id"],
            estado=estado,
            operador_id=doc.get("operador_id"),
            tecnico_asignado_id=doc.get("tecnico_asignado_id"),
            fecha_creacion=doc["fecha_creacion"],
            fecha_actualizacion=doc["fecha_actualizacion"],
            registrar_creacion=False,
        )
    else:
        req = Solicitud(
            titulo=doc["titulo"],
            descripcion=doc["descripcion"],
            solicitante_id=doc["solicitante_id"],
            categoria=CategoriaSolicitud(doc["categoria"]),
            id=doc["_id"],
            estado=estado,
            operador_id=doc.get("operador_id"),
            tecnico_asignado_id=doc.get("tecnico_asignado_id"),
            fecha_creacion=doc["fecha_creacion"],
            fecha_actualizacion=doc["fecha_actualizacion"],
            registrar_creacion=False,
        )

    # Restaurar historial de auditoría (atributos privados convencionales)
    req._eventos = [_evento_doc_a_dominio(e) for e in doc.get("eventos", [])]
    req._comentarios = [_comentario_doc_a_dominio(c) for c in doc.get("comentarios", [])]
    req._eventos_dominio = []

    return req


# ──────────────────────────────────────────────────────────────────────────────
#  Helpers de traducción  Dominio → Documento
# ──────────────────────────────────────────────────────────────────────────────


def _dominio_a_doc(req: Requerimiento) -> dict[str, Any]:
    """Serializa el agregado completo a un documento MongoDB."""
    es_incidente = req.tipo == TipoRequerimiento.INCIDENTE

    doc: dict[str, Any] = {
        "_id": req.id,
        "tipo": req.tipo.value,
        "titulo": req.titulo,
        "descripcion": req.descripcion,
        "estado": req.estado.value,
        "solicitante_id": req.solicitante_id,
        "operador_id": req.operador_id,
        "tecnico_asignado_id": req.tecnico_asignado_id,
        "urgencia": req.urgencia.value if es_incidente else None,  # type: ignore[attr-defined]
        "categoria": req.categoria.value,  # type: ignore[attr-defined]
        "fecha_creacion": req.fecha_creacion,
        "fecha_actualizacion": req.fecha_actualizacion,
        "eventos": [
            {
                "id": ev.id,
                "tipo": ev.tipo.value,
                "actor_id": ev.actor_id,
                "detalle": ev.detalle,
                "fecha": ev.fecha,
            }
            for ev in req.eventos
        ],
        "comentarios": [
            {
                "id": co.id,
                "autor_id": co.autor_id,
                "rol_autor": co.rol_autor.value,
                "contenido": co.contenido,
                "fecha": co.fecha,
            }
            for co in req.comentarios
        ],
    }
    return doc


# ──────────────────────────────────────────────────────────────────────────────
#  Repositorio concreto
# ──────────────────────────────────────────────────────────────────────────────


class RepositorioRequerimientoMongo(RepositorioRequerimiento):
    """Repositorio de requerimientos respaldado por MongoDB (pymongo).

    Estrategia de persistencia:
        El agregado completo (requerimiento + eventos + comentarios) se
        almacena como un único documento.  ``replace_one`` con ``upsert=True``
        garantiza escrituras atómicas sin transacciones.
    """

    def __init__(self, db: Database) -> None:
        self._col = db[_COLECCION]

    # ── Escritura ──────────────────────────────────────────────────────────

    def guardar(self, requerimiento: Requerimiento) -> None:
        doc = _dominio_a_doc(requerimiento)
        self._col.replace_one({"_id": doc["_id"]}, doc, upsert=True)

    # ── Lecturas individuales ──────────────────────────────────────────────

    def obtener_por_id(self, requerimiento_id: str) -> Optional[Requerimiento]:
        doc = self._col.find_one({"_id": requerimiento_id})
        return _doc_a_dominio(doc) if doc else None

    # ── Lecturas en lote ───────────────────────────────────────────────────

    def listar(self) -> list[Requerimiento]:
        return [_doc_a_dominio(doc) for doc in self._col.find()]

    def listar_por_solicitante(self, solicitante_id: str) -> list[Requerimiento]:
        return [
            _doc_a_dominio(doc)
            for doc in self._col.find({"solicitante_id": solicitante_id})
        ]

    def listar_por_tecnico(self, tecnico_id: str) -> list[Requerimiento]:
        return [
            _doc_a_dominio(doc)
            for doc in self._col.find({"tecnico_asignado_id": tecnico_id})
        ]

    def listar_por_estado(self, estado: EstadoRequerimiento) -> list[Requerimiento]:
        return [
            _doc_a_dominio(doc)
            for doc in self._col.find({"estado": estado.value})
        ]
