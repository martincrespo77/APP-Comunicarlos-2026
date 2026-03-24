"""Dominio del módulo de notificaciones.

Implementa el patrón Observer para notificaciones a supervisores.
La interfaz vive en el dominio; la implementación concreta con I/O
se inyectará desde la capa de servicio en fases posteriores.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from app.requerimientos.dominio import Evento


class ObservadorRequerimiento(ABC):
    """Interfaz Observer para eventos de requerimiento.

    Todo observador que quiera recibir notificaciones de cambios
    en requerimientos debe implementar esta interfaz.
    """

    @abstractmethod
    def notificar(self, evento: Evento, requerimiento_id: str) -> None:
        """Recibe una notificación de un evento sobre un requerimiento.

        Args:
            evento: El evento de auditoría que se produjo.
            requerimiento_id: ID del requerimiento afectado.
        """


class DespachadorEventos:
    """Despacha eventos de dominio a los observadores registrados.

    Componente puro (sin I/O) que implementa la mecánica del patrón
    Observer.  El Service lo instancia, registra observadores y le
    pasa los eventos generados por las operaciones de dominio.
    """

    def __init__(self) -> None:
        self._observadores: list[ObservadorRequerimiento] = []

    def registrar(self, observador: ObservadorRequerimiento) -> None:
        """Registra un observador para que reciba eventos futuros."""
        if observador not in self._observadores:
            self._observadores.append(observador)

    def quitar(self, observador: ObservadorRequerimiento) -> None:
        """Quita un observador previamente registrado."""
        self._observadores.remove(observador)

    def despachar(self, evento: Evento, requerimiento_id: str) -> None:
        """Notifica a todos los observadores registrados."""
        for observador in self._observadores:
            observador.notificar(evento, requerimiento_id)

    @property
    def cantidad_observadores(self) -> int:
        """Cantidad de observadores registrados."""
        return len(self._observadores)
