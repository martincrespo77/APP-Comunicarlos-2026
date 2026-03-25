"""Tests de integración HTTP para app/usuarios/router.py.

Framework: unittest.TestCase + fastapi.testclient.TestClient.
Se mantiene unittest por consistencia con el resto del proyecto.
TestClient de FastAPI es completamente compatible con TestCase.

Estrategia de aislamiento:
  Cada clase de test instancia un ``_RepoUsuarioFresh`` propio en setUp
  e inyecta un UsuarioService aislado mediante app.dependency_overrides.
  tearDown limpia todos los overrides para evitar contaminación entre tests.

Qué se prueba:
  Comportamiento HTTP: status codes, estructura del JSON, mapeo de
  excepciones de aplicación a responses HTTP.

Qué NO se prueba:
  Lógica interna de dominio o servicios (ya cubierta en test_usuarios_dominio.py
  y test_usuarios_servicios.py).
"""

from __future__ import annotations

import hashlib
import unittest
from typing import Optional

from fastapi.testclient import TestClient

from main import app
from app.compartido.dominio import RolUsuario
from app.deps import UsuarioActual, get_current_user, get_usuario_service
from app.usuarios.dominio import Usuario
from app.usuarios.repositorio import RepositorioUsuario
from app.usuarios.servicios import UsuarioService


# ── Infraestructura de test ──────────────────────────────────────────

def _hasher(pw: str) -> str:
    return hashlib.sha256(pw.encode()).hexdigest()


def _verificador(pw: str, h: str) -> bool:
    return hashlib.sha256(pw.encode()).hexdigest() == h


class _RepoUsuarioFresh(RepositorioUsuario):
    """Repositorio en memoria sin estado compartido entre tests."""

    def __init__(self) -> None:
        self._store: dict[str, Usuario] = {}

    def guardar(self, u: Usuario) -> None:
        self._store[u.id] = u

    def obtener_por_id(self, uid: str) -> Optional[Usuario]:
        return self._store.get(uid)

    def obtener_por_email(self, email: str) -> Optional[Usuario]:
        return next((u for u in self._store.values() if u.email == email), None)

    def listar(self) -> list[Usuario]:
        return list(self._store.values())


_SUPERVISOR_ACTUAL = UsuarioActual(id="sys", rol=RolUsuario.SUPERVISOR)

_BODY_ANA = {
    "nombre": "Ana López",
    "email": "ana@empresa.com",
    "rol": "tecnico",
    "password": "secreto123",
}


class _BaseUsuarioTest(unittest.TestCase):
    """Base: cliente HTTP con repo fresco e inyección de dependencias."""

    def setUp(self):
        self._repo = _RepoUsuarioFresh()
        app.dependency_overrides[get_usuario_service] = lambda: UsuarioService(
            self._repo, _hasher, _verificador
        )
        app.dependency_overrides[get_current_user] = lambda: _SUPERVISOR_ACTUAL
        self.client = TestClient(app)

    def tearDown(self):
        app.dependency_overrides.clear()

    def _registrar(self, body: dict | None = None) -> dict:
        """Helper: POST /usuarios/ y devuelve el JSON de respuesta."""
        resp = self.client.post("/usuarios/", json=body or _BODY_ANA)
        return resp.json()


# ═══════════════════════════════════════════════════════════
#  POST /usuarios/ — Registrar
# ═══════════════════════════════════════════════════════════


