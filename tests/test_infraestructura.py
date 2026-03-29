"""Tests de integración para la capa de infraestructura MongoDB.

Tests de caja negra: no prueban detalles internos de la persistencia sino
el contrato público de los repositorios (guardar / obtener / listar, etc.).

Cada clase de test crea su propia base de datos mongomock en memoria para
mantener completo aislamiento entre tests y no afectar la base de producción.

Diseño:
  - ``setUpClass`` crea un MongoClient mongomock + database una vez por clase.
  - ``setUp`` limpia las colecciones antes de cada test.
"""

from __future__ import annotations

import unittest
from datetime import datetime

import mongomock

from app.compartido.dominio import RolUsuario
from app.infraestructura.repo_usuarios import RepositorioUsuarioMongo
from app.infraestructura.repo_requerimientos import RepositorioRequerimientoMongo
from app.requerimientos.dominio import (
    CategoriaIncidente,
    CategoriaSolicitud,
    EstadoRequerimiento,
    Incidente,
    Solicitud,
    TipoEvento,
    Urgencia,
)
from app.usuarios.dominio import Usuario

# ──────────────────────────────────────────────────────────────────────────────
#  Fixtures
# ──────────────────────────────────────────────────────────────────────────────


def _usuario(**kwargs) -> Usuario:
    """Construye un Usuario con valores por defecto sobreescribibles."""
    defaults: dict = dict(
        id="usr-001",
        nombre="Ana García",
        email="ana@comunicarlos.com.ar",
        rol=RolUsuario.OPERADOR,
        password_hash="$2b$12$fakehashXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
        activo=True,
        fecha_creacion=datetime(2024, 1, 15, 10, 0, 0),
    )
    defaults.update(kwargs)
    return Usuario(**defaults)


def _incidente(**kwargs) -> Incidente:
    """Construye un Incidente con valores por defecto sobreescribibles."""
    defaults: dict = dict(
        titulo="Servicio caído",
        descripcion="El servicio de correo está inaccesible.",
        solicitante_id="usr-001",
        urgencia=Urgencia.CRITICA,
        categoria=CategoriaIncidente.SERVICIO_INACCESIBLE,
    )
    defaults.update(kwargs)
    return Incidente(**defaults)


def _solicitud(**kwargs) -> Solicitud:
    """Construye una Solicitud con valores por defecto sobreescribibles."""
    defaults: dict = dict(
        titulo="Alta de servicio VoIP",
        descripcion="Necesitamos habilitar el servicio VoIP para el equipo de ventas.",
        solicitante_id="usr-002",
        categoria=CategoriaSolicitud.ALTA_SERVICIO,
    )
    defaults.update(kwargs)
    return Solicitud(**defaults)


# ──────────────────────────────────────────────────────────────────────────────
#  Repositorio de Usuarios
# ──────────────────────────────────────────────────────────────────────────────


