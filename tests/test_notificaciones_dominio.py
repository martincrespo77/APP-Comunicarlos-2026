"""Tests unitarios — Dominio de notificaciones (Observer pattern).

Cubre ObservadorRequerimiento (vía espía) y DespachadorEventos:
registro, despacho, quitar observador y comportamientos edge case.

STYLEGUIDE_PROFE: unittest, setUp, tearDown, AAA, test_<comportamiento>.
"""

import unittest

from app.compartido.dominio import RolUsuario
from app.notificaciones.dominio import DespachadorEventos, ObservadorRequerimiento
from app.requerimientos.dominio import (
    CategoriaIncidente,
    RequerimientoFactory,
    TipoEvento,
    Urgencia,
)


# ── Implementación espía para tests ──

class ObservadorEspia(ObservadorRequerimiento):
    """Spy del patrón Observer — registra todas las notificaciones recibidas."""

    def __init__(self) -> None:
        self.notificaciones: list[tuple[str, str]] = []

    def notificar(self, evento, requerimiento_id: str) -> None:
        self.notificaciones.append((evento.tipo.value, requerimiento_id))

    def cantidad_recibidas(self) -> int:
        return len(self.notificaciones)


# ── Constantes ──
SOLICITANTE = "solicitante-001"
OPERADOR = "operador-001"
TECNICO_A = "tecnico-001"
TECNICO_B = "tecnico-002"


def _crear_incidente():
    return RequerimientoFactory.crear_incidente(
        titulo="Servidor caído",
        descripcion="No responde",
        solicitante_id=SOLICITANTE,
        urgencia=Urgencia.CRITICA,
        categoria=CategoriaIncidente.SERVICIO_INACCESIBLE,
    )


class TestDespachadorEventos(unittest.TestCase):
    """N01-N05, O06, O07 — Verifica el DespachadorEventos."""

    def setUp(self):
        self.despachador = DespachadorEventos()
        self.espia = ObservadorEspia()

    def tearDown(self):
        pass

    # ── Registro ──

    def test_registrar_observador_incrementa_cantidad(self):
        # Arrange (setUp — 0 observadores)
        # Act
        self.despachador.registrar(self.espia)
        # Assert
        self.assertEqual(self.despachador.cantidad_observadores, 1)

    def test_registrar_mismo_observador_dos_veces_no_duplica(self):
        # Arrange (setUp)
        # Act
        self.despachador.registrar(self.espia)
        self.despachador.registrar(self.espia)
        # Assert
        self.assertEqual(self.despachador.cantidad_observadores, 1)

    def test_registrar_multiple_observadores_distintos(self):
        # Arrange
        espia2 = ObservadorEspia()
        # Act
        self.despachador.registrar(self.espia)
        self.despachador.registrar(espia2)
        # Assert
        self.assertEqual(self.despachador.cantidad_observadores, 2)

    # ── Quitar ──

    def test_quitar_observador_registrado(self):
        # Arrange
        self.despachador.registrar(self.espia)
        # Act
        self.despachador.quitar(self.espia)
        # Assert
        self.assertEqual(self.despachador.cantidad_observadores, 0)

    def test_quitar_observador_no_registrado_falla(self):
        # Arrange — no registrado
        # Act / Assert
        with self.assertRaises(ValueError):
            self.despachador.quitar(self.espia)

    # ── Despacho ──

    def test_despachar_notifica_observadores_registrados(self):
        # Arrange
        incidente = _crear_incidente()
        self.despachador.registrar(self.espia)
        evento = incidente.eventos[0]
        # Act
        self.despachador.despachar(evento, incidente.id)
        # Assert
        self.assertEqual(self.espia.cantidad_recibidas(), 1)
        self.assertEqual(self.espia.notificaciones[0][0], "creacion")
        self.assertEqual(self.espia.notificaciones[0][1], incidente.id)

    def test_despachar_notifica_multiples_observadores(self):
        # Arrange
        incidente = _crear_incidente()
        espia2 = ObservadorEspia()
        self.despachador.registrar(self.espia)
        self.despachador.registrar(espia2)
        evento = incidente.eventos[0]
        # Act
        self.despachador.despachar(evento, incidente.id)
        # Assert
        self.assertEqual(self.espia.cantidad_recibidas(), 1)
        self.assertEqual(espia2.cantidad_recibidas(), 1)

    def test_despachar_sin_observadores_no_falla(self):
        # Arrange — despachador sin observadores
        incidente = _crear_incidente()
        evento = incidente.eventos[0]
        # Act / Assert
        try:
            self.despachador.despachar(evento, incidente.id)
        except Exception as e:
            self.fail(f"despachar() sin observadores lanzó excepción: {e}")

    def test_despachar_no_notifica_observador_quitado(self):
        # Arrange
        incidente = _crear_incidente()
        self.despachador.registrar(self.espia)
        self.despachador.quitar(self.espia)
        evento = incidente.eventos[0]
        # Act
        self.despachador.despachar(evento, incidente.id)
        # Assert
        self.assertEqual(self.espia.cantidad_recibidas(), 0)

    def test_cantidad_observadores_inicial_es_cero(self):
        # Arrange (setUp — despachador nuevo)
        # Act / Assert
        self.assertEqual(self.despachador.cantidad_observadores, 0)


class TestFlujoServiceSimulado(unittest.TestCase):
    """O05 — Flujo completo: recolectar → despachar → observador notificado."""

    def setUp(self):
        self.incidente = _crear_incidente()
        self.espia = ObservadorEspia()
        self.despachador = DespachadorEventos()
        self.despachador.registrar(self.espia)

    def tearDown(self):
        pass

    def test_flujo_service_simulado_despacho_creacion(self):
        # Arrange (setUp)
        # Act — el Service recolecta y despacha
        for evento in self.incidente.recolectar_eventos():
            self.despachador.despachar(evento, self.incidente.id)
        # Assert
        self.assertEqual(self.espia.cantidad_recibidas(), 1)
        self.assertEqual(self.espia.notificaciones[0][0], "creacion")

    def test_flujo_service_simulado_despacho_asignacion(self):
        # Arrange — limpiar CREACION
        self.incidente.recolectar_eventos()
        self.incidente.asignar_tecnico(TECNICO_A, OPERADOR, RolUsuario.OPERADOR)
        # Act
        for evento in self.incidente.recolectar_eventos():
            self.despachador.despachar(evento, self.incidente.id)
        # Assert
        self.assertEqual(self.espia.cantidad_recibidas(), 1)
        self.assertEqual(self.espia.notificaciones[0][0], "asignacion")

    def test_flujo_service_simulado_multiples_operaciones(self):
        # Arrange — despachar CREACION
        for evt in self.incidente.recolectar_eventos():
            self.despachador.despachar(evt, self.incidente.id)

        self.incidente.asignar_tecnico(TECNICO_A, OPERADOR, RolUsuario.OPERADOR)
        for evt in self.incidente.recolectar_eventos():
            self.despachador.despachar(evt, self.incidente.id)

        self.incidente.iniciar_trabajo(TECNICO_A)
        for evt in self.incidente.recolectar_eventos():
            self.despachador.despachar(evt, self.incidente.id)

        # Assert — 3 eventos despachados en total
        self.assertEqual(self.espia.cantidad_recibidas(), 3)
        tipos = [n[0] for n in self.espia.notificaciones]
        self.assertEqual(tipos, ["creacion", "asignacion", "inicio_trabajo"])


if __name__ == "__main__":
    unittest.main()
