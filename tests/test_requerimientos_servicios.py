"""Tests unitarios — capa de servicios de requerimientos.

Usa FakeRepositorioRequerimiento (dict en memoria) y DespachadorEventos real
(es puro, no produce I/O).  Sin base de datos real, sin FastAPI.

STYLEGUIDE_PROFE: unittest, setUp, tearDown, AAA, test_<comportamiento>.
"""

import unittest

from app.compartido.dominio import RolUsuario
from app.notificaciones.dominio import DespachadorEventos, ObservadorRequerimiento
from app.requerimientos.dominio import (
    CategoriaIncidente,
    CategoriaSolicitud,
    EstadoRequerimiento,
    Requerimiento,
    TipoEvento,
    TipoRequerimiento,
    Urgencia,
)
from app.requerimientos.excepciones import OperacionNoAutorizada, TransicionEstadoInvalida
from app.requerimientos.excepciones_aplicacion import RequerimientoNoEncontrado
from app.requerimientos.repositorio import RepositorioRequerimiento
from app.requerimientos.servicios import RequerimientoService


# ── Fake de repositorio ───────────────────────────────────────────────────────

class FakeRepositorioRequerimiento(RepositorioRequerimiento):
    """Implementación en memoria para tests."""

    def __init__(self):
        self._por_id: dict[str, Requerimiento] = {}

    def guardar(self, requerimiento: Requerimiento) -> None:
        self._por_id[requerimiento.id] = requerimiento

    def obtener_por_id(self, requerimiento_id: str) -> Requerimiento | None:
        return self._por_id.get(requerimiento_id)

    def listar(self) -> list[Requerimiento]:
        return list(self._por_id.values())

    def listar_por_solicitante(self, solicitante_id: str) -> list[Requerimiento]:
        return [r for r in self._por_id.values() if r.solicitante_id == solicitante_id]

    def listar_por_tecnico(self, tecnico_id: str) -> list[Requerimiento]:
        return [r for r in self._por_id.values() if r.tecnico_asignado_id == tecnico_id]

    def listar_por_estado(self, estado: EstadoRequerimiento) -> list[Requerimiento]:
        return [r for r in self._por_id.values() if r.estado == estado]


# ── Observador espía ──────────────────────────────────────────────────────────

class ObservadorEspia(ObservadorRequerimiento):
    """Captura eventos recibidos para verificar el despacho."""

    def __init__(self):
        self.eventos_recibidos: list[tuple] = []

    def notificar(self, evento, requerimiento_id: str) -> None:
        self.eventos_recibidos.append((evento, requerimiento_id))


# ── Helper ────────────────────────────────────────────────────────────────────

def _hacer_servicio(espia: ObservadorEspia | None = None):
    repo = FakeRepositorioRequerimiento()
    despachador = DespachadorEventos()
    if espia:
        despachador.registrar(espia)
    return RequerimientoService(repo=repo, despachador=despachador), repo


# ══════════════════════════════════════════════════════════════════════════════
#  Tests: creación
# ══════════════════════════════════════════════════════════════════════════════

class TestCrearIncidente(unittest.TestCase):
    """S-R01 — Crear incidente."""

    def setUp(self):
        self.espia = ObservadorEspia()
        self.servicio, self.repo = _hacer_servicio(self.espia)

    def tearDown(self):
        pass

    def test_crear_incidente_retorna_id(self):
        # Arrange / Act
        id_ = self.servicio.crear_incidente(
            titulo="Sin internet",
            descripcion="La red cayó",
            solicitante_id="sol-1",
            urgencia=Urgencia.CRITICA,
            categoria=CategoriaIncidente.SERVICIO_INACCESIBLE,
        )
        # Assert
        self.assertIsInstance(id_, str)

    def test_crear_incidente_persiste_en_repositorio(self):
        # Arrange / Act
        id_ = self.servicio.crear_incidente(
            titulo="Sin internet",
            descripcion="La red cayó",
            solicitante_id="sol-1",
            urgencia=Urgencia.CRITICA,
            categoria=CategoriaIncidente.SERVICIO_INACCESIBLE,
        )
        # Assert
        req = self.repo.obtener_por_id(id_)
        self.assertIsNotNone(req)
        self.assertEqual(req.tipo, TipoRequerimiento.INCIDENTE)
        self.assertEqual(req.estado, EstadoRequerimiento.ABIERTO)

    def test_crear_incidente_despacha_evento_creacion(self):
        # Arrange / Act
        id_ = self.servicio.crear_incidente(
            titulo="Sin internet",
            descripcion="La red cayó",
            solicitante_id="sol-1",
            urgencia=Urgencia.CRITICA,
            categoria=CategoriaIncidente.SERVICIO_INACCESIBLE,
        )
        # Assert
        self.assertEqual(len(self.espia.eventos_recibidos), 1)
        evento, req_id = self.espia.eventos_recibidos[0]
        self.assertEqual(evento.tipo, TipoEvento.CREACION)
        self.assertEqual(req_id, id_)

    def test_crear_incidente_titulo_vacio_falla(self):
        # Arrange / Act / Assert — ValueError del dominio se propaga
        with self.assertRaises(ValueError):
            self.servicio.crear_incidente(
                titulo="",
                descripcion="algo",
                solicitante_id="sol-1",
                urgencia=Urgencia.MENOR,
                categoria=CategoriaIncidente.BLOQUEO_SIM,
            )


