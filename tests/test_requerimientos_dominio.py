"""Tests unitarios — Dominio del módulo de requerimientos.

Cubre: enums, Comentario, Evento, Incidente, Solicitud, Requerimiento
(invariantes, transiciones, permisos, auditoría, eventos de dominio)
y RequerimientoFactory.

STYLEGUIDE_PROFE: unittest, setUp, tearDown, AAA, test_<comportamiento>.
"""

import unittest

from app.compartido.dominio import RolUsuario
from app.requerimientos.dominio import (
    CategoriaIncidente,
    CategoriaSolicitud,
    Comentario,
    EstadoRequerimiento,
    Evento,
    Incidente,
    RequerimientoFactory,
    Solicitud,
    TipoEvento,
    TipoRequerimiento,
    Urgencia,
)
from app.requerimientos.excepciones import (
    OperacionNoAutorizada,
    RequerimientoError,
    TransicionEstadoInvalida,
)

# ── Constantes de prueba ──
SOLICITANTE = "solicitante-001"
SOLICITANTE_OTRO = "solicitante-999"
OPERADOR = "operador-001"
TECNICO_A = "tecnico-001"
TECNICO_B = "tecnico-002"


# ═══════════════════════════════════════════════════════════
#  HELPERS
# ═══════════════════════════════════════════════════════════

def _crear_incidente(**kwargs) -> Incidente:
    defaults = dict(
        titulo="Servidor caído",
        descripcion="El servidor principal no responde",
        solicitante_id=SOLICITANTE,
        urgencia=Urgencia.CRITICA,
        categoria=CategoriaIncidente.SERVICIO_INACCESIBLE,
    )
    defaults.update(kwargs)
    return RequerimientoFactory.crear_incidente(**defaults)


def _crear_solicitud(**kwargs) -> Solicitud:
    defaults = dict(
        titulo="Alta de correo",
        descripcion="Necesito cuenta de correo corporativa",
        solicitante_id=SOLICITANTE,
        categoria=CategoriaSolicitud.ALTA_SERVICIO,
    )
    defaults.update(kwargs)
    return RequerimientoFactory.crear_solicitud(**defaults)


# ═══════════════════════════════════════════════════════════
#  ENUMS
# ═══════════════════════════════════════════════════════════

class TestEstadoRequerimiento(unittest.TestCase):
    """R01 — Verifica los estados del ciclo de vida."""

    def test_estados_tienen_cinco_valores(self):
        # Arrange / Act
        estados = list(EstadoRequerimiento)
        # Assert
        self.assertEqual(len(estados), 5)

    def test_estado_abierto_tiene_valor_correcto(self):
        self.assertEqual(EstadoRequerimiento.ABIERTO.value, "abierto")

    def test_estado_asignado_tiene_valor_correcto(self):
        self.assertEqual(EstadoRequerimiento.ASIGNADO.value, "asignado")

    def test_estado_en_progreso_tiene_valor_correcto(self):
        self.assertEqual(EstadoRequerimiento.EN_PROGRESO.value, "en_progreso")

    def test_estado_resuelto_tiene_valor_correcto(self):
        self.assertEqual(EstadoRequerimiento.RESUELTO.value, "resuelto")

    def test_estado_reabierto_tiene_valor_correcto(self):
        self.assertEqual(EstadoRequerimiento.REABIERTO.value, "reabierto")


class TestUrgencia(unittest.TestCase):
    """R02 — Verifica los valores de urgencia alineados al TP."""

    def test_urgencia_tiene_tres_valores_del_tp(self):
        self.assertEqual(len(list(Urgencia)), 3)

    def test_urgencia_critica_tiene_valor_correcto(self):
        self.assertEqual(Urgencia.CRITICA.value, "critica")

    def test_urgencia_importante_tiene_valor_correcto(self):
        self.assertEqual(Urgencia.IMPORTANTE.value, "importante")

    def test_urgencia_menor_tiene_valor_correcto(self):
        self.assertEqual(Urgencia.MENOR.value, "menor")


class TestCategorias(unittest.TestCase):
    """R03-R04 — Verifica las categorías alineadas al TP."""

    def test_categoria_incidente_tiene_tres_valores_del_tp(self):
        self.assertEqual(len(list(CategoriaIncidente)), 3)

    def test_categoria_incidente_servicio_inaccesible(self):
        self.assertEqual(
            CategoriaIncidente.SERVICIO_INACCESIBLE.value, "servicio_inaccesible"
        )

    def test_categoria_incidente_bloqueo_sim(self):
        self.assertEqual(CategoriaIncidente.BLOQUEO_SIM.value, "bloqueo_sim")

    def test_categoria_incidente_perdida_o_destruccion_equipo(self):
        self.assertEqual(
            CategoriaIncidente.PERDIDA_O_DESTRUCCION_EQUIPO.value,
            "perdida_o_destruccion_equipo",
        )

    def test_categoria_solicitud_tiene_dos_valores(self):
        self.assertEqual(len(list(CategoriaSolicitud)), 2)

    def test_categoria_solicitud_alta_servicio(self):
        self.assertEqual(CategoriaSolicitud.ALTA_SERVICIO.value, "alta_servicio")

    def test_categoria_solicitud_baja_servicio(self):
        self.assertEqual(CategoriaSolicitud.BAJA_SERVICIO.value, "baja_servicio")


# ═══════════════════════════════════════════════════════════
#  VALUE OBJECT: Comentario
# ═══════════════════════════════════════════════════════════

