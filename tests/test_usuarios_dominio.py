"""Tests unitarios — Dominio del módulo de usuarios.

Cubre la entidad Usuario: creación, validaciones, campos de auditoría,
activación/desactivación e identidad por ID.

STYLEGUIDE_PROFE: unittest, setUp, tearDown, AAA, test_<comportamiento>.
"""

import unittest
from datetime import datetime

from app.compartido.dominio import RolUsuario
from app.usuarios.dominio import Usuario

_HASH = "$2b$12$hash_fijo_para_tests"


class TestUsuarioCreacion(unittest.TestCase):
    """U01-U02, E26-E27 — Verifica la creación y validaciones de Usuario."""

    def setUp(self):
        self.usuario = Usuario(
            id="usr-001",
            nombre="Ana García",
            email="ana@comunicarlos.com.ar",
            rol=RolUsuario.OPERADOR,
            password_hash=_HASH,
        )

    def tearDown(self):
        pass

    def test_usuario_se_crea_con_datos_correctos(self):
        # Arrange (setUp)
        # Act / Assert
        self.assertEqual(self.usuario.id, "usr-001")
        self.assertEqual(self.usuario.nombre, "Ana García")
        self.assertEqual(self.usuario.email, "ana@comunicarlos.com.ar")
        self.assertEqual(self.usuario.rol, RolUsuario.OPERADOR)

    def test_usuario_activo_por_defecto(self):
        # Arrange (setUp)
        # Act / Assert
        self.assertTrue(self.usuario.activo)

    def test_usuario_nombre_vacio_falla(self):
        # Arrange / Act / Assert
        with self.assertRaises(ValueError):
            Usuario(
                id="usr-002",
                nombre="",
                email="x@x.com",
                rol=RolUsuario.SOLICITANTE,
                password_hash=_HASH,
            )

    def test_usuario_nombre_solo_espacios_falla(self):
        with self.assertRaises(ValueError):
            Usuario(
                id="usr-002",
                nombre="   ",
                email="x@x.com",
                rol=RolUsuario.SOLICITANTE,
                password_hash=_HASH,
            )

    def test_usuario_email_vacio_falla(self):
        # Arrange / Act / Assert
        with self.assertRaises(ValueError):
            Usuario(
                id="usr-003",
                nombre="Carlos",
                email="",
                rol=RolUsuario.TECNICO,
                password_hash=_HASH,
            )

    def test_usuario_email_solo_espacios_falla(self):
        with self.assertRaises(ValueError):
            Usuario(
                id="usr-003",
                nombre="Carlos",
                email="   ",
                rol=RolUsuario.TECNICO,
                password_hash=_HASH,
            )

    def test_usuario_email_sin_arroba_falla(self):
        # Arrange / Act / Assert
        with self.assertRaises(ValueError):
            Usuario(
                id="usr-004",
                nombre="Carlos",
                email="carlos_sin_arroba",
                rol=RolUsuario.TECNICO,
                password_hash=_HASH,
            )

    def test_usuario_con_cada_rol_valido(self):
        # Arrange / Act / Assert
        emails_por_rol = {
            RolUsuario.SOLICITANTE: "sol@gmail.com",
            RolUsuario.SUPERVISOR: "sup@gmail.com",
            RolUsuario.OPERADOR: "op@comunicarlos.com.ar",
            RolUsuario.TECNICO: "tec@comunicarlos.com.ar",
        }
        for rol in RolUsuario:
            with self.subTest(rol=rol.value):
                u = Usuario(
                    id="x",
                    nombre="Test",
                    email=emails_por_rol[rol],
                    rol=rol,
                    password_hash=_HASH,
                )
                self.assertEqual(u.rol, rol)


class TestUsuarioPasswordHash(unittest.TestCase):
    """U06 — Verifica el campo password_hash."""

    def tearDown(self):
        pass

    def test_password_hash_se_almacena(self):
        # Arrange / Act
        u = Usuario(
            id="usr-020",
            nombre="Laura",
            email="laura@comunicarlos.com.ar",
            rol=RolUsuario.OPERADOR,
            password_hash="$2b$12$abcdef",
        )
        # Assert
        self.assertEqual(u.password_hash, "$2b$12$abcdef")

    def test_password_hash_vacio_falla(self):
        # Arrange / Act / Assert
        with self.assertRaises(ValueError):
            Usuario(
                id="usr-021",
                nombre="Laura",
                email="laura@comunicarlos.com.ar",
                rol=RolUsuario.OPERADOR,
                password_hash="",
            )

    def test_password_hash_solo_espacios_falla(self):
        with self.assertRaises(ValueError):
            Usuario(
                id="usr-022",
                nombre="Laura",
                email="laura@comunicarlos.com.ar",
                rol=RolUsuario.OPERADOR,
                password_hash="   ",
            )

    def test_password_hash_no_tiene_setter(self):
        # Arrange
        u = Usuario(
            id="usr-023",
            nombre="Laura",
            email="laura@comunicarlos.com.ar",
            rol=RolUsuario.OPERADOR,
            password_hash=_HASH,
        )
        # Act / Assert — la propiedad no expone setter
        with self.assertRaises(AttributeError):
            u.password_hash = "otro_hash"  # type: ignore[misc]


