"""Tests unitarios para app/usuarios/schemas.py.

Cubre:
  - UsuarioCrearIn: creación válida y rechazo de datos faltantes.
  - UsuarioAutenticarIn: creación válida.
  - UsuarioOut: construcción directa y mapeo desde_entidad().
  - Ausencia de password_hash en UsuarioOut.
"""

from __future__ import annotations

import unittest
from datetime import datetime

from pydantic import ValidationError

from app.compartido.dominio import RolUsuario
from app.usuarios.dominio import Usuario
from app.usuarios.schemas import UsuarioAutenticarIn, UsuarioCrearIn, UsuarioOut

_HASH = "$2b$12$hash_fijo_para_tests"


def _usuario_base(
    rol: RolUsuario = RolUsuario.TECNICO,
    activo: bool = True,
    ultimo_acceso: datetime | None = None,
) -> Usuario:
    return Usuario(
        id="u-001",
        nombre="Ana Gómez",
        email="ana@empresa.com",
        rol=rol,
        password_hash=_HASH,
        activo=activo,
        ultimo_acceso=ultimo_acceso,
    )


# ═══════════════════════════════════════════════════════════
#  UsuarioCrearIn
# ═══════════════════════════════════════════════════════════


class TestUsuarioCrearIn(unittest.TestCase):

    def test_creacion_valida(self):
        dto = UsuarioCrearIn(
            nombre="Carlos Ruiz",
            email="carlos@empresa.com",
            rol=RolUsuario.OPERADOR,
            password="secreto123",
        )
        self.assertEqual(dto.nombre, "Carlos Ruiz")
        self.assertEqual(dto.email, "carlos@empresa.com")
        self.assertEqual(dto.rol, RolUsuario.OPERADOR)
        self.assertEqual(dto.password, "secreto123")

    def test_rol_acepta_valor_enum_string(self):
        """Pydantic debe coercionar el string al enum."""
        dto = UsuarioCrearIn(
            nombre="Luis",
            email="luis@empresa.com",
            rol="solicitante",
            password="pw",
        )
        self.assertEqual(dto.rol, RolUsuario.SOLICITANTE)

    def test_falta_campo_obligatorio_nombre(self):
        with self.assertRaises(ValidationError):
            UsuarioCrearIn(
                email="x@empresa.com",
                rol=RolUsuario.TECNICO,
                password="pw",
            )

    def test_falta_campo_obligatorio_password(self):
        with self.assertRaises(ValidationError):
            UsuarioCrearIn(
                nombre="Juan",
                email="juan@empresa.com",
                rol=RolUsuario.TECNICO,
            )

    def test_no_tiene_campo_password_hash(self):
        """El schema de entrada nunca debe exponer password_hash."""
        dto = UsuarioCrearIn(
            nombre="Test",
            email="t@e.com",
            rol=RolUsuario.SOLICITANTE,
            password="pw",
        )
        self.assertFalse(hasattr(dto, "password_hash"))


# ═══════════════════════════════════════════════════════════
#  UsuarioAutenticarIn
# ═══════════════════════════════════════════════════════════


class TestUsuarioAutenticarIn(unittest.TestCase):

    def test_creacion_valida(self):
        dto = UsuarioAutenticarIn(email="a@b.com", password="clave")
        self.assertEqual(dto.email, "a@b.com")
        self.assertEqual(dto.password, "clave")

    def test_falta_email_lanza_error(self):
        with self.assertRaises(ValidationError):
            UsuarioAutenticarIn(password="clave")

    def test_falta_password_lanza_error(self):
        with self.assertRaises(ValidationError):
            UsuarioAutenticarIn(email="a@b.com")


# ═══════════════════════════════════════════════════════════
#  UsuarioOut
# ═══════════════════════════════════════════════════════════


class TestUsuarioOut(unittest.TestCase):

    def test_construccion_directa(self):
        ahora = datetime(2025, 1, 15, 10, 0, 0)
        dto = UsuarioOut(
            id="u-001",
            nombre="Ana",
            email="ana@e.com",
            rol=RolUsuario.TECNICO,
            activo=True,
            fecha_creacion=ahora,
            ultimo_acceso=None,
        )
        self.assertEqual(dto.id, "u-001")
        self.assertIsNone(dto.ultimo_acceso)

    def test_desde_entidad_mapea_correctamente(self):
        usuario = _usuario_base()
        dto = UsuarioOut.desde_entidad(usuario)
        self.assertEqual(dto.id, usuario.id)
        self.assertEqual(dto.nombre, usuario.nombre)
        self.assertEqual(dto.email, usuario.email)
        self.assertEqual(dto.rol, usuario.rol)
        self.assertEqual(dto.activo, usuario.activo)
        self.assertEqual(dto.fecha_creacion, usuario.fecha_creacion)
        self.assertIsNone(dto.ultimo_acceso)

    def test_desde_entidad_con_ultimo_acceso(self):
        acceso = datetime(2025, 6, 1, 8, 30, 0)
        usuario = _usuario_base(ultimo_acceso=acceso)
        dto = UsuarioOut.desde_entidad(usuario)
        self.assertEqual(dto.ultimo_acceso, acceso)

    def test_desde_entidad_usuario_inactivo(self):
        usuario = _usuario_base(activo=False)
        usuario.desactivar()
        dto = UsuarioOut.desde_entidad(usuario)
        self.assertFalse(dto.activo)

    def test_no_expone_password_hash(self):
        """La representación pública nunca debe incluir password_hash."""
        usuario = _usuario_base()
        dto = UsuarioOut.desde_entidad(usuario)
        self.assertFalse(hasattr(dto, "password_hash"))
        datos = dto.model_dump()
        self.assertNotIn("password_hash", datos)

    def test_serializable_a_dict(self):
        usuario = _usuario_base()
        datos = UsuarioOut.desde_entidad(usuario).model_dump()
        campos_esperados = {"id", "nombre", "email", "rol", "activo", "fecha_creacion", "ultimo_acceso"}
        self.assertEqual(set(datos.keys()), campos_esperados)

    def test_diferentes_roles(self):
        for rol in RolUsuario:
            usuario = _usuario_base(rol=rol)
            dto = UsuarioOut.desde_entidad(usuario)
            self.assertEqual(dto.rol, rol)


if __name__ == "__main__":
    unittest.main()