class TestComentario(unittest.TestCase):
    """R05-R06, E01-E02, A01, A03 — Verifica el value object Comentario."""

    def setUp(self):
        self.comentario = Comentario(
            autor_id=SOLICITANTE,
            rol_autor=RolUsuario.SOLICITANTE,
            contenido="  Necesito ayuda urgente  ",
        )

    def tearDown(self):
        pass

    def test_comentario_se_crea_con_datos_correctos(self):
        # Arrange (setUp)
        # Act / Assert
        self.assertEqual(self.comentario.autor_id, SOLICITANTE)
        self.assertEqual(self.comentario.rol_autor, RolUsuario.SOLICITANTE)

    def test_comentario_trim_contenido(self):
        # Arrange (setUp)
        # Act / Assert
        self.assertEqual(self.comentario.contenido, "Necesito ayuda urgente")

    def test_comentario_id_autogenerado(self):
        # Arrange / Act
        c = Comentario(autor_id="x", rol_autor=RolUsuario.OPERADOR, contenido="test")
        # Assert
        self.assertIsNotNone(c.id)
        self.assertIsInstance(c.id, str)

    def test_comentario_fecha_autogenerada(self):
        # Arrange / Act
        c = Comentario(autor_id="x", rol_autor=RolUsuario.OPERADOR, contenido="test")
        # Assert
        self.assertIsNotNone(c.fecha)

    def test_comentario_igualdad_por_id(self):
        # Arrange
        id_fijo = "id-fijo-123"
        c1 = Comentario(autor_id="a", rol_autor=RolUsuario.OPERADOR, contenido="x", id=id_fijo)
        c2 = Comentario(autor_id="b", rol_autor=RolUsuario.TECNICO, contenido="y", id=id_fijo)
        # Act / Assert
        self.assertEqual(c1, c2)

    def test_comentario_contenido_vacio_falla(self):
        # Arrange / Act / Assert
        with self.assertRaises(ValueError):
            Comentario(autor_id="x", rol_autor=RolUsuario.OPERADOR, contenido="")

    def test_comentario_solo_espacios_falla(self):
        # Arrange / Act / Assert
        with self.assertRaises(ValueError):
            Comentario(autor_id="x", rol_autor=RolUsuario.OPERADOR, contenido="   ")

    def test_comentario_no_tiene_setter_contenido(self):
        # Arrange (setUp)
        # Act / Assert
        with self.assertRaises(AttributeError):
            self.comentario.contenido = "Modificado"

    def test_comentario_no_tiene_setter_autor_id(self):
        # Arrange (setUp)
        # Act / Assert
        with self.assertRaises(AttributeError):
            self.comentario.autor_id = "otro"


# ═══════════════════════════════════════════════════════════
#  VALUE OBJECT: Evento
# ═══════════════════════════════════════════════════════════

class TestEvento(unittest.TestCase):
    """R07-R08, A04 — Verifica el value object Evento."""

    def setUp(self):
        self.evento = Evento(
            tipo=TipoEvento.CREACION,
            actor_id=SOLICITANTE,
            detalle="Evento de prueba",
        )

    def tearDown(self):
        pass

    def test_evento_se_crea_con_datos_correctos(self):
        # Arrange (setUp)
        # Act / Assert
        self.assertEqual(self.evento.tipo, TipoEvento.CREACION)
        self.assertEqual(self.evento.actor_id, SOLICITANTE)
        self.assertEqual(self.evento.detalle, "Evento de prueba")

    def test_evento_id_autogenerado_si_no_se_provee(self):
        # Arrange (setUp)
        # Act / Assert
        self.assertIsNotNone(self.evento.id)
        self.assertIsInstance(self.evento.id, str)

    def test_evento_fecha_autogenerada(self):
        # Arrange (setUp)
        # Act / Assert
        self.assertIsNotNone(self.evento.fecha)

    def test_evento_igualdad_por_id(self):
        # Arrange
        id_fijo = "evt-fijo-456"
        e1 = Evento(tipo=TipoEvento.CREACION, actor_id="a", detalle="x", id=id_fijo)
        e2 = Evento(tipo=TipoEvento.RESOLUCION, actor_id="b", detalle="y", id=id_fijo)
        # Act / Assert
        self.assertEqual(e1, e2)

    def test_evento_no_tiene_setter_tipo(self):
        # Arrange (setUp)
        # Act / Assert
        with self.assertRaises(AttributeError):
            self.evento.tipo = TipoEvento.RESOLUCION

    def test_evento_no_tiene_setter_detalle(self):
        # Arrange (setUp)
        # Act / Assert
        with self.assertRaises(AttributeError):
            self.evento.detalle = "Modificado"


# ═══════════════════════════════════════════════════════════
#  FACTORY — Incidente
# ═══════════════════════════════════════════════════════════

