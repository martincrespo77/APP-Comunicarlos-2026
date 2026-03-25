"""Tests de integración HTTP para app/requerimientos/router.py.

Framework: unittest.TestCase + fastapi.testclient.TestClient.
Se mantiene unittest por consistencia con el resto del proyecto.

Estrategia de aislamiento:
  ``_BaseReqTest`` sobreescribe ``get_requerimiento_service`` con un servicio
  que usa un repositorio en memoria fresco instanciado en setUp.
  ``_set_current()`` permite cambiar el usuario autenticado mid-test para
  simular distintos roles a lo largo del ciclo de vida de un requerimiento
  (ej. OPERADOR para asignar → TECNICO para iniciar → TECNICO para resolver).
  tearDown limpia app.dependency_overrides tras cada test.

Qué se prueba:
  Status codes HTTP, estructura de DTOs de respuesta, mapeo de
  excepciones de aplicación/dominio a respuestas HTTP.

  Mapeo de excepciones verificado:
    RequerimientoNoEncontrado  →  404
    OperacionNoAutorizada      →  403
    TransicionEstadoInvalida   →  422
    RequerimientoError         →  422
    ValueError (dominio)       →  422

Qué NO se prueba:
  Invariantes del dominio ni lógica de servicios, ya cubiertos en
  test_requerimientos_dominio.py y test_requerimientos_servicios.py.
"""

from __future__ import annotations

import unittest
from typing import Optional

from fastapi.testclient import TestClient

from main import app
from app.compartido.dominio import RolUsuario
from app.deps import UsuarioActual, get_current_user, get_requerimiento_service
from app.notificaciones.dominio import DespachadorEventos
from app.requerimientos.dominio import EstadoRequerimiento, Requerimiento
from app.requerimientos.repositorio import RepositorioRequerimiento
from app.requerimientos.servicios import RequerimientoService


# ── Repositorio en memoria para tests ───────────────────────────────

class _RepoReqFresh(RepositorioRequerimiento):
    """Repositorio en memoria aislado por instancia de test."""

    def __init__(self) -> None:
        self._store: dict[str, Requerimiento] = {}

    def guardar(self, r: Requerimiento) -> None:
        self._store[r.id] = r

    def obtener_por_id(self, rid: str) -> Optional[Requerimiento]:
        return self._store.get(rid)

    def listar(self) -> list[Requerimiento]:
        return list(self._store.values())

    def listar_por_solicitante(self, sol_id: str) -> list[Requerimiento]:
        return [r for r in self._store.values() if r.solicitante_id == sol_id]

    def listar_por_tecnico(self, tec_id: str) -> list[Requerimiento]:
        return [r for r in self._store.values() if r.tecnico_asignado_id == tec_id]

    def listar_por_estado(self, estado: EstadoRequerimiento) -> list[Requerimiento]:
        return [r for r in self._store.values() if r.estado == estado]


# ── Payloads de test ─────────────────────────────────────────────────

_INCIDENTE_BODY = {
    "titulo": "Servidor caído",
    "descripcion": "El servidor principal no responde desde las 08:00",
    "solicitante_id": "sol-1",
    "urgencia": "critica",
    "categoria": "servicio_inaccesible",
}

_SOLICITUD_BODY = {
    "titulo": "Alta de línea de telefonía",
    "descripcion": "Se requiere una nueva línea corporativa",
    "solicitante_id": "sol-1",
    "categoria": "alta_servicio",
}


# ── Clase base ───────────────────────────────────────────────────────

