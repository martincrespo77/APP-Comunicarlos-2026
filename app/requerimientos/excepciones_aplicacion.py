"""Excepciones de la capa de aplicación del módulo de requerimientos.

Separadas intencionalmente de ``excepciones.py`` (que contiene las
excepciones de dominio: RequerimientoError, TransicionEstadoInvalida,
OperacionNoAutorizada).

Estas excepciones son generadas por el servicio, no por la entidad.
"""


class RequerimientoAplicacionError(Exception):
    """Error base de la capa de aplicación de requerimientos."""


class RequerimientoNoEncontrado(RequerimientoAplicacionError):
    """No existe un requerimiento con el ID indicado."""
