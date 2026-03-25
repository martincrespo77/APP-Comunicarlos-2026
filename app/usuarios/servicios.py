"""Capa de servicios de aplicación — módulo de usuarios.

Orquesta repositorio, entidad y hashing de contraseñas.
No contiene lógica de negocio: las reglas de la entidad viven en
``app.usuarios.dominio``.

Dependencias inyectadas:
    repo        — RepositorioUsuario (ABC)
    hasher      — Callable[[str], str]: password_plano → hash
    verificador — Callable[[str, str], bool]: (password_plano, hash) → bool

En producción se inyectan las funciones de bcrypt.
En tests se inyectan callables triviales sin dependencias externas.
"""

from __future__ import annotations

from typing import Callable
from uuid import uuid4

from app.compartido.dominio import RolUsuario
from app.usuarios.dominio import Usuario
from app.usuarios.excepciones import (
    CredencialesInvalidas,
    EmailDuplicado,
    UsuarioNoEncontrado,
)
from app.usuarios.repositorio import RepositorioUsuario


class UsuarioService:
    """Casos de uso del módulo de usuarios."""

    def __init__(
        self,
        repo: RepositorioUsuario,
        hasher: Callable[[str], str],
        verificador: Callable[[str, str], bool],
    ) -> None:
        self._repo = repo
        self._hasher = hasher
        self._verificador = verificador

    # ── Casos de uso ──────────────────────────────────────────────

    def registrar(
        self,
        nombre: str,
        email: str,
        rol: RolUsuario,
        password_plano: str,
    ) -> str:
        """Registra un nuevo usuario en el sistema.

        Returns:
            El ID del usuario creado.

        Raises:
            EmailDuplicado: si ya existe un usuario con ese email.
            ValueError:     si los datos violan invariantes de la entidad.
        """
        if self._repo.obtener_por_email(email) is not None:
            raise EmailDuplicado(f"Ya existe un usuario con el email '{email}'.")

        hash_ = self._hasher(password_plano)
        usuario = Usuario(
            id=str(uuid4()),
            nombre=nombre,
            email=email,
            rol=rol,
            password_hash=hash_,
        )
        self._repo.guardar(usuario)
        return usuario.id

    def autenticar(self, email: str, password_plano: str) -> Usuario:
        """Verifica credenciales y registra el acceso.

        Returns:
            La entidad Usuario autenticada.

        Raises:
            CredencialesInvalidas: si el email no existe o la contraseña
                                   no coincide.
        """
        usuario = self._repo.obtener_por_email(email)
        if usuario is None:
            raise CredencialesInvalidas("Credenciales inválidas.")
        if not self._verificador(password_plano, usuario.password_hash):
            raise CredencialesInvalidas("Credenciales inválidas.")

        usuario.registrar_acceso()
        self._repo.guardar(usuario)
        return usuario

    def obtener(self, usuario_id: str) -> Usuario:
        """Retorna el usuario con ese ID.

        Raises:
            UsuarioNoEncontrado: si no existe.
        """
        usuario = self._repo.obtener_por_id(usuario_id)
        if usuario is None:
            raise UsuarioNoEncontrado(f"Usuario '{usuario_id}' no encontrado.")
        return usuario

    def listar(self) -> list[Usuario]:
        """Retorna todos los usuarios del sistema."""
        return self._repo.listar()

    def desactivar(self, usuario_id: str) -> None:
        """Desactiva el usuario indicado.

        Raises:
            UsuarioNoEncontrado: si no existe.
        """
        usuario = self.obtener(usuario_id)
        usuario.desactivar()
        self._repo.guardar(usuario)