class TestFactoryIncidente(unittest.TestCase):
    """R09-R17, E03-E04 — Verifica la creación de Incidente via Factory."""

    def setUp(self):
        self.incidente = _crear_incidente()

    def tearDown(self):
        pass

    def test_crear_incidente_estado_inicial_abierto(self):
        # Arrange (setUp)
        # Act / Assert
        self.assertEqual(self.incidente.estado, EstadoRequerimiento.ABIERTO)

    def test_crear_incidente_tipo_correcto(self):
        self.assertEqual(self.incidente.tipo, TipoRequerimiento.INCIDENTE)

    def test_crear_incidente_genera_evento_creacion(self):
        # Arrange (setUp)
        # Act
        tipos = [e.tipo for e in self.incidente.eventos]
        # Assert
        self.assertIn(TipoEvento.CREACION, tipos)

    def test_crear_incidente_exactamente_un_evento_inicial(self):
        self.assertEqual(len(self.incidente.eventos), 1)

    def test_crear_incidente_urgencia_critica(self):
        # Arrange / Act
        inc = _crear_incidente(urgencia=Urgencia.CRITICA)
        # Assert
        self.assertEqual(inc.urgencia, Urgencia.CRITICA)

    def test_crear_incidente_urgencia_importante(self):
        inc = _crear_incidente(urgencia=Urgencia.IMPORTANTE)
        self.assertEqual(inc.urgencia, Urgencia.IMPORTANTE)

    def test_crear_incidente_urgencia_menor(self):
        inc = _crear_incidente(urgencia=Urgencia.MENOR)
        self.assertEqual(inc.urgencia, Urgencia.MENOR)

    def test_crear_incidente_categoria_servicio_inaccesible(self):
        inc = _crear_incidente(categoria=CategoriaIncidente.SERVICIO_INACCESIBLE)
        self.assertEqual(inc.categoria, CategoriaIncidente.SERVICIO_INACCESIBLE)

    def test_crear_incidente_categoria_bloqueo_sim(self):
        inc = _crear_incidente(categoria=CategoriaIncidente.BLOQUEO_SIM)
        self.assertEqual(inc.categoria, CategoriaIncidente.BLOQUEO_SIM)

    def test_crear_incidente_categoria_perdida_equipo(self):
        inc = _crear_incidente(
            categoria=CategoriaIncidente.PERDIDA_O_DESTRUCCION_EQUIPO
        )
        self.assertEqual(inc.categoria, CategoriaIncidente.PERDIDA_O_DESTRUCCION_EQUIPO)

    def test_crear_incidente_titulo_vacio_falla(self):
        # Arrange / Act / Assert
        with self.assertRaises(ValueError):
            RequerimientoFactory.crear_incidente(
                titulo="",
                descripcion="desc",
                solicitante_id=SOLICITANTE,
                urgencia=Urgencia.MENOR,
                categoria=CategoriaIncidente.BLOQUEO_SIM,
            )

    def test_crear_incidente_descripcion_vacia_falla(self):
        with self.assertRaises(ValueError):
            RequerimientoFactory.crear_incidente(
                titulo="Título ok",
                descripcion="",
                solicitante_id=SOLICITANTE,
                urgencia=Urgencia.MENOR,
                categoria=CategoriaIncidente.BLOQUEO_SIM,
            )

    def test_crear_incidente_titulo_solo_espacios_falla(self):
        with self.assertRaises(ValueError):
            RequerimientoFactory.crear_incidente(
                titulo="   ",
                descripcion="desc",
                solicitante_id=SOLICITANTE,
                urgencia=Urgencia.MENOR,
                categoria=CategoriaIncidente.BLOQUEO_SIM,
            )


# ═══════════════════════════════════════════════════════════
#  FACTORY — Solicitud
# ═══════════════════════════════════════════════════════════

class TestFactorySolicitud(unittest.TestCase):
    """R18-R22, E05 — Verifica la creación de Solicitud via Factory."""

    def setUp(self):
        self.solicitud = _crear_solicitud()

    def tearDown(self):
        pass

    def test_crear_solicitud_estado_inicial_abierto(self):
        self.assertEqual(self.solicitud.estado, EstadoRequerimiento.ABIERTO)

    def test_crear_solicitud_tipo_correcto(self):
        self.assertEqual(self.solicitud.tipo, TipoRequerimiento.SOLICITUD)

    def test_crear_solicitud_categoria_alta_servicio(self):
        sol = _crear_solicitud(categoria=CategoriaSolicitud.ALTA_SERVICIO)
        self.assertEqual(sol.categoria, CategoriaSolicitud.ALTA_SERVICIO)

    def test_crear_solicitud_categoria_baja_servicio(self):
        sol = _crear_solicitud(categoria=CategoriaSolicitud.BAJA_SERVICIO)
        self.assertEqual(sol.categoria, CategoriaSolicitud.BAJA_SERVICIO)

    def test_crear_solicitud_genera_evento_creacion(self):
        tipos = [e.tipo for e in self.solicitud.eventos]
        self.assertIn(TipoEvento.CREACION, tipos)

    def test_crear_solicitud_no_tiene_propiedad_urgencia(self):
        """Solicitud nunca tiene urgencia — solo Incidente la tiene."""
        # Arrange (setUp)
        # Act / Assert
        self.assertFalse(hasattr(self.solicitud, "urgencia"))

    def test_crear_solicitud_titulo_vacio_falla(self):
        with self.assertRaises(ValueError):
            RequerimientoFactory.crear_solicitud(
                titulo="",
                descripcion="desc",
                solicitante_id=SOLICITANTE,
                categoria=CategoriaSolicitud.ALTA_SERVICIO,
            )


# ═══════════════════════════════════════════════════════════
#  CONSISTENCIA DEL AGREGADO EN __init__
# ═══════════════════════════════════════════════════════════

class TestConsistenciaInit(unittest.TestCase):
    """E06-E10 — Verifica que el __init__ rechaza estados inconsistentes."""

    def setUp(self):
        self.kwargs_base = dict(
            titulo="X",
            descripcion="Y",
            solicitante_id=SOLICITANTE,
            urgencia=Urgencia.MENOR,
            categoria=CategoriaIncidente.BLOQUEO_SIM,
            registrar_creacion=False,
        )

    def tearDown(self):
        pass

    def test_init_asignado_sin_tecnico_falla(self):
        # Arrange
        kwargs = {**self.kwargs_base,
                  "estado": EstadoRequerimiento.ASIGNADO,
                  "tecnico_asignado_id": None}
        # Act / Assert
        with self.assertRaises(RequerimientoError):
            Incidente(**kwargs)

    def test_init_en_progreso_sin_tecnico_falla(self):
        kwargs = {**self.kwargs_base,
                  "estado": EstadoRequerimiento.EN_PROGRESO,
                  "tecnico_asignado_id": None}
        with self.assertRaises(RequerimientoError):
            Incidente(**kwargs)

    def test_init_resuelto_sin_tecnico_falla(self):
        kwargs = {**self.kwargs_base,
                  "estado": EstadoRequerimiento.RESUELTO,
                  "tecnico_asignado_id": None}
        with self.assertRaises(RequerimientoError):
            Incidente(**kwargs)

    def test_init_abierto_con_tecnico_falla(self):
        kwargs = {**self.kwargs_base,
                  "estado": EstadoRequerimiento.ABIERTO,
                  "tecnico_asignado_id": TECNICO_A}
        with self.assertRaises(RequerimientoError):
            Incidente(**kwargs)

    def test_init_reabierto_con_tecnico_falla(self):
        kwargs = {**self.kwargs_base,
                  "estado": EstadoRequerimiento.REABIERTO,
                  "tecnico_asignado_id": TECNICO_A}
        with self.assertRaises(RequerimientoError):
            Incidente(**kwargs)

    def test_init_asignado_con_tecnico_es_valido(self):
        # Arrange
        kwargs = {**self.kwargs_base,
                  "estado": EstadoRequerimiento.ASIGNADO,
                  "tecnico_asignado_id": TECNICO_A}
        # Act
        inc = Incidente(**kwargs)
        # Assert
        self.assertEqual(inc.estado, EstadoRequerimiento.ASIGNADO)
        self.assertEqual(inc.tecnico_asignado_id, TECNICO_A)


