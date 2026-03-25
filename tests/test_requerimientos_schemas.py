"""Tests unitarios para app/requerimientos/schemas.py.

Cubre:
  - Schemas de entrada: IncidenteCrearIn, SolicitudCrearIn,
    AsignarTecnicoIn, DerivarRequerimientoIn, ComentarioAgregarIn.
  - Schemas de salida: EventoOut, ComentarioOut, RequerimientoOut.
  - Mapeo desde_entidad() para tipos concretos Incidente y Solicitud.
  - Discriminación correcta de campos opcionales según tipo.
"""

from __future__ import annotations

import unittest

from pydantic import ValidationError

from app.compartido.dominio import RolUsuario
from app.requerimientos.dominio import (
    CategoriaIncidente,
    CategoriaSolicitud,
    EstadoRequerimiento,
    RequerimientoFactory,
    TipoEvento,
    TipoRequerimiento,
    Urgencia,
)
from app.requerimientos.schemas import (
    AsignarTecnicoIn,
    ComentarioAgregarIn,
    ComentarioOut,
    DerivarRequerimientoIn,
    EventoOut,
    IncidenteCrearIn,
    RequerimientoOut,
    SolicitudCrearIn,
)


# ── Helpers ─────────────────────────────────────────────────

def _incidente():
    return RequerimientoFactory.crear_incidente(
        titulo="Servidor caído",
        descripcion="El servidor principal no responde",
        solicitante_id="u-sol",
        urgencia=Urgencia.CRITICA,
        categoria=CategoriaIncidente.SERVICIO_INACCESIBLE,
    )


def _solicitud():
    return RequerimientoFactory.crear_solicitud(
        titulo="Alta de línea",
        descripcion="Se requiere una nueva línea de telefonía",
        solicitante_id="u-sol",
        categoria=CategoriaSolicitud.ALTA_SERVICIO,
    )


# ═══════════════════════════════════════════════════════════
#  SCHEMAS DE ENTRADA
# ═══════════════════════════════════════════════════════════


class TestIncidenteCrearIn(unittest.TestCase):

    def test_creacion_valida(self):
        dto = IncidenteCrearIn(
            titulo="Fallo de red",
            descripcion="Sin acceso a internet",
            solicitante_id="u-001",
            urgencia=Urgencia.IMPORTANTE,
            categoria=CategoriaIncidente.BLOQUEO_SIM,
        )
        self.assertEqual(dto.titulo, "Fallo de red")
        self.assertEqual(dto.urgencia, Urgencia.IMPORTANTE)
        self.assertEqual(dto.categoria, CategoriaIncidente.BLOQUEO_SIM)

    def test_acepta_string_enum_urgencia(self):
        dto = IncidenteCrearIn(
            titulo="T",
            descripcion="D",
            solicitante_id="u-1",
            urgencia="menor",
            categoria="bloqueo_sim",
        )
        self.assertEqual(dto.urgencia, Urgencia.MENOR)

    def test_falta_campo_obligatorio(self):
        with self.assertRaises(ValidationError):
            IncidenteCrearIn(
                titulo="T",
                descripcion="D",
                solicitante_id="u-1",
                # falta urgencia y categoria
            )

    def test_urgencia_invalida(self):
        with self.assertRaises(ValidationError):
            IncidenteCrearIn(
                titulo="T",
                descripcion="D",
                solicitante_id="u-1",
                urgencia="muy_urgente",
                categoria=CategoriaIncidente.BLOQUEO_SIM,
            )


class TestSolicitudCrearIn(unittest.TestCase):

    def test_creacion_valida(self):
        dto = SolicitudCrearIn(
            titulo="Alta servicio",
            descripcion="Solicito una nueva línea",
            solicitante_id="u-002",
            categoria=CategoriaSolicitud.ALTA_SERVICIO,
        )
        self.assertEqual(dto.categoria, CategoriaSolicitud.ALTA_SERVICIO)

    def test_no_tiene_campo_urgencia(self):
        """Las solicitudes no tienen urgencia."""
        dto = SolicitudCrearIn(
            titulo="T",
            descripcion="D",
            solicitante_id="u-1",
            categoria=CategoriaSolicitud.BAJA_SERVICIO,
        )
        self.assertFalse(hasattr(dto, "urgencia"))

    def test_falta_categoria_lanza_error(self):
        with self.assertRaises(ValidationError):
            SolicitudCrearIn(titulo="T", descripcion="D", solicitante_id="u-1")


class TestAsignarTecnicoIn(unittest.TestCase):

    def test_creacion_valida(self):
        dto = AsignarTecnicoIn(tecnico_id="tec-001")
        self.assertEqual(dto.tecnico_id, "tec-001")

    def test_falta_tecnico_id(self):
        with self.assertRaises(ValidationError):
            AsignarTecnicoIn()


class TestDerivarRequerimientoIn(unittest.TestCase):

    def test_creacion_valida(self):
        dto = DerivarRequerimientoIn(
            tecnico_destino_id="tec-002",
            motivo="Especialización en redes requerida",
        )
        self.assertEqual(dto.tecnico_destino_id, "tec-002")
        self.assertEqual(dto.motivo, "Especialización en redes requerida")

    def test_falta_motivo_lanza_error(self):
        with self.assertRaises(ValidationError):
            DerivarRequerimientoIn(tecnico_destino_id="tec-002")