class _BaseReqTest(unittest.TestCase):
    """Base: cliente HTTP con repo fresco y helpers de ciclo de vida.

    Los helpers ``_asignar`` / ``_iniciar`` cambian temporalmente el
    usuario autenticado al rol necesario (OPERADOR / TECNICO) antes
    de cada request de setup, lo que permite encadenar pasos de ciclo
    de vida dentro de un mismo test.
    """

    _OPERADOR = UsuarioActual(id="op-1", rol=RolUsuario.OPERADOR)
    _TECNICO = UsuarioActual(id="tec-1", rol=RolUsuario.TECNICO)
    _SUPERVISOR = UsuarioActual(id="sup-1", rol=RolUsuario.SUPERVISOR)

    def setUp(self):
        self._repo = _RepoReqFresh()
        app.dependency_overrides[get_requerimiento_service] = (
            lambda: RequerimientoService(self._repo, DespachadorEventos())
        )
        app.dependency_overrides[get_current_user] = lambda: self._OPERADOR
        self.client = TestClient(app)

    def tearDown(self):
        app.dependency_overrides.clear()

    def _set_current(self, usuario: UsuarioActual) -> None:
        """Cambia el usuario autenticado para el próximo request."""
        app.dependency_overrides[get_current_user] = lambda: usuario

    # ── Helpers de creación y ciclo de vida ─────────────────────────

    def _crear_incidente(
        self,
        solicitante_id: str = "sol-1",
        titulo: str = "Servidor caído",
    ) -> str:
        """Crea un incidente (no requiere usuario autenticado) y retorna el ID."""
        body = {**_INCIDENTE_BODY, "solicitante_id": solicitante_id, "titulo": titulo}
        resp = self.client.post("/requerimientos/incidentes", json=body)
        self.assertEqual(resp.status_code, 201, msg=f"Fallo al crear incidente: {resp.text}")
        return resp.json()["id"]

    def _crear_solicitud(self, solicitante_id: str = "sol-1") -> str:
        body = {**_SOLICITUD_BODY, "solicitante_id": solicitante_id}
        resp = self.client.post("/requerimientos/solicitudes", json=body)
        self.assertEqual(resp.status_code, 201, msg=f"Fallo al crear solicitud: {resp.text}")
        return resp.json()["id"]

    def _asignar(self, req_id: str, tecnico_id: str = "tec-1") -> None:
        """Asigna el requerimiento actuando como OPERADOR."""
        self._set_current(self._OPERADOR)
        r = self.client.post(
            f"/requerimientos/{req_id}/asignar", json={"tecnico_id": tecnico_id}
        )
        self.assertEqual(r.status_code, 204, msg=f"Fallo al asignar: {r.text}")

    def _iniciar(self, req_id: str, tecnico_id: str = "tec-1") -> None:
        """Inicia trabajo actuando como el técnico asignado."""
        self._set_current(UsuarioActual(id=tecnico_id, rol=RolUsuario.TECNICO))
        r = self.client.post(f"/requerimientos/{req_id}/iniciar")
        self.assertEqual(r.status_code, 204, msg=f"Fallo al iniciar: {r.text}")


# ═══════════════════════════════════════════════════════════
#  POST /requerimientos/incidentes
# ═══════════════════════════════════════════════════════════


class TestCrearIncidente(_BaseReqTest):

    def test_retorna_201_con_id(self):
        resp = self.client.post("/requerimientos/incidentes", json=_INCIDENTE_BODY)
        self.assertEqual(resp.status_code, 201)
        self.assertIn("id", resp.json())
        self.assertIsInstance(resp.json()["id"], str)

    def test_titulo_en_blanco_retorna_422(self):
        """El dominio rechaza un título vacío → router mapea a 422."""
        body = {**_INCIDENTE_BODY, "titulo": "   "}
        resp = self.client.post("/requerimientos/incidentes", json=body)
        self.assertEqual(resp.status_code, 422)

    def test_urgencia_invalida_retorna_422_por_pydantic(self):
        """Pydantic rechaza el enum desconocido antes de llegar al servicio."""
        body = {**_INCIDENTE_BODY, "urgencia": "extrema"}
        resp = self.client.post("/requerimientos/incidentes", json=body)
        self.assertEqual(resp.status_code, 422)


# ═══════════════════════════════════════════════════════════
#  POST /requerimientos/solicitudes
# ═══════════════════════════════════════════════════════════


class TestCrearSolicitud(_BaseReqTest):

    def test_retorna_201_con_id(self):
        resp = self.client.post("/requerimientos/solicitudes", json=_SOLICITUD_BODY)
        self.assertEqual(resp.status_code, 201)
        self.assertIn("id", resp.json())

    def test_categoria_invalida_retorna_422_por_pydantic(self):
        body = {**_SOLICITUD_BODY, "categoria": "categoria_magica"}
        resp = self.client.post("/requerimientos/solicitudes", json=body)
        self.assertEqual(resp.status_code, 422)