# ═══════════════════════════════════════════════════════════
#  ASIGNACIÓN DE TÉCNICO
# ═══════════════════════════════════════════════════════════

class TestAsignarTecnico(unittest.TestCase):
    """R23-R25, E11-E13, P01-P03 — Verifica asignar_tecnico."""

    def setUp(self):
        self.incidente = _crear_incidente()

    def tearDown(self):
        pass

    def test_asignar_tecnico_desde_abierto(self):
        # Arrange (setUp)
        # Act
        evento = self.incidente.asignar_tecnico(TECNICO_A, OPERADOR, RolUsuario.OPERADOR)
        # Assert
        self.assertEqual(self.incidente.estado, EstadoRequerimiento.ASIGNADO)
        self.assertEqual(self.incidente.tecnico_asignado_id, TECNICO_A)
        self.assertEqual(self.incidente.operador_id, OPERADOR)
        self.assertEqual(evento.tipo, TipoEvento.ASIGNACION)

    def test_reasignar_tecnico_desde_asignado(self):
        # Arrange
        self.incidente.asignar_tecnico(TECNICO_A, OPERADOR, RolUsuario.OPERADOR)
        # Act
        evento = self.incidente.asignar_tecnico(TECNICO_B, OPERADOR, RolUsuario.OPERADOR)
        # Assert
        self.assertEqual(self.incidente.tecnico_asignado_id, TECNICO_B)
        self.assertEqual(evento.tipo, TipoEvento.REASIGNACION)

    def test_reasignar_tecnico_desde_en_progreso(self):
        # Arrange
        self.incidente.asignar_tecnico(TECNICO_A, OPERADOR, RolUsuario.OPERADOR)
        self.incidente.iniciar_trabajo(TECNICO_A)
        # Act
        evento = self.incidente.asignar_tecnico(TECNICO_B, OPERADOR, RolUsuario.OPERADOR)
        # Assert
        self.assertEqual(self.incidente.estado, EstadoRequerimiento.ASIGNADO)
        self.assertEqual(self.incidente.tecnico_asignado_id, TECNICO_B)
        self.assertEqual(evento.tipo, TipoEvento.REASIGNACION)

    def test_asignar_tecnico_desde_resuelto_falla(self):
        # Arrange
        self.incidente.asignar_tecnico(TECNICO_A, OPERADOR, RolUsuario.OPERADOR)
        self.incidente.iniciar_trabajo(TECNICO_A)
        self.incidente.resolver(TECNICO_A)
        # Act / Assert
        with self.assertRaises(TransicionEstadoInvalida):
            self.incidente.asignar_tecnico(TECNICO_B, OPERADOR, RolUsuario.OPERADOR)

    def test_asignar_tecnico_rol_tecnico_falla(self):
        # Arrange / Act / Assert
        with self.assertRaises(OperacionNoAutorizada):
            self.incidente.asignar_tecnico(TECNICO_A, TECNICO_B, RolUsuario.TECNICO)

    def test_asignar_tecnico_rol_solicitante_falla(self):
        with self.assertRaises(OperacionNoAutorizada):
            self.incidente.asignar_tecnico(
                TECNICO_A, SOLICITANTE, RolUsuario.SOLICITANTE
            )

    def test_asignar_tecnico_rol_supervisor_falla(self):
        with self.assertRaises(OperacionNoAutorizada):
            self.incidente.asignar_tecnico(
                TECNICO_A, "supervisor-001", RolUsuario.SUPERVISOR
            )

    def test_asignar_mismo_tecnico_falla(self):
        # Arrange
        self.incidente.asignar_tecnico(TECNICO_A, OPERADOR, RolUsuario.OPERADOR)
        # Act / Assert
        with self.assertRaises(RequerimientoError):
            self.incidente.asignar_tecnico(TECNICO_A, OPERADOR, RolUsuario.OPERADOR)

    def test_asignar_tecnico_desde_reabierto(self):
        # Arrange — ir a REABIERTO
        self.incidente.asignar_tecnico(TECNICO_A, OPERADOR, RolUsuario.OPERADOR)
        self.incidente.iniciar_trabajo(TECNICO_A)
        self.incidente.resolver(TECNICO_A)
        self.incidente.agregar_comentario(OPERADOR, RolUsuario.OPERADOR, "Reabrir")
        self.assertEqual(self.incidente.estado, EstadoRequerimiento.REABIERTO)
        # Act
        evento = self.incidente.asignar_tecnico(TECNICO_B, OPERADOR, RolUsuario.OPERADOR)
        # Assert
        self.assertEqual(self.incidente.estado, EstadoRequerimiento.ASIGNADO)
        self.assertEqual(self.incidente.tecnico_asignado_id, TECNICO_B)
        self.assertEqual(evento.tipo, TipoEvento.ASIGNACION)


