"""Schemas (DTOs) del módulo de usuarios.

Esta capa es la única que depende de Pydantic.
El dominio (dominio.py) y los servicios (servicios.py) nunca importan
nada de este módulo.

Convención:
  - Sufijo ``In``  → datos que entran al sistema (request / input).
  - Sufijo ``Out`` → datos que salen del sistema (response / output).
  - ``password_hash`` NUNCA aparece en ningún schema de salida.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field

from app.compartido.dominio import RolUsuario
from app.usuarios.dominio import Usuario


# ═══════════════════════════════════════════════════════════
#  SCHEMAS DE ENTRADA
# ═══════════════════════════════════════════════════════════


class UsuarioCrearIn(BaseModel):
    """Datos necesarios para registrar un nuevo usuario.

    ``password`` es texto plano; la capa de servicio lo hashea
    antes de construir la entidad.
    """

    nombre: str = Field(
        min_length=2,
        max_length=100,
        examples=["Juan Pérez"],
        description="Nombre completo del usuario.",
    )
    email: EmailStr = Field(
        examples=["juan@comunicarlos.com.ar"],
        description="Email del usuario. Operadores y técnicos requieren dominio corporativo.",
    )
    rol: RolUsuario = Field(
        examples=["solicitante"],
        description="Rol asignado al usuario.",
    )
    password: str = Field(
        min_length=6,
        max_length=72,
        examples=["MiClave123"],
        description="Contraseña en texto plano (se hashea en el server).",
    )


class UsuarioAutenticarIn(BaseModel):
    """Credenciales para autenticar a un usuario."""

    email: EmailStr = Field(examples=["juan@comunicarlos.com.ar"])
    password: str = Field(min_length=1)


# ═══════════════════════════════════════════════════════════
#  SCHEMAS DE SALIDA
# ═══════════════════════════════════════════════════════════


class UsuarioOut(BaseModel):
    """Representación pública de un usuario.

    Excluye deliberadamente ``password_hash``.
    """

    id: str
    nombre: str
    email: str
    rol: RolUsuario
    activo: bool
    fecha_creacion: datetime
    ultimo_acceso: datetime | None

    @classmethod
    def desde_entidad(cls, usuario: Usuario) -> "UsuarioOut":
        """Construye el DTO a partir de la entidad de dominio."""
        return cls(
            id=usuario.id,
            nombre=usuario.nombre,
            email=usuario.email,
            rol=usuario.rol,
            activo=usuario.activo,
            fecha_creacion=usuario.fecha_creacion,
            ultimo_acceso=usuario.ultimo_acceso,
        )


class TokenOut(BaseModel):
    """Respuesta del endpoint de autenticación.

    Contiene el token JWT y el tipo (siempre ``bearer``).
    No incluye ningún dato personal del usuario: el cliente
    debe decodificar el token o llamar a GET /usuarios/{id}
    si necesita el perfil completo.
    """

    access_token: str
    token_type: str = "bearer"