class TestCrearSolicitud(unittest.TestCase):
    """S-R02 — Crear solicitud."""

    def setUp(self):
        self.servicio, self.repo = _hacer_servicio()

    def tearDown(self):
        pass

    def test_crear_solicitud_retorna_id(self):
        # Arrange / Act
        id_ = self.servicio.crear_solicitud(
            titulo="Alta de línea",
            descripcion="Nuevo empleado",
            solicitante_id="sol-2",
            categoria=CategoriaSolicitud.ALTA_SERVICIO,
        )
        # Assert
        self.assertIsInstance(id_, str)

    def test_crear_solicitud_persiste_tipo_correcto(self):
        # Arrange / Act
        id_ = self.servicio.crear_solicitud(
            titulo="Alta de línea",
            descripcion="Nuevo empleado",
            solicitante_id="sol-2",
            categoria=CategoriaSolicitud.ALTA_SERVICIO,
        )
        # Assert
        req = self.repo.obtener_por_id(id_)
        self.assertEqual(req.tipo, TipoRequerimiento.SOLICITUD)


# ══════════════════════════════════════════════════════════════════════════════
#  Tests: ciclo de vida
# ══════════════════════════════════════════════════════════════════════════════

class TestAsignarTecnico(unittest.TestCase):
    """S-R03 — Asignar técnico via servicio."""

    def setUp(self):
        self.espia = ObservadorEspia()
        self.servicio, self.repo = _hacer_servicio(self.espia)
        self.req_id = self.servicio.crear_incidente(
            titulo="Falla red",
            descripcion="Sin acceso",
            solicitante_id="sol-1",
            urgencia=Urgencia.IMPORTANTE,
            categoria=CategoriaIncidente.SERVICIO_INACCESIBLE,
        )
        self.espia.eventos_recibidos.clear()

    def tearDown(self):
        pass

    def test_asignar_tecnico_cambia_estado_a_asignado(self):
        # Arrange (setUp)
        # Act
        self.servicio.asignar_tecnico(
            self.req_id, "tec-1", "op-1", RolUsuario.OPERADOR
        )
        # Assert
        req = self.repo.obtener_por_id(self.req_id)
        self.assertEqual(req.estado, EstadoRequerimiento.ASIGNADO)
        self.assertEqual(req.tecnico_asignado_id, "tec-1")

    def test_asignar_tecnico_despacha_evento_asignacion(self):
        # Arrange (setUp)
        # Act
        self.servicio.asignar_tecnico(
            self.req_id, "tec-1", "op-1", RolUsuario.OPERADOR
        )
        # Assert
        self.assertEqual(len(self.espia.eventos_recibidos), 1)
        evento, _ = self.espia.eventos_recibidos[0]
        self.assertEqual(evento.tipo, TipoEvento.ASIGNACION)

    def test_asignar_tecnico_requerimiento_inexistente_falla(self):
        # Arrange / Act / Assert
        with self.assertRaises(RequerimientoNoEncontrado):
            self.servicio.asignar_tecnico(
                "id-falso", "tec-1", "op-1", RolUsuario.OPERADOR
            )

    def test_asignar_tecnico_rol_incorrecto_falla(self):
        # Arrange / Act / Assert — excepción de dominio se propaga
        with self.assertRaises(OperacionNoAutorizada):
            self.servicio.asignar_tecnico(
                self.req_id, "tec-1", "sol-1", RolUsuario.SOLICITANTE
            )


class TestIniciarTrabajo(unittest.TestCase):
    """S-R04 — Iniciar trabajo via servicio."""

    def setUp(self):
        self.servicio, self.repo = _hacer_servicio()
        self.req_id = self.servicio.crear_incidente(
            titulo="Falla red",
            descripcion="Desc",
            solicitante_id="sol-1",
            urgencia=Urgencia.MENOR,
            categoria=CategoriaIncidente.BLOQUEO_SIM,
        )
        self.servicio.asignar_tecnico(
            self.req_id, "tec-1", "op-1", RolUsuario.OPERADOR
        )

    def tearDown(self):
        pass

    def test_iniciar_trabajo_cambia_estado_a_en_progreso(self):
        # Arrange (setUp)
        # Act
        self.servicio.iniciar_trabajo(self.req_id, "tec-1")
        # Assert
        req = self.repo.obtener_por_id(self.req_id)
        self.assertEqual(req.estado, EstadoRequerimiento.EN_PROGRESO)

    def test_iniciar_trabajo_tecnico_incorrecto_falla(self):
        # Arrange / Act / Assert — excepción de dominio se propaga
        with self.assertRaises(OperacionNoAutorizada):
            self.servicio.iniciar_trabajo(self.req_id, "tec-OTRO")