# ═══════════════════════════════════════════════════════════
#  INICIO DE TRABAJO
# ═══════════════════════════════════════════════════════════

class TestIniciarTrabajo(unittest.TestCase):
    """R26, E14-E15, T01 — Verifica iniciar_trabajo."""

    def setUp(self):
        self.incidente = _crear_incidente()
        self.incidente.asignar_tecnico(TECNICO_A, OPERADOR, RolUsuario.OPERADOR)

    def tearDown(self):
        pass

    def test_iniciar_trabajo_por_tecnico_asignado(self):
        # Arrange (setUp)
        # Act
        evento = self.incidente.iniciar_trabajo(TECNICO_A)
        # Assert
        self.assertEqual(self.incidente.estado, EstadoRequerimiento.EN_PROGRESO)
        self.assertEqual(evento.tipo, TipoEvento.INICIO_TRABAJO)

    def test_iniciar_trabajo_tecnico_no_asignado_falla(self):
        # Arrange (setUp)
        # Act / Assert
        with self.assertRaises(OperacionNoAutorizada):
            self.incidente.iniciar_trabajo(TECNICO_B)

    def test_iniciar_trabajo_desde_abierto_falla(self):
        # Arrange
        inc = _crear_incidente()
        # Act / Assert
        with self.assertRaises(TransicionEstadoInvalida):
            inc.iniciar_trabajo(TECNICO_A)


# ═══════════════════════════════════════════════════════════
#  RESOLUCIÓN
# ═══════════════════════════════════════════════════════════

class TestResolver(unittest.TestCase):
    """R27, E16-E17, T03 — Verifica resolver."""

    def setUp(self):
        self.incidente = _crear_incidente()
        self.incidente.asignar_tecnico(TECNICO_A, OPERADOR, RolUsuario.OPERADOR)
        self.incidente.iniciar_trabajo(TECNICO_A)

    def tearDown(self):
        pass

    def test_resolver_por_tecnico_asignado(self):
        # Arrange (setUp)
        # Act
        evento = self.incidente.resolver(TECNICO_A)
        # Assert
        self.assertEqual(self.incidente.estado, EstadoRequerimiento.RESUELTO)
        self.assertEqual(evento.tipo, TipoEvento.RESOLUCION)

    def test_resolver_tecnico_no_asignado_falla(self):
        # Arrange (setUp)
        # Act / Assert
        with self.assertRaises(OperacionNoAutorizada):
            self.incidente.resolver(TECNICO_B)

    def test_resolver_desde_asignado_falla(self):
        # Arrange
        inc = _crear_incidente()
        inc.asignar_tecnico(TECNICO_A, OPERADOR, RolUsuario.OPERADOR)
        # Act / Assert (sin haber iniciado trabajo)
        with self.assertRaises(TransicionEstadoInvalida):
            inc.resolver(TECNICO_A)

    def test_tecnico_asignado_persiste_despues_de_resolver(self):
        # Arrange (setUp) — H1 de la matriz
        # Act
        self.incidente.resolver(TECNICO_A)
        # Assert
        self.assertEqual(self.incidente.tecnico_asignado_id, TECNICO_A)


# ═══════════════════════════════════════════════════════════
#  DERIVACIÓN
# ═══════════════════════════════════════════════════════════

class TestDerivar(unittest.TestCase):
    """R28-R29, E18-E22, T05 — Verifica derivar."""

    def setUp(self):
        self.incidente = _crear_incidente()
        self.incidente.asignar_tecnico(TECNICO_A, OPERADOR, RolUsuario.OPERADOR)

    def tearDown(self):
        pass

    def test_derivar_desde_asignado(self):
        # Arrange (setUp)
        # Act
        evento = self.incidente.derivar(TECNICO_A, TECNICO_B, "Requiere especialista")
        # Assert
        self.assertEqual(self.incidente.tecnico_asignado_id, TECNICO_B)
        self.assertEqual(self.incidente.estado, EstadoRequerimiento.ASIGNADO)
        self.assertEqual(evento.tipo, TipoEvento.DERIVACION)

    def test_derivar_desde_en_progreso(self):
        # Arrange
        self.incidente.iniciar_trabajo(TECNICO_A)
        # Act
        evento = self.incidente.derivar(TECNICO_A, TECNICO_B, "Interconsulta urgente")
        # Assert
        self.assertEqual(self.incidente.tecnico_asignado_id, TECNICO_B)
        self.assertEqual(self.incidente.estado, EstadoRequerimiento.ASIGNADO)
        self.assertEqual(evento.tipo, TipoEvento.DERIVACION)

    def test_derivar_tecnico_no_asignado_falla(self):
        # Arrange (setUp)
        # Act / Assert
        with self.assertRaises(OperacionNoAutorizada):
            self.incidente.derivar(TECNICO_B, TECNICO_A, "Sin permiso")

    def test_derivar_al_mismo_tecnico_falla(self):
        # Arrange (setUp)
        # Act / Assert
        with self.assertRaises(RequerimientoError):
            self.incidente.derivar(TECNICO_A, TECNICO_A, "Mismo técnico")

    def test_derivar_motivo_vacio_falla(self):
        # Arrange (setUp)
        # Act / Assert
        with self.assertRaises(RequerimientoError):
            self.incidente.derivar(TECNICO_A, TECNICO_B, "")

    def test_derivar_motivo_solo_espacios_falla(self):
        with self.assertRaises(RequerimientoError):
            self.incidente.derivar(TECNICO_A, TECNICO_B, "   ")

    def test_derivar_desde_resuelto_falla(self):
        # Arrange
        self.incidente.iniciar_trabajo(TECNICO_A)
        self.incidente.resolver(TECNICO_A)
        # Act / Assert
        with self.assertRaises(TransicionEstadoInvalida):
            self.incidente.derivar(TECNICO_A, TECNICO_B, "Motivo")

    def test_derivar_registra_origen_destino_motivo_en_evento(self):
        # Arrange (setUp)
        motivo = "Requiere hardware especializado"
        # Act
        evento = self.incidente.derivar(TECNICO_A, TECNICO_B, motivo)
        # Assert
        self.assertIn(TECNICO_A, evento.detalle)
        self.assertIn(TECNICO_B, evento.detalle)
        self.assertIn(motivo, evento.detalle)