# ═══════════════════════════════════════════════════════════
#  GET /requerimientos/{id}
# ═══════════════════════════════════════════════════════════


class TestObtenerRequerimiento(_BaseReqTest):

    def test_incidente_existente_retorna_200_con_dto_completo(self):
        rid = self._crear_incidente()
        resp = self.client.get(f"/requerimientos/{rid}")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        for campo in ("id", "titulo", "descripcion", "tipo", "estado",
                      "solicitante_id", "comentarios", "eventos"):
            self.assertIn(campo, data, f"campo '{campo}' ausente en el DTO")

    def test_incidente_retorna_tipo_correcto(self):
        rid = self._crear_incidente()
        data = self.client.get(f"/requerimientos/{rid}").json()
        self.assertEqual(data["tipo"], "incidente")
        self.assertEqual(data["urgencia"], "critica")
        self.assertIsNone(data["categoria_solicitud"])

    def test_solicitud_retorna_tipo_correcto(self):
        rid = self._crear_solicitud()
        data = self.client.get(f"/requerimientos/{rid}").json()
        self.assertEqual(data["tipo"], "solicitud")
        self.assertIsNone(data["urgencia"])
        self.assertEqual(data["categoria_solicitud"], "alta_servicio")

    def test_dto_incluye_evento_creacion(self):
        rid = self._crear_incidente()
        data = self.client.get(f"/requerimientos/{rid}").json()
        self.assertEqual(len(data["eventos"]), 1)
        self.assertEqual(data["eventos"][0]["tipo"], "creacion")

    def test_inexistente_retorna_404(self):
        resp = self.client.get("/requerimientos/id-fantasma")
        self.assertEqual(resp.status_code, 404)


# ═══════════════════════════════════════════════════════════
#  GET /requerimientos/ (listado + filtros)
# ═══════════════════════════════════════════════════════════


class TestListarRequerimientos(_BaseReqTest):

    def test_lista_vacia_retorna_200(self):
        resp = self.client.get("/requerimientos/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json(), [])

    def test_lista_con_multiples_reqs_retorna_200_con_todos(self):
        self._crear_incidente()
        self._crear_solicitud()
        resp = self.client.get("/requerimientos/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.json()), 2)

    def test_filtro_por_solicitante_id(self):
        self._crear_incidente(solicitante_id="sol-A")
        self._crear_incidente(solicitante_id="sol-B")
        resp = self.client.get("/requerimientos/", params={"solicitante_id": "sol-A"})
        self.assertEqual(resp.status_code, 200)
        datos = resp.json()
        self.assertEqual(len(datos), 1)
        self.assertEqual(datos[0]["solicitante_id"], "sol-A")

    def test_filtro_por_estado_abierto(self):
        self._crear_incidente()
        self._crear_incidente(titulo="Segundo")
        resp = self.client.get("/requerimientos/", params={"estado": "abierto"})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.json()), 2)

    def test_filtro_por_tecnico_id(self):
        rid = self._crear_incidente()
        self._asignar(rid, tecnico_id="tec-filtro")
        resp = self.client.get("/requerimientos/", params={"tecnico_id": "tec-filtro"})
        self.assertEqual(resp.status_code, 200)
        datos = resp.json()
        self.assertEqual(len(datos), 1)
        self.assertEqual(datos[0]["tecnico_asignado_id"], "tec-filtro")

    def test_estado_invalido_retorna_422_por_pydantic(self):
        """FastAPI valida el query param enum antes de llegar al handler."""
        resp = self.client.get("/requerimientos/", params={"estado": "inexistente"})
        self.assertEqual(resp.status_code, 422)


# ═══════════════════════════════════════════════════════════
#  POST /{id}/asignar
# ═══════════════════════════════════════════════════════════