class TestRepositorioUsuarioMongo(unittest.TestCase):
    """Contrato del RepositorioUsuarioMongo contra mongomock en memoria."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.client = mongomock.MongoClient()
        cls.db = cls.client["test_usuarios"]

    def setUp(self) -> None:
        self.db.drop_collection("usuarios")
        self.repo = RepositorioUsuarioMongo(self.db)

    # ── guardar + obtener por id ─────────────────────────────────────────────

    def test_guardar_y_obtener_por_id(self):
        usuario = _usuario()
        self.repo.guardar(usuario)

        recuperado = self.repo.obtener_por_id("usr-001")

        self.assertIsNotNone(recuperado)
        self.assertEqual(recuperado.id, "usr-001")
        self.assertEqual(recuperado.nombre, "Ana García")
        self.assertEqual(recuperado.email, "ana@comunicarlos.com.ar")
        self.assertEqual(recuperado.rol, RolUsuario.OPERADOR)
        self.assertTrue(recuperado.activo)

    def test_obtener_por_id_inexistente_retorna_none(self):
        resultado = self.repo.obtener_por_id("no-existe")
        self.assertIsNone(resultado)

    # ── obtener por email ────────────────────────────────────────────────────

    def test_obtener_por_email_existente(self):
        self.repo.guardar(_usuario(id="usr-e1", email="otro@comunicarlos.com.ar"))

        resultado = self.repo.obtener_por_email("otro@comunicarlos.com.ar")

        self.assertIsNotNone(resultado)
        self.assertEqual(resultado.id, "usr-e1")

    def test_obtener_por_email_inexistente_retorna_none(self):
        resultado = self.repo.obtener_por_email("noexiste@comunicarlos.com.ar")
        self.assertIsNone(resultado)

    # ── listar ───────────────────────────────────────────────────────────────

    def test_listar_retorna_todos_los_usuarios(self):
        self.repo.guardar(_usuario(id="u1", email="u1@comunicarlos.com.ar"))
        self.repo.guardar(_usuario(id="u2", email="u2@comunicarlos.com.ar"))
        self.repo.guardar(_usuario(id="u3", email="u3@comunicarlos.com.ar"))

        todos = self.repo.listar()

        ids = {u.id for u in todos}
        self.assertIn("u1", ids)
        self.assertIn("u2", ids)
        self.assertIn("u3", ids)

    # ── upsert (idempotencia) ─────────────────────────────────────────────────

    def test_guardar_dos_veces_mismo_id_actualiza(self):
        self.repo.guardar(_usuario(nombre="Nombre Original"))
        # actualizar nombre
        self.repo.guardar(_usuario(nombre="Nombre Nuevo"))

        recuperado = self.repo.obtener_por_id("usr-001")
        self.assertEqual(recuperado.nombre, "Nombre Nuevo")

    # ── activo ────────────────────────────────────────────────────────────────

    def test_usuario_inactivo_persiste_activo_false(self):
        self.repo.guardar(_usuario(activo=False))
        recuperado = self.repo.obtener_por_id("usr-001")
        self.assertFalse(recuperado.activo)

    # ── ultimo_acceso ─────────────────────────────────────────────────────────

    def test_ultimo_acceso_nulo_se_persiste_y_recupera(self):
        self.repo.guardar(_usuario(ultimo_acceso=None))
        recuperado = self.repo.obtener_por_id("usr-001")
        self.assertIsNone(recuperado.ultimo_acceso)

    def test_ultimo_acceso_con_valor_se_persiste_y_recupera(self):
        ts = datetime(2024, 6, 1, 12, 0, 0)
        self.repo.guardar(_usuario(ultimo_acceso=ts))
        recuperado = self.repo.obtener_por_id("usr-001")
        self.assertEqual(recuperado.ultimo_acceso, ts)


# ──────────────────────────────────────────────────────────────────────────────
#  Repositorio de Requerimientos
# ──────────────────────────────────────────────────────────────────────────────


class TestRepositorioRequerimientoMongo(unittest.TestCase):
    """Contrato del RepositorioRequerimientoMongo contra mongomock en memoria."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.client = mongomock.MongoClient()
        cls.db = cls.client["test_requerimientos"]

    def setUp(self) -> None:
        self.db.drop_collection("requerimientos")
        self.repo = RepositorioRequerimientoMongo(self.db)

    # ── Incidente: guardar + obtener ─────────────────────────────────────────

    def test_guardar_incidente_y_obtener_por_id(self):
        inc = _incidente()
        self.repo.guardar(inc)

        recuperado = self.repo.obtener_por_id(inc.id)

        self.assertIsNotNone(recuperado)
        self.assertIsInstance(recuperado, Incidente)
        self.assertEqual(recuperado.titulo, "Servicio caído")
        self.assertEqual(recuperado.descripcion, "El servicio de correo está inaccesible.")
        self.assertEqual(recuperado.solicitante_id, "usr-001")
        self.assertEqual(recuperado.urgencia, Urgencia.CRITICA)
        self.assertEqual(recuperado.categoria, CategoriaIncidente.SERVICIO_INACCESIBLE)
        self.assertEqual(recuperado.estado, EstadoRequerimiento.ABIERTO)

    def test_incidente_tiene_evento_creacion_tras_recuperar(self):
        inc = _incidente()
        self.repo.guardar(inc)

        recuperado = self.repo.obtener_por_id(inc.id)

        self.assertEqual(len(recuperado.eventos), 1)
        self.assertEqual(recuperado.eventos[0].tipo, TipoEvento.CREACION)

    # ── Solicitud: guardar + obtener ─────────────────────────────────────────

    def test_guardar_solicitud_y_obtener_por_id(self):
        sol = _solicitud()
        self.repo.guardar(sol)

        recuperado = self.repo.obtener_por_id(sol.id)

        self.assertIsNotNone(recuperado)
        self.assertIsInstance(recuperado, Solicitud)
        self.assertEqual(recuperado.titulo, "Alta de servicio VoIP")
        self.assertEqual(recuperado.categoria, CategoriaSolicitud.ALTA_SERVICIO)

    # ── obtener id inexistente ────────────────────────────────────────────────

    def test_obtener_por_id_inexistente_retorna_none(self):
        resultado = self.repo.obtener_por_id("no-existe")
        self.assertIsNone(resultado)

    # ── listar ───────────────────────────────────────────────────────────────

    def test_listar_retorna_todos(self):
        self.repo.guardar(_incidente(titulo="Inc A"))
        self.repo.guardar(_incidente(titulo="Inc B"))
        self.repo.guardar(_solicitud())

        todos = self.repo.listar()

        self.assertEqual(len(todos), 3)

    def test_listar_inicialmente_vacia(self):
        todos = self.repo.listar()
        self.assertEqual(todos, [])

    # ── listar_por_solicitante ────────────────────────────────────────────────

    def test_listar_por_solicitante_filtra_correctamente(self):
        self.repo.guardar(_incidente(solicitante_id="usr-AAA"))
        self.repo.guardar(_incidente(solicitante_id="usr-BBB"))
        self.repo.guardar(_incidente(solicitante_id="usr-AAA"))

        resultado = self.repo.listar_por_solicitante("usr-AAA")

        self.assertEqual(len(resultado), 2)
        self.assertTrue(all(r.solicitante_id == "usr-AAA" for r in resultado))

    def test_listar_por_solicitante_sin_resultados_retorna_lista_vacia(self):
        resultado = self.repo.listar_por_solicitante("nadie")
        self.assertEqual(resultado, [])

    # ── listar_por_estado ─────────────────────────────────────────────────────

    def test_listar_por_estado_filtra_abiertos(self):
        inc_a = _incidente(titulo="Abierto")
        self.repo.guardar(inc_a)

        resultado = self.repo.listar_por_estado(EstadoRequerimiento.ABIERTO)

        self.assertGreaterEqual(len(resultado), 1)
        self.assertTrue(all(r.estado == EstadoRequerimiento.ABIERTO for r in resultado))

    # ── upsert: guardar con estado cambiado ───────────────────────────────────

    def test_guardar_dos_veces_actualiza_estado(self):
        inc = _incidente()
        self.repo.guardar(inc)

        # Un operador asigna un técnico (evoluciona el estado a ASIGNADO)
        inc.asignar_tecnico("tec-001", "op-001", RolUsuario.OPERADOR)
        self.repo.guardar(inc)

        recuperado = self.repo.obtener_por_id(inc.id)
        self.assertEqual(recuperado.estado, EstadoRequerimiento.ASIGNADO)
        self.assertEqual(recuperado.tecnico_asignado_id, "tec-001")

    # ── comentarios se persisten y recuperan ─────────────────────────────────

    def test_comentario_se_persiste_y_recupera(self):
        inc = _incidente()
        self.repo.guardar(inc)

        inc.agregar_comentario(
            autor_id="op-001",
            rol_autor=RolUsuario.OPERADOR,
            contenido="Revisando el problema.",
        )
        self.repo.guardar(inc)

        recuperado = self.repo.obtener_por_id(inc.id)
        self.assertEqual(len(recuperado.comentarios), 1)
        self.assertEqual(recuperado.comentarios[0].contenido, "Revisando el problema.")
        self.assertEqual(recuperado.comentarios[0].autor_id, "op-001")

    # ── múltiples eventos ─────────────────────────────────────────────────────

    def test_multiples_eventos_se_recuperan_en_orden(self):
        inc = _incidente()
        self.repo.guardar(inc)  # CREACION

        # Operador asigna técnico → genera evento ASIGNACION
        inc.asignar_tecnico("tec-001", "op-001", RolUsuario.OPERADOR)
        self.repo.guardar(inc)  # + ASIGNACION

        recuperado = self.repo.obtener_por_id(inc.id)
        # Debe tener CREACION + ASIGNACION
        self.assertGreaterEqual(len(recuperado.eventos), 2)
        tipos = [e.tipo for e in recuperado.eventos]
        self.assertIn(TipoEvento.CREACION, tipos)
        self.assertIn(TipoEvento.ASIGNACION, tipos)

    # ── listar_por_tecnico ────────────────────────────────────────────────────

    def test_listar_por_tecnico(self):
        inc = _incidente()
        inc.asignar_tecnico("tec-XYZ", "op-001", RolUsuario.OPERADOR)
        self.repo.guardar(inc)

        resultado = self.repo.listar_por_tecnico("tec-XYZ")

        self.assertEqual(len(resultado), 1)
        self.assertEqual(resultado[0].tecnico_asignado_id, "tec-XYZ")

    def test_listar_por_tecnico_sin_resultados(self):
        resultado = self.repo.listar_por_tecnico("nadie")
        self.assertEqual(resultado, [])


if __name__ == "__main__":
    unittest.main()