class TestUsuarioFechasAuditoria(unittest.TestCase):
    """U07-U09 — Verifica fecha_creacion, ultimo_acceso y registrar_acceso."""

    def setUp(self):
        self.antes = datetime.now()
        self.usuario = Usuario(
            id="usr-030",
            nombre="Marcos",
            email="marcos@comunicarlos.com.ar",
            rol=RolUsuario.TECNICO,
            password_hash=_HASH,
        )
        self.despues = datetime.now()

    def tearDown(self):
        pass

    def test_fecha_creacion_se_autogenera(self):
        # Arrange (setUp)
        # Act / Assert — fecha_creacion cae entre antes y después
        self.assertGreaterEqual(self.usuario.fecha_creacion, self.antes)
        self.assertLessEqual(self.usuario.fecha_creacion, self.despues)

    def test_fecha_creacion_no_tiene_setter(self):
        # Arrange (setUp)
        # Act / Assert
        with self.assertRaises(AttributeError):
            self.usuario.fecha_creacion = datetime.now()  # type: ignore[misc]

    def test_fecha_creacion_aceptada_explicitamente(self):
        # Arrange
        fecha_fija = datetime(2025, 1, 15, 10, 0, 0)
        # Act
        u = Usuario(
            id="usr-031",
            nombre="Reconstruido",
            email="r@empresa.com",
            rol=RolUsuario.SOLICITANTE,
            password_hash=_HASH,
            fecha_creacion=fecha_fija,
        )
        # Assert — permite reconstituir desde persistencia
        self.assertEqual(u.fecha_creacion, fecha_fija)

    def test_ultimo_acceso_inicia_en_none(self):
        # Arrange (setUp)
        # Act / Assert
        self.assertIsNone(self.usuario.ultimo_acceso)

    def test_registrar_acceso_actualiza_ultimo_acceso(self):
        # Arrange
        self.assertIsNone(self.usuario.ultimo_acceso)
        antes = datetime.now()
        # Act
        self.usuario.registrar_acceso()
        despues = datetime.now()
        # Assert
        self.assertIsNotNone(self.usuario.ultimo_acceso)
        self.assertGreaterEqual(self.usuario.ultimo_acceso, antes)
        self.assertLessEqual(self.usuario.ultimo_acceso, despues)

    def test_registrar_acceso_multiples_veces_actualiza_siempre(self):
        # Arrange
        self.usuario.registrar_acceso()
        primer_acceso = self.usuario.ultimo_acceso
        # Act
        self.usuario.registrar_acceso()
        segundo_acceso = self.usuario.ultimo_acceso
        # Assert — segundo acceso es >= que el primero
        self.assertGreaterEqual(segundo_acceso, primer_acceso)

    def test_ultimo_acceso_no_tiene_setter(self):
        # Arrange (setUp)
        # Act / Assert
        with self.assertRaises(AttributeError):
            self.usuario.ultimo_acceso = datetime.now()  # type: ignore[misc]


class TestUsuarioActivacion(unittest.TestCase):
    """U03-U04 — Verifica activar y desactivar usuario."""

    def setUp(self):
        self.usuario = Usuario(
            id="usr-010",
            nombre="Pedro López",
            email="pedro@comunicarlos.com.ar",
            rol=RolUsuario.TECNICO,
            password_hash=_HASH,
        )

    def tearDown(self):
        pass

    def test_desactivar_usuario(self):
        # Arrange (setUp — activo por defecto)
        # Act
        self.usuario.desactivar()
        # Assert
        self.assertFalse(self.usuario.activo)

    def test_activar_usuario_desactivado(self):
        # Arrange
        self.usuario.desactivar()
        self.assertFalse(self.usuario.activo)
        # Act
        self.usuario.activar()
        # Assert
        self.assertTrue(self.usuario.activo)

    def test_activar_usuario_ya_activo_no_falla(self):
        # Arrange (setUp — ya activo)
        # Act / Assert — debe ser idempotente
        try:
            self.usuario.activar()
        except Exception as e:
            self.fail(f"activar() en usuario ya activo lanzó excepción: {e}")

    def test_desactivar_usuario_ya_inactivo_no_falla(self):
        # Arrange
        self.usuario.desactivar()
        # Act / Assert — debe ser idempotente
        try:
            self.usuario.desactivar()
        except Exception as e:
            self.fail(f"desactivar() en usuario ya inactivo lanzó excepción: {e}")


