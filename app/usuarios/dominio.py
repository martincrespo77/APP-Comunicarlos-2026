"""Dominio del módulo de usuarios.

Define la entidad Usuario.  El enum RolUsuario se importa
del shared kernel (``app.compartido.dominio``).

Nota sobre email corporativo:
    El TP exige que operadores y técnicos usen correo corporativo.
    La política concreta (ej. dominio @comunicarlos.com) se aplica
    en la capa de servicio o mediante un Value Object EmailCorporativo
    cuando se defina el dominio de la empresa.  El dominio valida
    únicamente que el email tenga formato mínimo reconocible.
"""

from __future__ import annotations

from datetime import datetime

from app.compartido.dominio import RolUsuario


class Usuario:
    """Entidad que representa un actor del sistema.

    Cada usuario tiene un rol fijo que determina qué acciones puede
    realizar sobre los requerimientos.

    ``password_hash`` es un string opaco: el hash ya procesado por
    bcrypt (u otro algoritmo) en la capa de servicio.  El dominio
    no conoce ni aplica el algoritmo de hashing.
    """

    def __init__(
        self,
        id: str,
        nombre: str,
        email: str,
        rol: RolUsuario,
        *,
        password_hash: str,
        activo: bool = True,
        fecha_creacion: datetime | None = None,
        ultimo_acceso: datetime | None = None,
    ) -> None:
        if not nombre or not nombre.strip():
            raise ValueError("El nombre del usuario no puede estar vacío.")
        if not email or not email.strip():
            raise ValueError("El email del usuario no puede estar vacío.")
        if "@" not in email:
            raise ValueError("El email del usuario debe contener '@'.")
        if not password_hash or not password_hash.strip():
            raise ValueError("El password_hash no puede estar vacío.")

        self._id = id
        self._nombre = nombre.strip()
        self._email = email.strip()
        self._rol = rol
        self._password_hash = password_hash
        self._activo = activo
        self._fecha_creacion = fecha_creacion or datetime.now()
        self._ultimo_acceso: datetime | None = ultimo_acceso

    # ── Propiedades ──

    @property
    def id(self) -> str:
        return self._id

    @property
    def nombre(self) -> str:
        return self._nombre

    @property
    def email(self) -> str:
        return self._email

    @property
    def rol(self) -> RolUsuario:
        return self._rol

    @property
    def password_hash(self) -> str:
        return self._password_hash

    @property
    def activo(self) -> bool:
        return self._activo

    @property
    def fecha_creacion(self) -> datetime:
        return self._fecha_creacion

    @property
    def ultimo_acceso(self) -> datetime | None:
        return self._ultimo_acceso

    # ── Comportamiento ──

    def desactivar(self) -> None:
        """Marca al usuario como inactivo."""
        self._activo = False

    def activar(self) -> None:
        """Marca al usuario como activo."""
        self._activo = True

    def registrar_acceso(self) -> None:
        """Actualiza la marca temporal del último acceso al momento actual."""
        self._ultimo_acceso = datetime.now()

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Usuario):
            return NotImplemented
        return self._id == other._id

    def __hash__(self) -> int:
        return hash(self._id)

    def __repr__(self) -> str:
        return f"Usuario(id={self._id!r}, nombre={self._nombre!r}, rol={self._rol.value})"
