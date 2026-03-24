"""Shared Kernel — tipos compartidos entre bounded contexts.

Este módulo contiene exclusivamente los tipos que dos o más
bounded contexts necesitan conocer.  Debe mantenerse **mínimo**:
no agregar nada sin justificación de uso cruzado.
"""

from enum import Enum


class RolUsuario(Enum):
    """Roles del sistema reconocidos por múltiples bounded contexts.

    Shared kernel entre Requerimientos (permisos de dominio) y
    Usuarios (identidad del actor).
    """

    SOLICITANTE = "solicitante"
    OPERADOR = "operador"
    TECNICO = "tecnico"
    SUPERVISOR = "supervisor"