# ═══════════════════════════════════════════════════════════
#  COMENTARIOS, PERMISOS Y REAPERTURA
# ═══════════════════════════════════════════════════════════

class TestAgregarComentario(unittest.TestCase):
    """R30-R34, E23-E25 — Verifica agregar_comentario y permisos."""

    def setUp(self):
        self.incidente = _crear_incidente()
        self.incidente.asignar_tecnico(TECNICO_A, OPERADOR, RolUsuario.OPERADOR)

    def tearDown(self):
        pass

    def test_agregar_comentario_por_solicitante_propio(self):
        # Arrange (setUp)
        # Act
        comentario = self.incidente.agregar_comentario(
            SOLICITANTE, RolUsuario.SOLICITANTE, "Sigo esperando"
        )
        # Assert
        self.assertEqual(comentario.autor_id, SOLICITANTE)
        self.assertIn(comentario, self.incidente.comentarios)

    def test_agregar_comentario_por_operador(self):
        # Arrange (setUp)
        # Act
        comentario = self.incidente.agregar_comentario(
            OPERADOR, RolUsuario.OPERADOR, "Revisado"
        )
        # Assert
        self.assertEqual(comentario.rol_autor, RolUsuario.OPERADOR)

    def test_agregar_comentario_por_tecnico_asignado(self):
        # Arrange (setUp)
        # Act
        comentario = self.incidente.agregar_comentario(
            TECNICO_A, RolUsuario.TECNICO, "Recibido, analizando"
        )
        # Assert
        self.assertEqual(comentario.rol_autor, RolUsuario.TECNICO)

    def test_comentario_vacio_falla(self):
        with self.assertRaises(ValueError):
            self.incidente.agregar_comentario(SOLICITANTE, RolUsuario.SOLICITANTE, "")

    def test_comentario_por_supervisor_falla(self):
        # Arrange / Act / Assert
        with self.assertRaises(OperacionNoAutorizada):
            self.incidente.agregar_comentario(
                "supervisor-001", RolUsuario.SUPERVISOR, "Supervisando"
            )

    def test_comentario_solicitante_ajeno_falla(self):
        # Arrange / Act / Assert
        with self.assertRaises(OperacionNoAutorizada):
            self.incidente.agregar_comentario(
                SOLICITANTE_OTRO, RolUsuario.SOLICITANTE, "No debería poder"
            )

    def test_comentario_tecnico_no_asignado_falla(self):
        # Arrange / Act / Assert
        with self.assertRaises(OperacionNoAutorizada):
            self.incidente.agregar_comentario(
                TECNICO_B, RolUsuario.TECNICO, "No me corresponde"
            )

    def test_comentario_genera_evento_comentario(self):
        # Arrange (setUp)
        # Act
        self.incidente.agregar_comentario(
            SOLICITANTE, RolUsuario.SOLICITANTE, "Info adicional"
        )
        # Assert
        tipos = [e.tipo for e in self.incidente.eventos]
        self.assertIn(TipoEvento.COMENTARIO, tipos)


class TestReapertura(unittest.TestCase):
    """R33-R35, H2 — Verifica la reapertura automática por comentario."""

    def setUp(self):
        self.incidente = _crear_incidente()
        self.incidente.asignar_tecnico(TECNICO_A, OPERADOR, RolUsuario.OPERADOR)
        self.incidente.iniciar_trabajo(TECNICO_A)
        self.incidente.resolver(TECNICO_A)

    def tearDown(self):
        pass

    def test_comentario_operador_en_resuelto_reabre(self):
        # Arrange (setUp — estado RESUELTO)
        # Act
        self.incidente.agregar_comentario(OPERADOR, RolUsuario.OPERADOR, "Falta verificar")
        # Assert
        self.assertEqual(self.incidente.estado, EstadoRequerimiento.REABIERTO)
        self.assertIsNone(self.incidente.tecnico_asignado_id)

    def test_comentario_tecnico_en_resuelto_reabre(self):
        # Arrange (setUp — estado RESUELTO, TECNICO_A asignado)
        # Act
        self.incidente.agregar_comentario(TECNICO_A, RolUsuario.TECNICO, "Error persiste")
        # Assert
        self.assertEqual(self.incidente.estado, EstadoRequerimiento.REABIERTO)

    def test_reapertura_genera_evento_reapertura(self):
        # Arrange (setUp)
        # Act
        self.incidente.agregar_comentario(OPERADOR, RolUsuario.OPERADOR, "Reabrir")
        # Assert
        tipos = [e.tipo for e in self.incidente.eventos]
        self.assertIn(TipoEvento.REAPERTURA, tipos)

    def test_comentario_solicitante_en_resuelto_no_reabre(self):
        # Arrange (setUp)
        # Act
        self.incidente.agregar_comentario(
            SOLICITANTE, RolUsuario.SOLICITANTE, "Sigue sin andar"
        )
        # Assert
        self.assertEqual(self.incidente.estado, EstadoRequerimiento.RESUELTO)

    def test_tecnico_no_puede_comentar_en_reabierto(self):
        """H2 — técnico queda desasignado al reabrir; no puede comentar."""
        # Arrange
        self.incidente.agregar_comentario(OPERADOR, RolUsuario.OPERADOR, "Reabrir")
        self.assertEqual(self.incidente.estado, EstadoRequerimiento.REABIERTO)
        # Act / Assert
        with self.assertRaises(OperacionNoAutorizada):
            self.incidente.agregar_comentario(
                TECNICO_A, RolUsuario.TECNICO, "Quiero seguir"
            )


