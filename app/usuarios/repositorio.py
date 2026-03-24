"""Contrato abstracto del repositorio de usuarios.

Define la interfaz que cualquier implementación de persistencia de usuarios
debe cumplir.  No contiene ningún detalle de infraestructura (sin SQLAlchemy,
sin MongoDB, sin HTTP).

La capa de servicios depende únicamente de esta interfaz, lo que permite:
- inyectar un repositorio en memoria en los tests de servicio,
- sustituir la implementación concreta sin tocar el dominio ni los servicios.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from app.usuarios.dominio import Usuario


class RepositorioUsuario(ABC):
    """Contrato de persistencia para la entidad Usuario.

    Semántica de ``guardar``:
        Actúa como upsert: persiste el usuario tanto si es nuevo como si ya
        existe.  La implementación concreta es responsable de distinguir
        inserción de actualización (por ejemplo, verificando si el ID ya
        existe en la base de datos).
    """

    @abstractmethod
    def guardar(self, usuario: Usuario) -> None:
        """Persiste el usuario (inserción o actualización)."""

    @abstractmethod
    def obtener_por_id(self, usuario_id: str) -> Usuario | None:
        """Retorna el usuario con ese ID, o ``None`` si no existe."""

    @abstractmethod
    def obtener_por_email(self, email: str) -> Usuario | None:
        """Retorna el usuario con ese email, o ``None`` si no existe.

        Utilizado por el servicio de autenticación para localizar al usuario
        antes de comparar el hash de contraseña.
        """

    @abstractmethod
    def listar(self) -> list[Usuario]:
        """Retorna todos los usuarios registrados en el sistema."""