class TestAsignarTecnico(_BaseReqTest):

    def test_operador_asigna_retorna_204(self):
        rid = self._crear_incidente()
        self._set_current(self._OPERADOR)
        resp = self.client.post(f"/requerimientos/{rid}/asignar",
                                json={"tecnico_id": "tec-1"})
        self.assertEqual(resp.status_code, 204)

    def test_supervisor_no_puede_asignar_retorna_403(self):
        """El dominio solo permite OPERADOR → router mapea a 403."""
        rid = self._crear_incidente()
        self._set_current(self._SUPERVISOR)
        resp = self.client.post(f"/requerimientos/{rid}/asignar",
                                json={"tecnico_id": "tec-1"})
        self.assertEqual(resp.status_code, 403)

    def test_requerimiento_inexistente_retorna_404(self):
        self._set_current(self._OPERADOR)
        resp = self.client.post("/requerimientos/no-existe/asignar",
                                json={"tecnico_id": "tec-1"})
        self.assertEqual(resp.status_code, 404)

    def test_estado_resuelto_no_permite_asignar_retorna_422(self):
        """Un req RESUELTO rechaza nuevas asignaciones → TransicionEstadoInvalida → 422."""
        rid = self._crear_incidente()
        self._asignar(rid)
        self._iniciar(rid)
        self._set_current(self._TECNICO)
        self.client.post(f"/requerimientos/{rid}/resolver")  # → RESUELTO

        self._set_current(self._OPERADOR)
        resp = self.client.post(f"/requerimientos/{rid}/asignar",
                                json={"tecnico_id": "tec-2"})
        self.assertEqual(resp.status_code, 422)


# ═══════════════════════════════════════════════════════════
#  POST /{id}/iniciar
# ═══════════════════════════════════════════════════════════


class TestIniciarTrabajo(_BaseReqTest):

    def setUp(self):
        super().setUp()
        self._rid = self._crear_incidente()
        self._asignar(self._rid, tecnico_id="tec-1")

    def test_tecnico_asignado_retorna_204(self):
        self._set_current(UsuarioActual(id="tec-1", rol=RolUsuario.TECNICO))
        resp = self.client.post(f"/requerimientos/{self._rid}/iniciar")
        self.assertEqual(resp.status_code, 204)

    def test_tecnico_distinto_retorna_403(self):
        """Solo el técnico asignado puede iniciar → 403 para cualquier otro."""
        self._set_current(UsuarioActual(id="tec-impostor", rol=RolUsuario.TECNICO))
        resp = self.client.post(f"/requerimientos/{self._rid}/iniciar")
        self.assertEqual(resp.status_code, 403)

    def test_req_sin_asignar_retorna_422(self):
        """Estado ABIERTO → TransicionEstadoInvalida → 422."""
        rid_abierto = self._crear_incidente(titulo="Incidente sin asignar")
        self._set_current(self._TECNICO)
        resp = self.client.post(f"/requerimientos/{rid_abierto}/iniciar")
        self.assertEqual(resp.status_code, 422)

    def test_requerimiento_inexistente_retorna_404(self):
        self._set_current(self._TECNICO)
        resp = self.client.post("/requerimientos/fantasma/iniciar")
        self.assertEqual(resp.status_code, 404)


# ═══════════════════════════════════════════════════════════
#  POST /{id}/resolver
# ═══════════════════════════════════════════════════════════


class TestResolver(_BaseReqTest):

    def setUp(self):
        super().setUp()
        self._rid = self._crear_incidente()
        self._asignar(self._rid, tecnico_id="tec-1")
        self._iniciar(self._rid, tecnico_id="tec-1")

    def test_tecnico_asignado_retorna_204(self):
        self._set_current(UsuarioActual(id="tec-1", rol=RolUsuario.TECNICO))
        resp = self.client.post(f"/requerimientos/{self._rid}/resolver")
        self.assertEqual(resp.status_code, 204)

    def test_tecnico_distinto_retorna_403(self):
        self._set_current(UsuarioActual(id="tec-impostor", rol=RolUsuario.TECNICO))
        resp = self.client.post(f"/requerimientos/{self._rid}/resolver")
        self.assertEqual(resp.status_code, 403)

    def test_req_no_en_progreso_retorna_422(self):
        """Estado ASIGNADO no permite pasar a RESUELTO → TransicionEstadoInvalida → 422."""
        rid_asignado = self._crear_incidente(titulo="Solo asignado")
        self._asignar(rid_asignado)
        self._set_current(self._TECNICO)  # id="tec-1" es el asignado
        resp = self.client.post(f"/requerimientos/{rid_asignado}/resolver")
        self.assertEqual(resp.status_code, 422)

    def test_requerimiento_inexistente_retorna_404(self):
        self._set_current(self._TECNICO)
        resp = self.client.post("/requerimientos/fantasma/resolver")
        self.assertEqual(resp.status_code, 404)