# ═══════════════════════════════════════════════════════════
#  TRANSICIONES PROHIBIDAS EXPLÍCITAS
# ═══════════════════════════════════════════════════════════

class TestTransicionesProhibidas(unittest.TestCase):
    """T01-T05 — Verifica que las transiciones ilegales sean rechazadas."""

    def setUp(self):
        self.incidente = _crear_incidente()

    def tearDown(self):
        pass

    def test_transicion_abierto_a_en_progreso_falla(self):
        # Arrange (setUp — ABIERTO)
        # Act / Assert
        with self.assertRaises(TransicionEstadoInvalida):
            self.incidente.iniciar_trabajo(TECNICO_A)

    def test_transicion_abierto_a_resuelto_falla(self):
        # Arrange (setUp — ABIERTO, sin técnico asignado)
        # Act / Assert — resolver desde ABIERTO viola la transición de estado
        with self.assertRaises(TransicionEstadoInvalida):
            self.incidente.resolver(TECNICO_A)

    def test_transicion_asignado_a_resuelto_falla(self):
        # Arrange
        self.incidente.asignar_tecnico(TECNICO_A, OPERADOR, RolUsuario.OPERADOR)
        # Act / Assert (debe pasar por EN_PROGRESO primero)
        with self.assertRaises(TransicionEstadoInvalida):
            self.incidente.resolver(TECNICO_A)

    def test_transicion_resuelto_a_asignado_directo_falla(self):
        # Arrange — llegar a RESUELTO
        self.incidente.asignar_tecnico(TECNICO_A, OPERADOR, RolUsuario.OPERADOR)
        self.incidente.iniciar_trabajo(TECNICO_A)
        self.incidente.resolver(TECNICO_A)
        # Act / Assert — intentar asignar directo viola la invariante
        with self.assertRaises(TransicionEstadoInvalida):
            self.incidente.asignar_tecnico(TECNICO_B, OPERADOR, RolUsuario.OPERADOR)

    def test_transicion_reabierto_a_en_progreso_directo_falla(self):
        # Arrange — llegar a REABIERTO
        self.incidente.asignar_tecnico(TECNICO_A, OPERADOR, RolUsuario.OPERADOR)
        self.incidente.iniciar_trabajo(TECNICO_A)
        self.incidente.resolver(TECNICO_A)
        self.incidente.agregar_comentario(OPERADOR, RolUsuario.OPERADOR, "Reabrir")
        self.assertEqual(self.incidente.estado, EstadoRequerimiento.REABIERTO)
        # Act / Assert — REABIERTO no permite iniciar trabajo (debe pasar por ASIGNADO)
        with self.assertRaises(TransicionEstadoInvalida):
            self.incidente.iniciar_trabajo(TECNICO_A)


# ═══════════════════════════════════════════════════════════
#  AUDITORÍA E INMUTABILIDAD
# ═══════════════════════════════════════════════════════════

class TestAuditoria(unittest.TestCase):
    """A01-A10 — Verifica la trazabilidad e inmutabilidad del historial."""

    def setUp(self):
        self.incidente = _crear_incidente()

    def tearDown(self):
        pass

    def test_comentarios_retorna_tupla_inmutable(self):
        # Arrange
        self.incidente.agregar_comentario(
            SOLICITANTE, RolUsuario.SOLICITANTE, "Hola"
        )
        # Act
        result = self.incidente.comentarios
        # Assert
        self.assertIsInstance(result, tuple)

    def test_eventos_retorna_tupla_inmutable(self):
        # Act
        result = self.incidente.eventos
        # Assert
        self.assertIsInstance(result, tuple)

    def test_modificar_lista_comentarios_externa_no_afecta_agregado(self):
        # Arrange
        self.incidente.agregar_comentario(
            SOLICITANTE, RolUsuario.SOLICITANTE, "Test"
        )
        copia = list(self.incidente.comentarios)
        # Act
        copia.clear()
        # Assert — la copia externa no afecta el agregado
        self.assertEqual(len(self.incidente.comentarios), 1)

    def test_ciclo_completo_genera_secuencia_eventos_correcta(self):
        # Arrange
        self.incidente.asignar_tecnico(TECNICO_A, OPERADOR, RolUsuario.OPERADOR)
        self.incidente.iniciar_trabajo(TECNICO_A)
        self.incidente.resolver(TECNICO_A)
        # Act
        tipos = [e.tipo for e in self.incidente.eventos]
        # Assert
        self.assertEqual(tipos, [
            TipoEvento.CREACION,
            TipoEvento.ASIGNACION,
            TipoEvento.INICIO_TRABAJO,
            TipoEvento.RESOLUCION,
        ])

    def test_derivacion_registra_origen_destino_y_motivo(self):
        # Arrange
        self.incidente.asignar_tecnico(TECNICO_A, OPERADOR, RolUsuario.OPERADOR)
        motivo = "Necesita especialista en redes"
        # Act
        self.incidente.derivar(TECNICO_A, TECNICO_B, motivo)
        ultimo = self.incidente.eventos[-1]
        # Assert
        self.assertEqual(ultimo.tipo, TipoEvento.DERIVACION)
        self.assertIn(TECNICO_A, ultimo.detalle)
        self.assertIn(TECNICO_B, ultimo.detalle)
        self.assertIn(motivo, ultimo.detalle)

    def test_reasignacion_registra_tecnico_anterior_y_nuevo(self):
        # Arrange
        self.incidente.asignar_tecnico(TECNICO_A, OPERADOR, RolUsuario.OPERADOR)
        # Act
        evento = self.incidente.asignar_tecnico(TECNICO_B, OPERADOR, RolUsuario.OPERADOR)
        # Assert
        self.assertEqual(evento.tipo, TipoEvento.REASIGNACION)
        self.assertIn(TECNICO_A, evento.detalle)
        self.assertIn(TECNICO_B, evento.detalle)

    def test_reapertura_genera_evento_reapertura_en_historial(self):
        # Arrange
        self.incidente.asignar_tecnico(TECNICO_A, OPERADOR, RolUsuario.OPERADOR)
        self.incidente.iniciar_trabajo(TECNICO_A)
        self.incidente.resolver(TECNICO_A)
        # Act
        self.incidente.agregar_comentario(OPERADOR, RolUsuario.OPERADOR, "Reabrir")
        tipos = [e.tipo for e in self.incidente.eventos]
        # Assert
        self.assertIn(TipoEvento.REAPERTURA, tipos)

    def test_comentario_genera_evento_comentario_en_historial(self):
        # Arrange / Act
        self.incidente.agregar_comentario(
            SOLICITANTE, RolUsuario.SOLICITANTE, "Más info"
        )
        tipos = [e.tipo for e in self.incidente.eventos]
        # Assert
        self.assertIn(TipoEvento.COMENTARIO, tipos)

    def test_operador_id_refleja_ultimo_operador_tras_reasignacion(self):
        """H5 — operador_id guarda solo el último operador."""
        # Arrange
        operador2 = "operador-002"
        self.incidente.asignar_tecnico(TECNICO_A, OPERADOR, RolUsuario.OPERADOR)
        # Act
        self.incidente.asignar_tecnico(TECNICO_B, operador2, RolUsuario.OPERADOR)
        # Assert
        self.assertEqual(self.incidente.operador_id, operador2)

    def test_fecha_actualizacion_cambia_tras_operacion(self):
        # Arrange
        fecha_inicial = self.incidente.fecha_actualizacion
        # Act
        self.incidente.asignar_tecnico(TECNICO_A, OPERADOR, RolUsuario.OPERADOR)
        # Assert
        self.assertGreaterEqual(
            self.incidente.fecha_actualizacion, fecha_inicial
        )