class TestComentarioAgregarIn(unittest.TestCase):

    def test_creacion_valida(self):
        dto = ComentarioAgregarIn(contenido="Se revisó y persiste el problema.")
        self.assertEqual(dto.contenido, "Se revisó y persiste el problema.")

    def test_falta_contenido(self):
        with self.assertRaises(ValidationError):
            ComentarioAgregarIn()


# ═══════════════════════════════════════════════════════════
#  SCHEMAS DE SALIDA
# ═══════════════════════════════════════════════════════════


class TestEventoOut(unittest.TestCase):

    def _primer_evento(self, req):
        return req.eventos[0]

    def test_desde_entidad_incidente(self):
        inc = _incidente()
        evento = self._primer_evento(inc)
        dto = EventoOut.desde_entidad(evento)
        self.assertEqual(dto.id, evento.id)
        self.assertEqual(dto.tipo, TipoEvento.CREACION)
        self.assertEqual(dto.actor_id, "u-sol")
        self.assertIsInstance(dto.detalle, str)

    def test_serializable_a_dict(self):
        inc = _incidente()
        dto = EventoOut.desde_entidad(self._primer_evento(inc))
        datos = dto.model_dump()
        self.assertIn("tipo", datos)
        self.assertIn("fecha", datos)


class TestComentarioOut(unittest.TestCase):

    def test_desde_entidad(self):
        inc = _incidente()
        inc.agregar_comentario("u-op", RolUsuario.OPERADOR, "En revisión")
        comentario = inc.comentarios[0]
        dto = ComentarioOut.desde_entidad(comentario)
        self.assertEqual(dto.autor_id, "u-op")
        self.assertEqual(dto.rol_autor, RolUsuario.OPERADOR)
        self.assertEqual(dto.contenido, "En revisión")

    def test_serializable_a_dict(self):
        inc = _incidente()
        inc.agregar_comentario("u-op", RolUsuario.OPERADOR, "OK")
        dto = ComentarioOut.desde_entidad(inc.comentarios[0])
        datos = dto.model_dump()
        self.assertIn("autor_id", datos)
        self.assertIn("rol_autor", datos)


# ═══════════════════════════════════════════════════════════
#  RequerimientoOut
# ═══════════════════════════════════════════════════════════


class TestRequerimientoOutDesdeIncidente(unittest.TestCase):

    def setUp(self):
        self.inc = _incidente()
        self.dto = RequerimientoOut.desde_entidad(self.inc)

    def test_campos_base(self):
        self.assertEqual(self.dto.id, self.inc.id)
        self.assertEqual(self.dto.titulo, "Servidor caído")
        self.assertEqual(self.dto.tipo, TipoRequerimiento.INCIDENTE)
        self.assertEqual(self.dto.estado, EstadoRequerimiento.ABIERTO)
        self.assertEqual(self.dto.solicitante_id, "u-sol")
        self.assertIsNone(self.dto.operador_id)
        self.assertIsNone(self.dto.tecnico_asignado_id)

    def test_campos_exclusivos_incidente(self):
        self.assertEqual(self.dto.urgencia, Urgencia.CRITICA)
        self.assertEqual(self.dto.categoria_incidente, CategoriaIncidente.SERVICIO_INACCESIBLE)
        self.assertIsNone(self.dto.categoria_solicitud)

    def test_eventos_incluidos(self):
        """El evento de creación debe aparecer en el DTO."""
        self.assertEqual(len(self.dto.eventos), 1)
        self.assertEqual(self.dto.eventos[0].tipo, TipoEvento.CREACION)

    def test_comentarios_vacios_por_defecto(self):
        self.assertEqual(self.dto.comentarios, [])

    def test_con_comentario(self):
        self.inc.agregar_comentario("u-op", RolUsuario.OPERADOR, "Revisando")
        dto = RequerimientoOut.desde_entidad(self.inc)
        self.assertEqual(len(dto.comentarios), 1)
        self.assertEqual(dto.comentarios[0].contenido, "Revisando")

    def test_serializable_a_dict(self):
        datos = self.dto.model_dump()
        self.assertIn("id", datos)
        self.assertIn("urgencia", datos)
        self.assertIn("comentarios", datos)
        self.assertIn("eventos", datos)


class TestRequerimientoOutDesdeSolicitud(unittest.TestCase):

    def setUp(self):
        self.sol = _solicitud()
        self.dto = RequerimientoOut.desde_entidad(self.sol)

    def test_tipo_solicitud(self):
        self.assertEqual(self.dto.tipo, TipoRequerimiento.SOLICITUD)

    def test_campos_exclusivos_solicitud(self):
        self.assertIsNone(self.dto.urgencia)
        self.assertIsNone(self.dto.categoria_incidente)
        self.assertEqual(self.dto.categoria_solicitud, CategoriaSolicitud.ALTA_SERVICIO)

    def test_campos_base_solicitud(self):
        self.assertEqual(self.dto.titulo, "Alta de línea")
        self.assertEqual(self.dto.estado, EstadoRequerimiento.ABIERTO)


if __name__ == "__main__":
    unittest.main()