class TestUsuarioIdentidad(unittest.TestCase):
    """U05 — Verifica igualdad por ID."""

    def setUp(self):
        self.u1 = Usuario(
            id="usr-777",
            nombre="Usuario A",
            email="a@x.com",
            rol=RolUsuario.SOLICITANTE,
            password_hash=_HASH,
        )
        self.u2 = Usuario(
            id="usr-777",
            nombre="Usuario B diferente",
            email="b@comunicarlos.com.ar",
            rol=RolUsuario.OPERADOR,
            password_hash=_HASH,
        )
        self.u3 = Usuario(
            id="usr-888",
            nombre="Usuario C",
            email="c@z.com",
            rol=RolUsuario.SOLICITANTE,
            password_hash=_HASH,
        )

    def tearDown(self):
        pass

    def test_igualdad_por_id(self):
        # Arrange (setUp)
        # Act / Assert — mismo ID, distintos datos → iguales
        self.assertEqual(self.u1, self.u2)

    def test_distintos_ids_no_son_iguales(self):
        # Arrange (setUp)
        # Act / Assert
        self.assertNotEqual(self.u1, self.u3)

    def test_usuario_hashable_por_id(self):
        # Arrange
        conjunto = {self.u1, self.u2}
        # Act / Assert — mismo ID → un solo elemento
        self.assertEqual(len(conjunto), 1)


class TestEmailCorporativo(unittest.TestCase):
    """U10 — Valida que operadores y técnicos usen @comunicarlos.com.ar."""

    def tearDown(self):
        pass

    # ── roles corporativos: OPERADOR y TECNICO ────────────────────────────

    def test_operador_con_email_corporativo_valido(self):
        # Arrange / Act / Assert — no debe lanzar excepción
        try:
            u = Usuario(
                id="usr-c1",
                nombre="Ana Operador",
                email="ana@comunicarlos.com.ar",
                rol=RolUsuario.OPERADOR,
                password_hash=_HASH,
            )
        except ValueError as e:
            self.fail(f"Operador con email corporativo lanzó ValueError: {e}")
        self.assertEqual(u.email, "ana@comunicarlos.com.ar")

    def test_tecnico_con_email_corporativo_valido(self):
        try:
            u = Usuario(
                id="usr-c2",
                nombre="Carlos Técnico",
                email="carlos@comunicarlos.com.ar",
                rol=RolUsuario.TECNICO,
                password_hash=_HASH,
            )
        except ValueError as e:
            self.fail(f"Técnico con email corporativo lanzó ValueError: {e}")
        self.assertEqual(u.email, "carlos@comunicarlos.com.ar")

    def test_operador_con_email_no_corporativo_falla(self):
        # Arrange / Act / Assert
        with self.assertRaises(ValueError) as ctx:
            Usuario(
                id="usr-c3",
                nombre="Operador Malo",
                email="operador@gmail.com",
                rol=RolUsuario.OPERADOR,
                password_hash=_HASH,
            )
        self.assertIn("comunicarlos.com.ar", str(ctx.exception))

    def test_tecnico_con_email_no_corporativo_falla(self):
        with self.assertRaises(ValueError) as ctx:
            Usuario(
                id="usr-c4",
                nombre="Técnico Malo",
                email="tecnico@empresa.com",
                rol=RolUsuario.TECNICO,
                password_hash=_HASH,
            )
        self.assertIn("comunicarlos.com.ar", str(ctx.exception))

    def test_tecnico_con_dominio_parcialmente_correcto_falla(self):
        """@comunicarlos.com (sin .ar) no es el dominio corporativo."""
        with self.assertRaises(ValueError):
            Usuario(
                id="usr-c5",
                nombre="Técnico Parcial",
                email="tecnico@comunicarlos.com",
                rol=RolUsuario.TECNICO,
                password_hash=_HASH,
            )

    # ── roles NO corporativos: SOLICITANTE y SUPERVISOR ─────────────────

    def test_solicitante_puede_usar_cualquier_email(self):
        # Arrange / Act / Assert — SOLICITANTE no tiene restricción de dominio
        for email in ("sol@gmail.com", "s@hotmail.com", "s@empresa.org"):
            with self.subTest(email=email):
                try:
                    Usuario(
                        id="usr-c6",
                        nombre="Solicitante",
                        email=email,
                        rol=RolUsuario.SOLICITANTE,
                        password_hash=_HASH,
                    )
                except ValueError as e:
                    self.fail(f"Solicitante con {email!r} lanzó ValueError: {e}")

    def test_supervisor_puede_usar_cualquier_email(self):
        # Arrange / Act / Assert — SUPERVISOR no tiene restricción de dominio
        for email in ("jefe@gmail.com", "dir@empresa.org"):
            with self.subTest(email=email):
                try:
                    Usuario(
                        id="usr-c7",
                        nombre="Supervisor",
                        email=email,
                        rol=RolUsuario.SUPERVISOR,
                        password_hash=_HASH,
                    )
                except ValueError as e:
                    self.fail(f"Supervisor con {email!r} lanzó ValueError: {e}")


if __name__ == "__main__":
    unittest.main()