class TestRegistrarUsuario(_BaseUsuarioTest):

    def test_registro_exitoso_retorna_201(self):
        resp = self.client.post("/usuarios/", json=_BODY_ANA)
        self.assertEqual(resp.status_code, 201)

    def test_registro_exitoso_retorna_id_string(self):
        resp = self.client.post("/usuarios/", json=_BODY_ANA)
        data = resp.json()
        self.assertIn("id", data)
        self.assertIsInstance(data["id"], str)
        self.assertTrue(data["id"])  # no vacío

    def test_email_duplicado_retorna_409(self):
        self.client.post("/usuarios/", json=_BODY_ANA)          # primera vez OK
        resp = self.client.post("/usuarios/", json=_BODY_ANA)   # duplicado
        self.assertEqual(resp.status_code, 409)

    def test_email_sin_arroba_retorna_422(self):
        """El dominio rechaza el email → router lo convierte en 422."""
        body = {**_BODY_ANA, "email": "sin-arroba.com"}
        resp = self.client.post("/usuarios/", json=body)
        self.assertEqual(resp.status_code, 422)

    def test_rol_desconocido_retorna_422_por_pydantic(self):
        """Pydantic rechaza el enum inválido antes de llegar al servicio."""
        body = {**_BODY_ANA, "rol": "jefe_supremo"}
        resp = self.client.post("/usuarios/", json=body)
        self.assertEqual(resp.status_code, 422)

    def test_campo_faltante_retorna_422_por_pydantic(self):
        body = {"nombre": "Sin email", "rol": "tecnico", "password": "pw"}
        resp = self.client.post("/usuarios/", json=body)
        self.assertEqual(resp.status_code, 422)


# ═══════════════════════════════════════════════════════════
#  POST /usuarios/autenticar — Autenticar
# ═══════════════════════════════════════════════════════════


class TestAutenticarUsuario(_BaseUsuarioTest):

    def setUp(self):
        super().setUp()
        self._registrar()   # precondición: usuario registrado

    def _autenticar(self, email: str = "ana@empresa.com", pw: str = "secreto123"):
        return self.client.post("/usuarios/autenticar", json={"email": email, "password": pw})

    def test_credenciales_correctas_retornan_200(self):
        resp = self._autenticar()
        self.assertEqual(resp.status_code, 200)

    def test_respuesta_incluye_access_token_y_token_type(self):
        """Autenticar devuelve TokenOut, no UsuarioOut."""
        data = self._autenticar().json()
        self.assertIn("access_token", data)
        self.assertIn("token_type", data)
        self.assertEqual(data["token_type"], "bearer")
        self.assertIsInstance(data["access_token"], str)
        self.assertTrue(data["access_token"])

    def test_respuesta_no_expone_datos_personales_ni_password_hash(self):
        """El token no debe incluir id, nombre, email ni password_hash."""
        data = self._autenticar().json()
        for campo_sensible in ("password_hash", "password", "id", "nombre", "email"):
            self.assertNotIn(campo_sensible, data)

    def test_email_inexistente_retorna_401(self):
        resp = self._autenticar(email="noexiste@empresa.com")
        self.assertEqual(resp.status_code, 401)

    def test_password_incorrecto_retorna_401(self):
        resp = self._autenticar(pw="clave_incorrecta")
        self.assertEqual(resp.status_code, 401)


# ═══════════════════════════════════════════════════════════
#  GET /usuarios/ — Listar
# ═══════════════════════════════════════════════════════════


