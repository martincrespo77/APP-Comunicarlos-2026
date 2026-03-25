"""Tests unitarios — capa de servicios de usuarios.

Usa FakeRepositorioUsuario (dict en memoria) y callables triviales
para hasher/verificador.  Sin base de datos real, sin FastAPI.

STYLEGUIDE_PROFE: unittest, setUp, tearDown, AAA, test_<comportamiento>.
"""

import unittest

from app.compartido.dominio import RolUsuario
from app.usuarios.dominio import Usuario
from app.usuarios.excepciones import (
    CredencialesInvalidas,
    EmailDuplicado,
    UsuarioNoEncontrado,
)
from app.usuarios.repositorio import RepositorioUsuario
from app.usuarios.servicios import UsuarioService


# ── Fake de repositorio ───────────────────────────────────────────────────────

class FakeRepositorioUsuario(RepositorioUsuario):
    """Implementación en memoria para tests."""

    def __init__(self):
        self._por_id: dict[str, Usuario] = {}

    def guardar(self, usuario: Usuario) -> None:
        self._por_id[usuario.id] = usuario

    def obtener_por_id(self, usuario_id: str) -> Usuario | None:
        return self._por_id.get(usuario_id)

    def obtener_por_email(self, email: str) -> Usuario | None:
        return next(
            (u for u in self._por_id.values() if u.email == email),
            None,
        )

    def listar(self) -> list[Usuario]:
        return list(self._por_id.values())


# ── Callables triviales ───────────────────────────────────────────────────────

def _hasher_fake(password_plano: str) -> str:
    return f"hashed:{password_plano}"


def _verificador_fake(password_plano: str, hash_: str) -> bool:
    return hash_ == f"hashed:{password_plano}"


# ── Helper ────────────────────────────────────────────────────────────────────

def _hacer_servicio() -> UsuarioService:
    return UsuarioService(
        repo=FakeRepositorioUsuario(),
        hasher=_hasher_fake,
        verificador=_verificador_fake,
    )


# ══════════════════════════════════════════════════════════════════════════════
#  Tests
# ══════════════════════════════════════════════════════════════════════════════

class TestRegistrarUsuario(unittest.TestCase):
    """S-U01 — Registrar nuevo usuario."""

    def setUp(self):
        self.servicio = _hacer_servicio()

    def tearDown(self):
        pass

    def test_registrar_retorna_id(self):
        # Arrange / Act
        id_ = self.servicio.registrar(
            nombre="Ana García",
            email="ana@comunicarlos.com.ar",
            rol=RolUsuario.OPERADOR,
            password_plano="clave123",
        )
        # Assert
        self.assertIsInstance(id_, str)
        self.assertTrue(len(id_) > 0)

    def test_registrar_persiste_usuario(self):
        # Arrange / Act
        id_ = self.servicio.registrar(
            nombre="Ana García",
            email="ana@comunicarlos.com.ar",
            rol=RolUsuario.OPERADOR,
            password_plano="clave123",
        )
        # Assert — puede recuperarse del repositorio
        usuario = self.servicio.obtener(id_)
        self.assertEqual(usuario.email, "ana@comunicarlos.com.ar")
        self.assertEqual(usuario.rol, RolUsuario.OPERADOR)

    def test_registrar_hashea_password(self):
        # Arrange / Act
        id_ = self.servicio.registrar(
            nombre="Ana García",
            email="ana@comunicarlos.com.ar",
            rol=RolUsuario.OPERADOR,
            password_plano="clave123",
        )
        # Assert — el hash no es el texto plano
        usuario = self.servicio.obtener(id_)
        self.assertNotEqual(usuario.password_hash, "clave123")
        self.assertEqual(usuario.password_hash, "hashed:clave123")

    def test_registrar_email_duplicado_falla(self):
        # Arrange
        self.servicio.registrar(
            nombre="Ana García",
            email="ana@comunicarlos.com.ar",
            rol=RolUsuario.OPERADOR,
            password_plano="clave123",
        )
        # Act / Assert
        with self.assertRaises(EmailDuplicado):
            self.servicio.registrar(
                nombre="Otra Ana",
                email="ana@comunicarlos.com.ar",
                rol=RolUsuario.TECNICO,
                password_plano="otraclav",
            )

    def test_registrar_nombre_vacio_falla(self):
        # Arrange / Act / Assert — ValueError del dominio se propaga
        with self.assertRaises(ValueError):
            self.servicio.registrar(
                nombre="",
                email="x@x.com",
                rol=RolUsuario.SOLICITANTE,
                password_plano="clave",
            )

    def test_registrar_email_sin_arroba_falla(self):
        with self.assertRaises(ValueError):
            self.servicio.registrar(
                nombre="Carlos",
                email="sin_arroba",
                rol=RolUsuario.SOLICITANTE,
                password_plano="clave",
            )


