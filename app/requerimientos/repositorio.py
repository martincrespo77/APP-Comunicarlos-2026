"""Contrato abstracto del repositorio de requerimientos.

Define la interfaz que cualquier implementación de persistencia de
requerimientos debe cumplir.  Sin detalles de infraestructura.

La capa de servicios depende únicamente de esta interfaz.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from app.requerimientos.dominio import EstadoRequerimiento, Requerimiento


class RepositorioRequerimiento(ABC):
    """Contrato de persistencia para el agregado Requerimiento.

    Semántica de ``guardar``:
        Actúa como upsert.  El servicio llama a ``guardar`` después de cada
        operación de dominio (asignar_tecnico, iniciar_trabajo, resolver…)
        para persistir el estado actualizado del agregado.

    Métodos de consulta:
        Los métodos ``listar_por_*`` se declaran abstractos (no como filtros
        sobre ``listar``) para permitir que la implementación concreta utilice
        consultas eficientes (por ejemplo, ``WHERE`` en SQL) en lugar de
        cargar toda la colección en memoria.
    """

    @abstractmethod
    def guardar(self, requerimiento: Requerimiento) -> None:
        """Persiste el requerimiento (inserción o actualización)."""

    @abstractmethod
    def obtener_por_id(self, requerimiento_id: str) -> Requerimiento | None:
        """Retorna el requerimiento con ese ID, o ``None`` si no existe."""

    @abstractmethod
    def listar(self) -> list[Requerimiento]:
        """Retorna todos los requerimientos del sistema.

        Uso típico: vistas de operadores y supervisores.
        """

    @abstractmethod
    def listar_por_solicitante(self, solicitante_id: str) -> list[Requerimiento]:
        """Retorna los requerimientos creados por ese solicitante.

        El TP exige que los solicitantes solo puedan ver sus propios
        requerimientos.  El servicio delega el filtrado aquí.
        """

    @abstractmethod
    def listar_por_tecnico(self, tecnico_id: str) -> list[Requerimiento]:
        """Retorna los requerimientos asignados a ese técnico.

        Utilizado por el técnico para ver su carga de trabajo actual.
        """

    @abstractmethod
    def listar_por_estado(self, estado: EstadoRequerimiento) -> list[Requerimiento]:
        """Retorna los requerimientos que se encuentran en ese estado.

        Utilizado por operadores y supervisores para monitoreo y filtrado.
        """
