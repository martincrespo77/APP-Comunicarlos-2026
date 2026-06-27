import unittest
from datetime import datetime
from uuid import uuid4

from app.compartido.dominio import RolUsuario
from app.usuarios.dominio import Usuario
from app.usuarios.servicios import UsuarioService
from tests.test_usuarios_servicios import FakeRepositorioUsuario

from app.requerimientos.dominio import (
    EstadoRequerimiento,
    CategoriaIncidente,
    Incidente,
    RequerimientoFactory,
    Urgencia,
)
from app.requerimientos.servicios import RequerimientoService
from tests.test_requerimientos_servicios import FakeRepositorioRequerimiento
from app.notificaciones.dominio import DespachadorEventos


class TestPaginacion(unittest.TestCase):
    def setUp(self):
        # Setup de usuarios
        self.repo_usuarios = FakeRepositorioUsuario()
        self.usuario_service = UsuarioService(
            repo=self.repo_usuarios,
            hasher=lambda p: f"hashed:{p}",
            verificador=lambda p, h: h == f"hashed:{p}",
        )
        
        # Guardar 5 usuarios de prueba
        for i in range(5):
            u = Usuario(
                id=f"user-{i}",
                nombre=f"Usuario {i}",
                email=f"user{i}@comunicarlos.com.ar",
                rol=RolUsuario.TECNICO,
                password_hash="hashed:Pass1234!",
            )
            self.repo_usuarios.guardar(u)

        # Setup de requerimientos
        self.repo_reqs = FakeRepositorioRequerimiento()
        self.despachador = DespachadorEventos()
        self.req_service = RequerimientoService(self.repo_reqs, self.despachador)

        # Guardar 5 requerimientos de prueba (todos del mismo solicitante y técnico)
        for i in range(5):
            req = RequerimientoFactory.crear_incidente(
                titulo=f"Incidente de prueba {i}",
                descripcion=f"Descripcion detallada del incidente {i}",
                solicitante_id="sol-1",
                urgencia=Urgencia.CRITICA,
                categoria=CategoriaIncidente.SERVICIO_INACCESIBLE,
            )
            # Reasignamos atributos para tests
            req._id = f"req-{i}"
            req._tecnico_asignado_id = "tec-1"
            req._estado = EstadoRequerimiento.ASIGNADO
            self.repo_reqs.guardar(req)

    def test_paginacion_usuarios_listar(self):
        # Listar todo
        todos = self.usuario_service.listar(skip=0, limit=10)
        self.assertEqual(len(todos), 5)

        # Listar limit 2
        primera_pagina = self.usuario_service.listar(skip=0, limit=2)
        self.assertEqual(len(primera_pagina), 2)
        self.assertEqual(primera_pagina[0].id, "user-0")
        self.assertEqual(primera_pagina[1].id, "user-1")

        # Listar skip 2, limit 2
        segunda_pagina = self.usuario_service.listar(skip=2, limit=2)
        self.assertEqual(len(segunda_pagina), 2)
        self.assertEqual(segunda_pagina[0].id, "user-2")
        self.assertEqual(segunda_pagina[1].id, "user-3")

        # Listar skip 4, limit 2
        tercera_pagina = self.usuario_service.listar(skip=4, limit=2)
        self.assertEqual(len(tercera_pagina), 1)
        self.assertEqual(tercera_pagina[0].id, "user-4")

    def test_paginacion_requerimientos_listar(self):
        # Listar todo
        todos = self.req_service.listar(skip=0, limit=10)
        self.assertEqual(len(todos), 5)

        # Listar con skip/limit
        primera_pagina = self.req_service.listar(skip=0, limit=3)
        self.assertEqual(len(primera_pagina), 3)
        self.assertEqual(primera_pagina[0].id, "req-0")
        self.assertEqual(primera_pagina[2].id, "req-2")

        # Segunda página
        segunda_pagina = self.req_service.listar(skip=3, limit=3)
        self.assertEqual(len(segunda_pagina), 2)
        self.assertEqual(segunda_pagina[0].id, "req-3")
        self.assertEqual(segunda_pagina[1].id, "req-4")

    def test_paginacion_requerimientos_por_solicitante(self):
        res = self.req_service.listar_por_solicitante("sol-1", skip=1, limit=2)
        self.assertEqual(len(res), 2)
        self.assertEqual(res[0].id, "req-1")
        self.assertEqual(res[1].id, "req-2")

    def test_paginacion_requerimientos_por_tecnico(self):
        res = self.req_service.listar_por_tecnico("tec-1", skip=2, limit=2)
        self.assertEqual(len(res), 2)
        self.assertEqual(res[0].id, "req-2")
        self.assertEqual(res[1].id, "req-3")

    def test_paginacion_requerimientos_por_estado(self):
        res = self.req_service.listar_por_estado(EstadoRequerimiento.ASIGNADO, skip=3, limit=2)
        self.assertEqual(len(res), 2)
        self.assertEqual(res[0].id, "req-3")
        self.assertEqual(res[1].id, "req-4")