# ═══════════════════════════════════════════════════════════
#  EVENTOS DE DOMINIO (Observer queue)
# ═══════════════════════════════════════════════════════════

class TestEventosDominio(unittest.TestCase):
    """O01-O07 — Verifica la cola de eventos de dominio para Observer."""

    def setUp(self):
        self.incidente = _crear_incidente()

    def tearDown(self):
        pass

    def test_recolectar_eventos_retorna_pendientes(self):
        # Arrange (setUp — 1 evento CREACION en cola)
        # Act
        eventos = self.incidente.recolectar_eventos()
        # Assert
        self.assertEqual(len(eventos), 1)
        self.assertEqual(eventos[0].tipo, TipoEvento.CREACION)

    def test_recolectar_eventos_vacia_la_cola(self):
        # Arrange
        self.incidente.recolectar_eventos()
        # Act
        segunda_llamada = self.incidente.recolectar_eventos()
        # Assert
        self.assertEqual(len(segunda_llamada), 0)

    def test_recolectar_no_afecta_historial_auditoria(self):
        # Arrange
        self.incidente.asignar_tecnico(TECNICO_A, OPERADOR, RolUsuario.OPERADOR)
        # Act
        self.incidente.recolectar_eventos()
        # Assert — auditoría intacta
        self.assertEqual(len(self.incidente.eventos), 2)

    def test_recolectar_acumula_multiples_operaciones(self):
        # Arrange
        self.incidente.recolectar_eventos()  # vaciar CREACION
        self.incidente.asignar_tecnico(TECNICO_A, OPERADOR, RolUsuario.OPERADOR)
        self.incidente.iniciar_trabajo(TECNICO_A)
        # Act
        eventos = self.incidente.recolectar_eventos()
        # Assert
        self.assertEqual(len(eventos), 2)
        self.assertEqual(eventos[0].tipo, TipoEvento.ASIGNACION)
        self.assertEqual(eventos[1].tipo, TipoEvento.INICIO_TRABAJO)


# ═══════════════════════════════════════════════════════════
#  CICLO COMPLETO
# ═══════════════════════════════════════════════════════════

class TestCicloCompleto(unittest.TestCase):
    """Verifica el ciclo de vida completo del agregado."""

    def setUp(self):
        self.incidente = _crear_incidente()

    def tearDown(self):
        pass

    def test_ciclo_doble_abierto_resuelto_reabierto_resuelto(self):
        # Arrange
        inc = self.incidente
        # Act — primer ciclo
        inc.asignar_tecnico(TECNICO_A, OPERADOR, RolUsuario.OPERADOR)
        inc.iniciar_trabajo(TECNICO_A)
        inc.resolver(TECNICO_A)
        self.assertEqual(inc.estado, EstadoRequerimiento.RESUELTO)

        # Reapertura
        inc.agregar_comentario(OPERADOR, RolUsuario.OPERADOR, "Falló de nuevo")
        self.assertEqual(inc.estado, EstadoRequerimiento.REABIERTO)

        # Segundo ciclo
        inc.asignar_tecnico(TECNICO_B, OPERADOR, RolUsuario.OPERADOR)
        inc.iniciar_trabajo(TECNICO_B)
        inc.resolver(TECNICO_B)
        # Assert
        self.assertEqual(inc.estado, EstadoRequerimiento.RESUELTO)
        self.assertEqual(inc.tecnico_asignado_id, TECNICO_B)


if __name__ == "__main__":
    unittest.main()
