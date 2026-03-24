"""Tests unitarios — Shared Kernel (compartido/dominio.py).

Verifica el enum RolUsuario del shared kernel: valores correctos,
identidad por comparación y que cada contexto lo puede usar.

STYLEGUIDE_PROFE: unittest, setUp, tearDown, AAA, test_<comportamiento>.
"""

import unittest

from app.compartido.dominio import RolUsuario


class TestRolUsuario(unittest.TestCase):
    """Verifica el enum RolUsuario del shared kernel."""

    def setUp(self):
        """Sin estado compartido — cada test es atómico."""
        pass

    def tearDown(self):
        pass

    # ── Valores y cantidad ──

    def test_rol_usuario_tiene_cuatro_valores(self):
        # Arrange / Act
        roles = list(RolUsuario)

        # Assert
        self.assertEqual(len(roles), 4)

    def test_rol_solicitante_tiene_valor_correcto(self):
        # Arrange / Act / Assert
        self.assertEqual(RolUsuario.SOLICITANTE.value, "solicitante")

    def test_rol_operador_tiene_valor_correcto(self):
        # Arrange / Act / Assert
        self.assertEqual(RolUsuario.OPERADOR.value, "operador")

    def test_rol_tecnico_tiene_valor_correcto(self):
        # Arrange / Act / Assert
        self.assertEqual(RolUsuario.TECNICO.value, "tecnico")

    def test_rol_supervisor_tiene_valor_correcto(self):
        # Arrange / Act / Assert
        self.assertEqual(RolUsuario.SUPERVISOR.value, "supervisor")

    # ── Identidad y comparación ──

    def test_rol_es_comparable_por_identidad(self):
        # Arrange
        rol_a = RolUsuario.OPERADOR
        rol_b = RolUsuario.OPERADOR

        # Act / Assert
        self.assertIs(rol_a, rol_b)

    def test_roles_distintos_no_son_iguales(self):
        # Arrange / Act / Assert
        self.assertNotEqual(RolUsuario.OPERADOR, RolUsuario.TECNICO)

    def test_rol_reconstruible_desde_valor_string(self):
        # Arrange
        valor = "supervisor"

        # Act
        rol = RolUsuario(valor)

        # Assert
        self.assertEqual(rol, RolUsuario.SUPERVISOR)

    # ── Importable desde requerimientos y usuarios ──

    def test_requerimientos_importa_mismo_rol_usuario(self):
        # Arrange
        from app.requerimientos.dominio import RolUsuario as RolReq

        # Act / Assert (misma clase, mismo enum)
        self.assertIs(RolReq.OPERADOR, RolUsuario.OPERADOR)

    def test_usuarios_importa_mismo_rol_usuario(self):
        # Arrange
        from app.usuarios.dominio import RolUsuario as RolUsr

        # Act / Assert
        self.assertIs(RolUsr.TECNICO, RolUsuario.TECNICO)


if __name__ == "__main__":
    unittest.main()
