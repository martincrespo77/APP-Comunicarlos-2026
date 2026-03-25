"""Excepciones de la capa de aplicación del módulo de usuarios.

Estas excepciones representan errores de aplicación (no de dominio):
situaciones detectadas por el servicio al orquestar repositorio y entidad.

Diferencia con las excepciones de dominio:
    Las excepciones de dominio (ValueError, etc.) señalan invariantes
    rotos dentro de la entidad.  Las excepciones de aquí señalan
    precondiciones del caso de uso: recurso no encontrado, email
    duplicado o credenciales incorrectas.
"""


class UsuarioError(Exception):
    """Error base de la capa de aplicación de usuarios."""


class UsuarioNoEncontrado(UsuarioError):
    """No existe un usuario con el ID o email indicado."""


class EmailDuplicado(UsuarioError):
    """Ya existe un usuario registrado con ese email."""


class CredencialesInvalidas(UsuarioError):
    """El email no existe o la contraseña no coincide con el hash."""