class TestResolver(unittest.TestCase):
    """S-R05 — Resolver via servicio."""

    def setUp(self):
        self.servicio, self.repo = _hacer_servicio()
        self.req_id = self.servicio.crear_incidente(
            titulo="Falla red",
            descripcion="Desc",
            solicitante_id="sol-1",
            urgencia=Urgencia.MENOR,
            categoria=CategoriaIncidente.BLOQUEO_SIM,
        )
        self.servicio.asignar_tecnico(
            self.req_id, "tec-1", "op-1", RolUsuario.OPERADOR
        )
        self.servicio.iniciar_trabajo(self.req_id, "tec-1")

    def tearDown(self):
        pass

    def test_resolver_cambia_estado_a_resuelto(self):
        # Arrange (setUp)
        # Act
        self.servicio.resolver(self.req_id, "tec-1")
        # Assert
        req = self.repo.obtener_por_id(self.req_id)
        self.assertEqual(req.estado, EstadoRequerimiento.RESUELTO)

    def test_resolver_tecnico_incorrecto_falla(self):
        # Arrange / Act / Assert
        with self.assertRaises(OperacionNoAutorizada):
            self.servicio.resolver(self.req_id, "tec-OTRO")

    def test_resolver_requerimiento_inexistente_falla(self):
        # Arrange / Act / Assert
        with self.assertRaises(RequerimientoNoEncontrado):
            self.servicio.resolver("id-falso", "tec-1")


class TestDerivar(unittest.TestCase):
    """S-R06 — Derivar via servicio."""

    def setUp(self):
        self.servicio, self.repo = _hacer_servicio()
        self.req_id = self.servicio.crear_incidente(
            titulo="Falla red",
            descripcion="Desc",
            solicitante_id="sol-1",
            urgencia=Urgencia.IMPORTANTE,
            categoria=CategoriaIncidente.SERVICIO_INACCESIBLE,
        )
        self.servicio.asignar_tecnico(
            self.req_id, "tec-1", "op-1", RolUsuario.OPERADOR
        )

    def tearDown(self):
        pass

    def test_derivar_cambia_tecnico_asignado(self):
        # Arrange (setUp)
        # Act
        self.servicio.derivar(self.req_id, "tec-1", "tec-2", "Se requiere otra especialidad")
        # Assert
        req = self.repo.obtener_por_id(self.req_id)
        self.assertEqual(req.tecnico_asignado_id, "tec-2")

    def test_derivar_mismo_tecnico_falla(self):
        # Arrange / Act / Assert — excepción de dominio se propaga
        from app.requerimientos.excepciones import RequerimientoError
        with self.assertRaises(RequerimientoError):
            self.servicio.derivar(self.req_id, "tec-1", "tec-1", "motivo")

    def test_derivar_motivo_vacio_falla(self):
        from app.requerimientos.excepciones import RequerimientoError
        with self.assertRaises(RequerimientoError):
            self.servicio.derivar(self.req_id, "tec-1", "tec-2", "")