class TestListarUsuarios(_BaseUsuarioTest):

    def test_lista_vacia_retorna_200(self):
        resp = self.client.get("/usuarios/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json(), [])

    def test_lista_con_usuarios_retorna_200_con_elementos(self):
        self._registrar()
        resp = self.client.get("/usuarios/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.json()), 1)

    def test_lista_no_expone_password_hash(self):
        self._registrar()
        for usuario in self.client.get("/usuarios/").json():
            self.assertNotIn("password_hash", usuario)
            self.assertNotIn("password", usuario)

    def test_rol_operador_puede_listar(self):
        """OPERADOR tiene acceso para gestionar tickets."""
        app.dependency_overrides[get_current_user] = lambda: UsuarioActual(
            id="op-1", rol=RolUsuario.OPERADOR
        )
        resp = self.client.get("/usuarios/")
        self.assertEqual(resp.status_code, 200)

    def test_rol_tecnico_no_puede_listar_retorna_403(self):
        """TECNICO no tiene acceso al padrón completo."""
        app.dependency_overrides[get_current_user] = lambda: UsuarioActual(
            id="tec-1", rol=RolUsuario.TECNICO
        )
        resp = self.client.get("/usuarios/")
        self.assertEqual(resp.status_code, 403)

    def test_rol_solicitante_no_puede_listar_retorna_403(self):
        app.dependency_overrides[get_current_user] = lambda: UsuarioActual(
            id="sol-1", rol=RolUsuario.SOLICITANTE
        )
        resp = self.client.get("/usuarios/")
        self.assertEqual(resp.status_code, 403)


# ═══════════════════════════════════════════════════════════
#  GET /usuarios/{id} — Obtener por ID
# ═══════════════════════════════════════════════════════════


class TestObtenerUsuario(_BaseUsuarioTest):

    def test_usuario_existente_retorna_200_con_dto(self):
        uid = self._registrar()["id"]
        resp = self.client.get(f"/usuarios/{uid}")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["id"], uid)
        self.assertEqual(resp.json()["email"], "ana@empresa.com")

    def test_usuario_inexistente_retorna_404(self):
        resp = self.client.get("/usuarios/id-que-no-existe")
        self.assertEqual(resp.status_code, 404)

    def test_dto_no_expone_password_hash(self):
        uid = self._registrar()["id"]
        data = self.client.get(f"/usuarios/{uid}").json()
        self.assertNotIn("password_hash", data)

    def test_propio_usuario_puede_ver_su_perfil(self):
        """Un usuario con cualquier rol puede ver su propio perfil."""
        uid = self._registrar()["id"]
        app.dependency_overrides[get_current_user] = lambda: UsuarioActual(
            id=uid, rol=RolUsuario.TECNICO
        )
        resp = self.client.get(f"/usuarios/{uid}")
        self.assertEqual(resp.status_code, 200)

    def test_tecnico_no_puede_ver_perfil_ajeno_retorna_403(self):
        uid = self._registrar()["id"]
        app.dependency_overrides[get_current_user] = lambda: UsuarioActual(
            id="otro-id", rol=RolUsuario.TECNICO
        )
        resp = self.client.get(f"/usuarios/{uid}")
        self.assertEqual(resp.status_code, 403)

    def test_solicitante_no_puede_ver_perfil_ajeno_retorna_403(self):
        uid = self._registrar()["id"]
        app.dependency_overrides[get_current_user] = lambda: UsuarioActual(
            id="sol-otro", rol=RolUsuario.SOLICITANTE
        )
        resp = self.client.get(f"/usuarios/{uid}")
        self.assertEqual(resp.status_code, 403)

    def test_operador_puede_ver_perfil_ajeno(self):
        """OPERADOR necesita ver perfiles para gestionar asignaciones."""
        uid = self._registrar()["id"]
        app.dependency_overrides[get_current_user] = lambda: UsuarioActual(
            id="op-1", rol=RolUsuario.OPERADOR
        )
        resp = self.client.get(f"/usuarios/{uid}")
        self.assertEqual(resp.status_code, 200)


# ═══════════════════════════════════════════════════════════
#  DELETE /usuarios/{id} — Desactivar
# ═══════════════════════════════════════════════════════════


class TestDesactivarUsuario(_BaseUsuarioTest):

    def test_desactivar_existente_retorna_204(self):
        uid = self._registrar()["id"]
        resp = self.client.delete(f"/usuarios/{uid}")
        self.assertEqual(resp.status_code, 204)

    def test_desactivar_inexistente_retorna_404(self):
        resp = self.client.delete("/usuarios/fantasma-123")
        self.assertEqual(resp.status_code, 404)

    def test_usuario_desactivado_queda_con_activo_false(self):
        uid = self._registrar()["id"]
        self.client.delete(f"/usuarios/{uid}")
        data = self.client.get(f"/usuarios/{uid}").json()
        self.assertFalse(data["activo"])

    def test_operador_no_puede_desactivar_retorna_403(self):
        """Solo SUPERVISOR puede desactivar cuentas."""
        uid = self._registrar()["id"]
        app.dependency_overrides[get_current_user] = lambda: UsuarioActual(
            id="op-1", rol=RolUsuario.OPERADOR
        )
        resp = self.client.delete(f"/usuarios/{uid}")
        self.assertEqual(resp.status_code, 403)

    def test_tecnico_no_puede_desactivar_retorna_403(self):
        uid = self._registrar()["id"]
        app.dependency_overrides[get_current_user] = lambda: UsuarioActual(
            id="tec-1", rol=RolUsuario.TECNICO
        )
        resp = self.client.delete(f"/usuarios/{uid}")
        self.assertEqual(resp.status_code, 403)


if __name__ == "__main__":
    unittest.main()