# ═══════════════════════════════════════════════════════════
#  POST /{id}/derivar
# ═══════════════════════════════════════════════════════════


class TestDerivar(_BaseReqTest):

    _BODY_DERIVAR = {
        "tecnico_destino_id": "tec-2",
        "motivo": "Requiere especialización en redes",
    }

    def setUp(self):
        super().setUp()
        self._rid = self._crear_incidente()
        self._asignar(self._rid, tecnico_id="tec-1")

    def test_tecnico_asignado_deriva_retorna_204(self):
        self._set_current(UsuarioActual(id="tec-1", rol=RolUsuario.TECNICO))
        resp = self.client.post(f"/requerimientos/{self._rid}/derivar",
                                json=self._BODY_DERIVAR)
        self.assertEqual(resp.status_code, 204)

    def test_tecnico_distinto_retorna_403(self):
        self._set_current(UsuarioActual(id="tec-impostor", rol=RolUsuario.TECNICO))
        resp = self.client.post(f"/requerimientos/{self._rid}/derivar",
                                json=self._BODY_DERIVAR)
        self.assertEqual(resp.status_code, 403)

    def test_motivo_en_blanco_retorna_422(self):
        """El dominio rechaza motivo vacío → RequerimientoError → 422."""
        self._set_current(UsuarioActual(id="tec-1", rol=RolUsuario.TECNICO))
        resp = self.client.post(f"/requerimientos/{self._rid}/derivar",
                                json={"tecnico_destino_id": "tec-2", "motivo": "   "})
        self.assertEqual(resp.status_code, 422)

    def test_mismo_tecnico_retorna_422(self):
        """No se puede derivar al mismo técnico → RequerimientoError → 422."""
        self._set_current(UsuarioActual(id="tec-1", rol=RolUsuario.TECNICO))
        resp = self.client.post(f"/requerimientos/{self._rid}/derivar",
                                json={"tecnico_destino_id": "tec-1", "motivo": "Motivo"})
        self.assertEqual(resp.status_code, 422)

    def test_requerimiento_inexistente_retorna_404(self):
        self._set_current(self._TECNICO)
        resp = self.client.post("/requerimientos/fantasma/derivar",
                                json=self._BODY_DERIVAR)
        self.assertEqual(resp.status_code, 404)


# ═══════════════════════════════════════════════════════════
#  POST /{id}/comentarios
# ═══════════════════════════════════════════════════════════


class TestAgregarComentario(_BaseReqTest):

    def setUp(self):
        super().setUp()
        self._rid = self._crear_incidente()

    def test_operador_puede_comentar_retorna_204(self):
        self._set_current(self._OPERADOR)
        resp = self.client.post(f"/requerimientos/{self._rid}/comentarios",
                                json={"contenido": "Revisando el caso"})
        self.assertEqual(resp.status_code, 204)

    def test_supervisor_no_puede_comentar_retorna_403(self):
        """El dominio prohíbe al SUPERVISOR comentar directamente → 403."""
        self._set_current(self._SUPERVISOR)
        resp = self.client.post(f"/requerimientos/{self._rid}/comentarios",
                                json={"contenido": "Comentario del jefe"})
        self.assertEqual(resp.status_code, 403)

    def test_requerimiento_inexistente_retorna_404(self):
        self._set_current(self._OPERADOR)
        resp = self.client.post("/requerimientos/no-existe/comentarios",
                                json={"contenido": "Comentario"})
        self.assertEqual(resp.status_code, 404)

    def test_comentario_se_refleja_en_dto_de_detalle(self):
        """El comentario persiste y aparece al hacer GET del requerimiento."""
        self._set_current(self._OPERADOR)
        self.client.post(f"/requerimientos/{self._rid}/comentarios",
                         json={"contenido": "Primer comentario"})
        data = self.client.get(f"/requerimientos/{self._rid}").json()
        self.assertEqual(len(data["comentarios"]), 1)
        self.assertEqual(data["comentarios"][0]["contenido"], "Primer comentario")
        self.assertEqual(data["comentarios"][0]["rol_autor"], "operador")