class TestAutenticarUsuario(unittest.TestCase):
    """S-U02 — Autenticar usuario."""

    def setUp(self):
        self.servicio = _hacer_servicio()
        self.id_ = self.servicio.registrar(
            nombre="Pedro López",
            email="pedro@comunicarlos.com.ar",
            rol=RolUsuario.TECNICO,
            password_plano="secreto",
        )

    def tearDown(self):
        pass

    def test_autenticar_credenciales_correctas_retorna_usuario(self):
        # Arrange (setUp)
        # Act
        usuario = self.servicio.autenticar("pedro@comunicarlos.com.ar", "secreto")
        # Assert
        self.assertEqual(usuario.id, self.id_)
        self.assertEqual(usuario.email, "pedro@comunicarlos.com.ar")

    def test_autenticar_actualiza_ultimo_acceso(self):
        # Arrange
        usuario_antes = self.servicio.obtener(self.id_)
        self.assertIsNone(usuario_antes.ultimo_acceso)
        # Act
        self.servicio.autenticar("pedro@comunicarlos.com.ar", "secreto")
        # Assert
        usuario_despues = self.servicio.obtener(self.id_)
        self.assertIsNotNone(usuario_despues.ultimo_acceso)

    def test_autenticar_email_inexistente_falla(self):
        # Arrange / Act / Assert
        with self.assertRaises(CredencialesInvalidas):
            self.servicio.autenticar("noexiste@comunicarlos.com.ar", "secreto")

    def test_autenticar_password_incorrecto_falla(self):
        # Arrange / Act / Assert
        with self.assertRaises(CredencialesInvalidas):
            self.servicio.autenticar("pedro@comunicarlos.com.ar", "CLAVE_MAL")

    def test_autenticar_no_revela_si_email_o_password_es_el_error(self):
        # Arrange — misma excepción para ambos casos (no enumerar usuarios)
        exc_email = None
        exc_pass = None
        try:
            self.servicio.autenticar("noexiste@comunicarlos.com.ar", "secreto")
        except CredencialesInvalidas as e:
            exc_email = str(e)
        try:
            self.servicio.autenticar("pedro@comunicarlos.com.ar", "CLAVE_MAL")
        except CredencialesInvalidas as e:
            exc_pass = str(e)
        # Assert — mismo mensaje
        self.assertEqual(exc_email, exc_pass)


class TestObtenerUsuario(unittest.TestCase):
    """S-U03 — Obtener usuario por ID."""

    def setUp(self):
        self.servicio = _hacer_servicio()
        self.id_ = self.servicio.registrar(
            nombre="Laura",
            email="laura@empresa.com",
            rol=RolUsuario.SOLICITANTE,
            password_plano="pw",
        )

    def tearDown(self):
        pass

    def test_obtener_usuario_existente(self):
        # Arrange (setUp)
        # Act
        usuario = self.servicio.obtener(self.id_)
        # Assert
        self.assertEqual(usuario.id, self.id_)

    def test_obtener_usuario_inexistente_falla(self):
        # Arrange / Act / Assert
        with self.assertRaises(UsuarioNoEncontrado):
            self.servicio.obtener("id-que-no-existe")


class TestListarUsuarios(unittest.TestCase):
    """S-U04 — Listar usuarios."""

    def setUp(self):
        self.servicio = _hacer_servicio()

    def tearDown(self):
        pass

    def test_listar_repositorio_vacio(self):
        # Arrange (setUp — repo vacío)
        # Act / Assert
        self.assertEqual(self.servicio.listar(), [])

    def test_listar_retorna_todos(self):
        # Arrange
        self.servicio.registrar("U1", "u1@comunicarlos.com.ar", RolUsuario.OPERADOR, "pw")
        self.servicio.registrar("U2", "u2@comunicarlos.com.ar", RolUsuario.TECNICO, "pw")
        # Act
        resultado = self.servicio.listar()
        # Assert
        self.assertEqual(len(resultado), 2)


class TestDesactivarUsuario(unittest.TestCase):
    """S-U05 — Desactivar usuario."""

    def setUp(self):
        self.servicio = _hacer_servicio()
        self.id_ = self.servicio.registrar(
            nombre="Marcos",
            email="marcos@empresa.com",
            rol=RolUsuario.SUPERVISOR,
            password_plano="pw",
        )

    def tearDown(self):
        pass

    def test_desactivar_usuario_activo(self):
        # Arrange
        usuario = self.servicio.obtener(self.id_)
        self.assertTrue(usuario.activo)
        # Act
        self.servicio.desactivar(self.id_)
        # Assert
        usuario = self.servicio.obtener(self.id_)
        self.assertFalse(usuario.activo)

    def test_desactivar_usuario_inexistente_falla(self):
        # Arrange / Act / Assert
        with self.assertRaises(UsuarioNoEncontrado):
            self.servicio.desactivar("id-inexistente")


if __name__ == "__main__":
    unittest.main()
