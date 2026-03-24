"""Tests unitarios — Excepciones del dominio de requerimientos.

Verifica la jerarquía de excepciones y que todas hereden de ValueError,
permitiendo captura uniforme junto con validaciones estándar de Python.

STYLEGUIDE_PROFE: unittest, setUp, tearDown, AAA, test_<comportamiento>.
"""

import unittest

from app.requerimientos.excepciones import (
    OperacionNoAutorizada,
    RequerimientoError,
    TransicionEstadoInvalida,
)


class TestJerarquiaExcepciones(unittest.TestCase):
    """Verifica la jerarquía de herencia de las excepciones de dominio."""

    def setUp(self):
        """Sin estado compartido — cada test es atómico."""
        pass

    def tearDown(self):
        pass

    # ── Herencia de ValueError ──

    def test_requerimiento_error_es_subclase_de_value_error(self):
        # Arrange / Act / Assert
        self.assertTrue(issubclass(RequerimientoError, ValueError))

    def test_transicion_estado_invalida_es_subclase_de_requerimiento_error(self):
        # Arrange / Act / Assert
        self.assertTrue(issubclass(TransicionEstadoInvalida, RequerimientoError))

    def test_operacion_no_autorizada_es_subclase_de_requerimiento_error(self):
        # Arrange / Act / Assert
        self.assertTrue(issubclass(OperacionNoAutorizada, RequerimientoError))

    def test_transicion_estado_invalida_es_subclase_de_value_error(self):
        # Arrange / Act / Assert
        self.assertTrue(issubclass(TransicionEstadoInvalida, ValueError))

    def test_operacion_no_autorizada_es_subclase_de_value_error(self):
        # Arrange / Act / Assert
        self.assertTrue(issubclass(OperacionNoAutorizada, ValueError))

    # ── Instanciación y mensaje ──

    def test_requerimiento_error_se_puede_lanzar_con_mensaje(self):
        # Arrange
        mensaje = "Error de prueba"

        # Act / Assert
        with self.assertRaises(RequerimientoError) as ctx:
            raise RequerimientoError(mensaje)

        self.assertEqual(str(ctx.exception), mensaje)

    def test_transicion_estado_invalida_se_puede_lanzar_con_mensaje(self):
        # Arrange
        mensaje = "Transición inválida"

        # Act / Assert
        with self.assertRaises(TransicionEstadoInvalida) as ctx:
            raise TransicionEstadoInvalida(mensaje)

        self.assertEqual(str(ctx.exception), mensaje)

    def test_operacion_no_autorizada_se_puede_lanzar_con_mensaje(self):
        # Arrange
        mensaje = "No autorizado"

        # Act / Assert
        with self.assertRaises(OperacionNoAutorizada) as ctx:
            raise OperacionNoAutorizada(mensaje)

        self.assertEqual(str(ctx.exception), mensaje)

    def test_captura_como_value_error_funciona_para_todas(self):
        """Verifica que se pueden capturar con except ValueError."""
        # Arrange
        excepciones = [
            RequerimientoError("base"),
            TransicionEstadoInvalida("transicion"),
            OperacionNoAutorizada("permiso"),
        ]

        # Act / Assert
        for exc in excepciones:
            with self.subTest(exc=type(exc).__name__):
                with self.assertRaises(ValueError):
                    raise exc


if __name__ == "__main__":
    unittest.main()
