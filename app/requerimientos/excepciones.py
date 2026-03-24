"""Excepciones de dominio del módulo de requerimientos."""


class RequerimientoError(ValueError):
    """Error base para el dominio de requerimientos.

    Hereda de ValueError para facilitar la captura junto con
    validaciones estándar de Python y mantener coherencia
    con el estilo de la cátedra.
    """


class TransicionEstadoInvalida(RequerimientoError):
    """Se intentó una transición de estado no permitida."""


class OperacionNoAutorizada(RequerimientoError):
    """El actor no tiene permiso para realizar esta operación de dominio."""
