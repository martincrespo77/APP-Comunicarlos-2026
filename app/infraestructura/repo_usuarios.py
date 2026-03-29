"""Implementación MongoDB del repositorio de usuarios.

Traduce entre la entidad de dominio ``Usuario`` y documentos MongoDB.
La lógica de negocio permanece cero: este módulo solo serializa/deserializa.

Patrón anti-corrupción:
    ``_doc_a_dominio`` reconstruye la entidad con todos sus campos, incluyendo
    los privados, sin pasar por el constructor de dominio más de una vez.
"""

from __future__ import annotations

from typing import Any, Optional

from pymongo.database import Database

from app.compartido.dominio import RolUsuario
from app.usuarios.dominio import Usuario
from app.usuarios.repositorio import RepositorioUsuario

_COLECCION = "usuarios"


# ──────────────────────────────────────────────────────────────────────────────
#  Helpers de traducción
# ──────────────────────────────────────────────────────────────────────────────


def _doc_a_dominio(doc: dict[str, Any]) -> Usuario:
    """Reconstruye un ``Usuario`` de dominio a partir de un documento MongoDB."""
    return Usuario(
        id=doc["_id"],
        nombre=doc["nombre"],
        email=doc["email"],
        rol=RolUsuario(doc["rol"]),
        password_hash=doc["password_hash"],
        activo=doc["activo"],
        fecha_creacion=doc.get("fecha_creacion"),
        ultimo_acceso=doc.get("ultimo_acceso"),
    )


def _dominio_a_doc(usuario: Usuario) -> dict[str, Any]:
    """Serializa un ``Usuario`` de dominio a documento MongoDB."""
    return {
        "_id": usuario.id,
        "nombre": usuario.nombre,
        "email": usuario.email,
        "rol": usuario.rol.value,
        "password_hash": usuario.password_hash,
        "activo": usuario.activo,
        "fecha_creacion": usuario.fecha_creacion,
        "ultimo_acceso": usuario.ultimo_acceso,
    }


# ──────────────────────────────────────────────────────────────────────────────
#  Repositorio concreto
# ──────────────────────────────────────────────────────────────────────────────


class RepositorioUsuarioMongo(RepositorioUsuario):
    """Repositorio de usuarios respaldado por MongoDB (pymongo).

    Cada instancia recibe una referencia a la ``Database`` pymongo activa.
    """

    def __init__(self, db: Database) -> None:
        self._col = db[_COLECCION]

    def guardar(self, usuario: Usuario) -> None:
        """Inserta o actualiza un usuario (upsert vía replace_one)."""
        doc = _dominio_a_doc(usuario)
        self._col.replace_one({"_id": doc["_id"]}, doc, upsert=True)

    def obtener_por_id(self, usuario_id: str) -> Optional[Usuario]:
        doc = self._col.find_one({"_id": usuario_id})
        return _doc_a_dominio(doc) if doc else None

    def obtener_por_email(self, email: str) -> Optional[Usuario]:
        doc = self._col.find_one({"email": email})
        return _doc_a_dominio(doc) if doc else None

    def listar(self) -> list[Usuario]:
        return [_doc_a_dominio(doc) for doc in self._col.find()]