# ═══════════════════════════════════════════════════════════
#  Visibilidad por rol — GET /requerimientos/ (listado)
# ═══════════════════════════════════════════════════════════


class TestListarRequerimientosPorRol(_BaseReqTest):
    """El listado filtra automáticamente según el rol del usuario."""

    def test_solicitante_ve_solo_sus_propios_reqs(self):
        """SOLICITANTE solo ve los reqs donde es el creador."""
        # Creamos 2 reqs como OPERADOR con distintos solicitantes
        self._crear_incidente(solicitante_id="sol-mio")
        self._crear_incidente(solicitante_id="sol-otro")

        self._set_current(UsuarioActual(id="sol-mio", rol=RolUsuario.SOLICITANTE))
        resp = self.client.get("/requerimientos/")
        self.assertEqual(resp.status_code, 200)
        datos = resp.json()
        self.assertEqual(len(datos), 1)
        self.assertEqual(datos[0]["solicitante_id"], "sol-mio")

    def test_solicitante_con_cero_reqs_ve_lista_vacia(self):
        self._crear_incidente(solicitante_id="sol-otro")
        self._set_current(UsuarioActual(id="sol-sin-reqs", rol=RolUsuario.SOLICITANTE))
        resp = self.client.get("/requerimientos/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json(), [])

    def test_solicitante_no_puede_usar_filtro_de_otro(self):
        """El filtro solicitante_id es ignorado para SOLICITANTE: siempre ve solo los suyos."""
        self._crear_incidente(solicitante_id="sol-A")
        self._crear_incidente(solicitante_id="sol-B")

        # Sol-A intenta ver los reqs de sol-B con el parámetro de query
        self._set_current(UsuarioActual(id="sol-A", rol=RolUsuario.SOLICITANTE))
        resp = self.client.get("/requerimientos/", params={"solicitante_id": "sol-B"})
        self.assertEqual(resp.status_code, 200)
        datos = resp.json()
        # Debe ignorar el query param y retornar solo los de sol-A
        self.assertEqual(len(datos), 1)
        self.assertEqual(datos[0]["solicitante_id"], "sol-A")

    def test_tecnico_ve_solo_los_reqs_que_tiene_asignados(self):
        rid1 = self._crear_incidente(titulo="Para tec-1")
        rid2 = self._crear_incidente(titulo="Para tec-2")  # noqa: F841
        self._asignar(rid1, tecnico_id="tec-filtro")

        self._set_current(UsuarioActual(id="tec-filtro", rol=RolUsuario.TECNICO))
        resp = self.client.get("/requerimientos/")
        self.assertEqual(resp.status_code, 200)
        datos = resp.json()
        self.assertEqual(len(datos), 1)
        self.assertEqual(datos[0]["tecnico_asignado_id"], "tec-filtro")

    def test_tecnico_sin_asignaciones_ve_lista_vacia(self):
        self._crear_incidente()  # asignado a nadie
        self._set_current(UsuarioActual(id="tec-libre", rol=RolUsuario.TECNICO))
        resp = self.client.get("/requerimientos/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json(), [])

    def test_supervisor_ve_todos_los_reqs(self):
        self._crear_incidente(titulo="Uno")
        self._crear_incidente(titulo="Dos")
        self._set_current(self._SUPERVISOR)
        resp = self.client.get("/requerimientos/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.json()), 2)

    def test_operador_puede_filtrar_por_solicitante(self):
        """OPERADOR mantiene la capacidad de filtrar por cualquier parámetro."""
        self._crear_incidente(solicitante_id="sol-X")
        self._crear_incidente(solicitante_id="sol-Y")
        resp = self.client.get("/requerimientos/", params={"solicitante_id": "sol-X"})
        self.assertEqual(resp.status_code, 200)
        datos = resp.json()
        self.assertEqual(len(datos), 1)
        self.assertEqual(datos[0]["solicitante_id"], "sol-X")


# ═══════════════════════════════════════════════════════════
#  Visibilidad por rol — GET /requerimientos/{id}
# ═══════════════════════════════════════════════════════════


class TestObtenerRequerimientoPorRol(_BaseReqTest):
    """Acceso al detalle de un requerimiento filtrado por rol."""

    def test_solicitante_puede_ver_su_propio_req(self):
        rid = self._crear_incidente(solicitante_id="sol-prop")
        self._set_current(UsuarioActual(id="sol-prop", rol=RolUsuario.SOLICITANTE))
        resp = self.client.get(f"/requerimientos/{rid}")
        self.assertEqual(resp.status_code, 200)

    def test_solicitante_no_puede_ver_req_ajeno_retorna_403(self):
        rid = self._crear_incidente(solicitante_id="sol-prop")
        self._set_current(UsuarioActual(id="sol-otro", rol=RolUsuario.SOLICITANTE))
        resp = self.client.get(f"/requerimientos/{rid}")
        self.assertEqual(resp.status_code, 403)

    def test_tecnico_puede_ver_req_que_tiene_asignado(self):
        rid = self._crear_incidente()
        self._asignar(rid, tecnico_id="tec-asig")
        self._set_current(UsuarioActual(id="tec-asig", rol=RolUsuario.TECNICO))
        resp = self.client.get(f"/requerimientos/{rid}")
        self.assertEqual(resp.status_code, 200)

    def test_tecnico_no_puede_ver_req_no_asignado_retorna_403(self):
        rid = self._crear_incidente()
        # No asignamos a nadie (tecnico_asignado_id es None)
        self._set_current(UsuarioActual(id="tec-libre", rol=RolUsuario.TECNICO))
        resp = self.client.get(f"/requerimientos/{rid}")
        self.assertEqual(resp.status_code, 403)

    def test_tecnico_no_puede_ver_req_asignado_a_otro_retorna_403(self):
        rid = self._crear_incidente()
        self._asignar(rid, tecnico_id="tec-A")
        self._set_current(UsuarioActual(id="tec-B", rol=RolUsuario.TECNICO))
        resp = self.client.get(f"/requerimientos/{rid}")
        self.assertEqual(resp.status_code, 403)

    def test_operador_puede_ver_cualquier_req(self):
        rid = self._crear_incidente(solicitante_id="sol-cualquiera")
        resp = self.client.get(f"/requerimientos/{rid}")
        self.assertEqual(resp.status_code, 200)

    def test_supervisor_puede_ver_cualquier_req(self):
        rid = self._crear_incidente()
        self._set_current(self._SUPERVISOR)
        resp = self.client.get(f"/requerimientos/{rid}")
        self.assertEqual(resp.status_code, 200)


# ═══════════════════════════════════════════════════════════
#  Creación con rol SOLICITANTE
# ═══════════════════════════════════════════════════════════


class TestCrearComoSolicitante(_BaseReqTest):
    """Cuando el rol es SOLICITANTE, solicitante_id se fuerza al current.id."""

    def test_incidente_usa_id_del_usuario_autenticado(self):
        """El solicitante_id del body es ignorado; se usa current.id."""
        self._set_current(UsuarioActual(id="sol-real", rol=RolUsuario.SOLICITANTE))
        body = {**_INCIDENTE_BODY, "solicitante_id": "intento-de-suplantacion"}
        resp = self.client.post("/requerimientos/incidentes", json=body)
        self.assertEqual(resp.status_code, 201)

        # Verificar que el req quedó con el id correcto
        rid = resp.json()["id"]
        self._set_current(self._OPERADOR)  # OPERADOR puede ver el req
        data = self.client.get(f"/requerimientos/{rid}").json()
        self.assertEqual(data["solicitante_id"], "sol-real")

    def test_solicitud_usa_id_del_usuario_autenticado(self):
        self._set_current(UsuarioActual(id="sol-legit", rol=RolUsuario.SOLICITANTE))
        body = {**_SOLICITUD_BODY, "solicitante_id": "otro-id"}
        resp = self.client.post("/requerimientos/solicitudes", json=body)
        self.assertEqual(resp.status_code, 201)

        rid = resp.json()["id"]
        self._set_current(self._OPERADOR)
        data = self.client.get(f"/requerimientos/{rid}").json()
        self.assertEqual(data["solicitante_id"], "sol-legit")


if __name__ == "__main__":
    unittest.main()
