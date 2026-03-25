"""Implementación SQLAlchemy del repositorio de usuarios.

Traduce entre la entidad de dominio ``Usuario`` y el modelo ORM ``UsuarioORM``.
La lógica de negocio permanece cero: este módulo solo serializa/deserializa.

Patrón anti-corrupción:
    ``_orm_a_dominio`` reconstruye la entidad con todos sus campos, incluyendo
    los privados, sin pasar por el constructor de dominio más de una vez.
    No hay eventos en Usuario, por lo que la reconstrucción es directa.
"""

from __future__ import annotations

from typing import Optional

from sqlalchemy.orm import Session

from app.compartido.dominio import RolUsuario
from app.infraestructura.modelos_orm import UsuarioORM
from app.usuarios.dominio import Usuario
from app.usuarios.repositorio import RepositorioUsuario


# ──────────────────────────────────────────────────────────────────────────────
#  Helpers de traducción
# ──────────────────────────────────────────────────────────────────────────────


def _orm_a_dominio(row: UsuarioORM) -> Usuario:
    """Reconstruye un ``Usuario`` de dominio a partir de una fila ORM."""
    return Usuario(
        id=row.id,
        nombre=row.nombre,
        email=row.email,
        rol=RolUsuario(row.rol),
        password_hash=row.password_hash,
        activo=row.activo,
        fecha_creacion=row.fecha_creacion,
        ultimo_acceso=row.ultimo_acceso,
    )


def _dominio_a_orm(usuario: Usuario) -> UsuarioORM:
    """Crea un ``UsuarioORM`` a partir de la entidad de dominio."""
    return UsuarioORM(
        id=usuario.id,
        nombre=usuario.nombre,
        email=usuario.email,
        rol=usuario.rol.value,
        password_hash=usuario.password_hash,
        activo=usuario.activo,
        fecha_creacion=usuario.fecha_creacion,
        ultimo_acceso=usuario.ultimo_acceso,
    )


# ──────────────────────────────────────────────────────────────────────────────
#  Repositorio concreto
# ──────────────────────────────────────────────────────────────────────────────


class RepositorioUsuarioSQL(RepositorioUsuario):
    """Repositorio de usuarios respaldado por SQLAlchemy.

    Cada instancia recibe una sesión activa.  El ciclo de vida de la
    sesión (commit / rollback / close) es responsabilidad de quien
    inyecta la sesión (``app.deps.get_db``).
    """

    def __init__(self, session: Session) -> None:
        self._session = session

    def guardar(self, usuario: Usuario) -> None:
        """Inserta o actualiza un usuario (upsert vía merge)."""
        orm = _dominio_a_orm(usuario)
        self._session.merge(orm)
        self._session.commit()

    def obtener_por_id(self, usuario_id: str) -> Optional[Usuario]:
        row = self._session.get(UsuarioORM, usuario_id)
        return _orm_a_dominio(row) if row else None

    def obtener_por_email(self, email: str) -> Optional[Usuario]:
        row = (
            self._session.query(UsuarioORM)
            .filter(UsuarioORM.email == email)
            .first()
        )
        return _orm_a_dominio(row) if row else None

    def listar(self) -> list[Usuario]:
        rows = self._session.query(UsuarioORM).all()
        return [_orm_a_dominio(r) for r in rows]