class TestAgregarComentario(unittest.TestCase):
    """S-R07 — Agregar comentario via servicio."""

    def setUp(self):
        self.espia = ObservadorEspia()
        self.servicio, self.repo = _hacer_servicio(self.espia)
        self.req_id = self.servicio.crear_incidente(
            titulo="Falla red",
            descripcion="Desc",
            solicitante_id="sol-1",
            urgencia=Urgencia.MENOR,
            categoria=CategoriaIncidente.BLOQUEO_SIM,
        )
        self.servicio.asignar_tecnico(
            self.req_id, "tec-1", "op-1", RolUsuario.OPERADOR
        )
        self.espia.eventos_recibidos.clear()

    def tearDown(self):
        pass

    def test_agregar_comentario_por_solicitante_propio(self):
        # Arrange (setUp — estado ASIGNADO)
        # Act
        self.servicio.agregar_comentario(
            self.req_id, "sol-1", RolUsuario.SOLICITANTE, "¿Hay novedades?"
        )
        # Assert
        req = self.repo.obtener_por_id(self.req_id)
        self.assertEqual(len(req.comentarios), 1)

    def test_agregar_comentario_supervisor_falla(self):
        # Arrange / Act / Assert — excepción de dominio se propaga
        with self.assertRaises(OperacionNoAutorizada):
            self.servicio.agregar_comentario(
                self.req_id, "sup-1", RolUsuario.SUPERVISOR, "Solo veo"
            )

    def test_agregar_comentario_despacha_evento(self):
        # Arrange (setUp)
        # Act
        self.servicio.agregar_comentario(
            self.req_id, "sol-1", RolUsuario.SOLICITANTE, "¿Hay novedades?"
        )
        # Assert
        self.assertEqual(len(self.espia.eventos_recibidos), 1)
        evento, _ = self.espia.eventos_recibidos[0]
        self.assertEqual(evento.tipo, TipoEvento.COMENTARIO)

    def test_comentario_en_resuelto_por_operador_reabre_y_despacha_dos_eventos(self):
        # Arrange — llevar a RESUELTO
        self.servicio.iniciar_trabajo(self.req_id, "tec-1")
        self.servicio.resolver(self.req_id, "tec-1")
        self.espia.eventos_recibidos.clear()
        # Act
        self.servicio.agregar_comentario(
            self.req_id, "op-1", RolUsuario.OPERADOR, "Necesita revisión"
        )
        # Assert — comentario + reapertura = 2 eventos despachados
        tipos = [e.tipo for e, _ in self.espia.eventos_recibidos]
        self.assertIn(TipoEvento.COMENTARIO, tipos)
        self.assertIn(TipoEvento.REAPERTURA, tipos)
        req = self.repo.obtener_por_id(self.req_id)
        self.assertEqual(req.estado, EstadoRequerimiento.REABIERTO)


# ══════════════════════════════════════════════════════════════════════════════
#  Tests: consultas
# ══════════════════════════════════════════════════════════════════════════════

class TestConsultas(unittest.TestCase):
    """S-R08 — Consultas vía servicio."""

    def setUp(self):
        self.servicio, self.repo = _hacer_servicio()
        # req1: sol-A, tec-1, asignado
        self.id1 = self.servicio.crear_incidente(
            titulo="Inc 1", descripcion="Desc",
            solicitante_id="sol-A",
            urgencia=Urgencia.CRITICA,
            categoria=CategoriaIncidente.SERVICIO_INACCESIBLE,
        )
        self.servicio.asignar_tecnico(self.id1, "tec-1", "op-1", RolUsuario.OPERADOR)
        # req2: sol-B, sin asignar (abierto)
        self.id2 = self.servicio.crear_solicitud(
            titulo="Sol 1", descripcion="Desc",
            solicitante_id="sol-B",
            categoria=CategoriaSolicitud.ALTA_SERVICIO,
        )

    def tearDown(self):
        pass

    def test_obtener_requerimiento_existente(self):
        # Arrange (setUp)
        # Act
        req = self.servicio.obtener(self.id1)
        # Assert
        self.assertEqual(req.id, self.id1)

    def test_obtener_requerimiento_inexistente_falla(self):
        # Arrange / Act / Assert
        with self.assertRaises(RequerimientoNoEncontrado):
            self.servicio.obtener("id-falso")

    def test_listar_retorna_todos(self):
        # Arrange (setUp)
        # Act
        resultado = self.servicio.listar()
        # Assert
        self.assertEqual(len(resultado), 2)

    def test_listar_por_solicitante(self):
        # Arrange (setUp)
        # Act
        resultado = self.servicio.listar_por_solicitante("sol-A")
        # Assert
        self.assertEqual(len(resultado), 1)
        self.assertEqual(resultado[0].id, self.id1)

    def test_listar_por_solicitante_otro_no_ve_ajenos(self):
        # Arrange (setUp)
        # Act
        resultado = self.servicio.listar_por_solicitante("sol-B")
        # Assert — sol-B solo ve su solicitud
        self.assertEqual(len(resultado), 1)
        self.assertEqual(resultado[0].id, self.id2)

    def test_listar_por_tecnico(self):
        # Arrange (setUp)
        # Act
        resultado = self.servicio.listar_por_tecnico("tec-1")
        # Assert
        self.assertEqual(len(resultado), 1)
        self.assertEqual(resultado[0].id, self.id1)

    def test_listar_por_estado_abierto(self):
        # Arrange (setUp)
        # Act
        resultado = self.servicio.listar_por_estado(EstadoRequerimiento.ABIERTO)
        # Assert — solo id2 está ABIERTO
        ids = [r.id for r in resultado]
        self.assertIn(self.id2, ids)
        self.assertNotIn(self.id1, ids)

    def test_listar_por_estado_asignado(self):
        # Arrange (setUp)
        # Act
        resultado = self.servicio.listar_por_estado(EstadoRequerimiento.ASIGNADO)
        # Assert — solo id1 está ASIGNADO
        ids = [r.id for r in resultado]
        self.assertIn(self.id1, ids)


if __name__ == "__main__":
    unittest.main()
