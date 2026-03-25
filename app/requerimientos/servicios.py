"""Capa de servicios de aplicación — módulo de requerimientos.

Orquesta repositorio de requerimientos y despacho de eventos.
No contiene lógica de negocio: las reglas de estado, permisos y
transiciones viven en ``app.requerimientos.dominio``.

Las excepciones de dominio (TransicionEstadoInvalida, OperacionNoAutorizada)
se dejan propagar sin capturar: el router las traducirá a HTTP.
"""

from __future__ import annotations

from app.compartido.dominio import RolUsuario
from app.notificaciones.dominio import DespachadorEventos
from app.requerimientos.dominio import (
    CategoriaIncidente,
    CategoriaSolicitud,
    EstadoRequerimiento,
    Requerimiento,
    RequerimientoFactory,
    Urgencia,
)
from app.requerimientos.excepciones_aplicacion import RequerimientoNoEncontrado
from app.requerimientos.repositorio import RepositorioRequerimiento


class RequerimientoService:
    """Casos de uso del módulo de requerimientos."""

    def __init__(
        self,
        repo: RepositorioRequerimiento,
        despachador: DespachadorEventos,
    ) -> None:
        self._repo = repo
        self._despachador = despachador

    # ── Métodos internos ──────────────────────────────────────────

    def _obtener_o_fallar(self, requerimiento_id: str) -> Requerimiento:
        req = self._repo.obtener_por_id(requerimiento_id)
        if req is None:
            raise RequerimientoNoEncontrado(
                f"Requerimiento '{requerimiento_id}' no encontrado."
            )
        return req

    def _guardar_y_despachar(self, requerimiento: Requerimiento) -> None:
        self._repo.guardar(requerimiento)
        for evento in requerimiento.recolectar_eventos():
            self._despachador.despachar(evento, requerimiento.id)

    # ── Casos de uso: creación ────────────────────────────────────

    def crear_incidente(
        self,
        titulo: str,
        descripcion: str,
        solicitante_id: str,
        urgencia: Urgencia,
        categoria: CategoriaIncidente,
    ) -> str:
        """Crea un nuevo incidente y lo persiste.

        Returns:
            El ID del incidente creado.
        """
        incidente = RequerimientoFactory.crear_incidente(
            titulo=titulo,
            descripcion=descripcion,
            solicitante_id=solicitante_id,
            urgencia=urgencia,
            categoria=categoria,
        )
        self._guardar_y_despachar(incidente)
        return incidente.id

    def crear_solicitud(
        self,
        titulo: str,
        descripcion: str,
        solicitante_id: str,
        categoria: CategoriaSolicitud,
    ) -> str:
        """Crea una nueva solicitud y la persiste.

        Returns:
            El ID de la solicitud creada.
        """
        solicitud = RequerimientoFactory.crear_solicitud(
            titulo=titulo,
            descripcion=descripcion,
            solicitante_id=solicitante_id,
            categoria=categoria,
        )
        self._guardar_y_despachar(solicitud)
        return solicitud.id

    # ── Casos de uso: ciclo de vida ───────────────────────────────

    def asignar_tecnico(
        self,
        requerimiento_id: str,
        tecnico_id: str,
        actor_id: str,
        rol_actor: RolUsuario,
    ) -> None:
        """Asigna o reasigna un técnico al requerimiento.

        Raises:
            RequerimientoNoEncontrado: si no existe el requerimiento.
            OperacionNoAutorizada:     si el actor no es operador.
            TransicionEstadoInvalida:  si el estado no permite asignación.
        """
        req = self._obtener_o_fallar(requerimiento_id)
        req.asignar_tecnico(tecnico_id, actor_id, rol_actor)
        self._guardar_y_despachar(req)

    def iniciar_trabajo(self, requerimiento_id: str, tecnico_id: str) -> None:
        """El técnico asignado marca el requerimiento como en progreso.

        Raises:
            RequerimientoNoEncontrado: si no existe el requerimiento.
            OperacionNoAutorizada:     si no es el técnico asignado.
            TransicionEstadoInvalida:  si el estado no lo permite.
        """
        req = self._obtener_o_fallar(requerimiento_id)
        req.iniciar_trabajo(tecnico_id)
        self._guardar_y_despachar(req)

    def resolver(self, requerimiento_id: str, tecnico_id: str) -> None:
        """El técnico asignado marca el requerimiento como resuelto.

        Raises:
            RequerimientoNoEncontrado: si no existe el requerimiento.
            OperacionNoAutorizada:     si no es el técnico asignado.
            TransicionEstadoInvalida:  si el estado no lo permite.
        """
        req = self._obtener_o_fallar(requerimiento_id)
        req.resolver(tecnico_id)
        self._guardar_y_despachar(req)

    def derivar(
        self,
        requerimiento_id: str,
        tecnico_origen_id: str,
        tecnico_destino_id: str,
        motivo: str,
    ) -> None:
        """El técnico asignado deriva el requerimiento a otro técnico.

        Raises:
            RequerimientoNoEncontrado: si no existe el requerimiento.
            OperacionNoAutorizada:     si no es el técnico asignado.
            RequerimientoError:        si el motivo está vacío o se deriva
                                       al mismo técnico.
        """
        req = self._obtener_o_fallar(requerimiento_id)
        req.derivar(tecnico_origen_id, tecnico_destino_id, motivo)
        self._guardar_y_despachar(req)

    def agregar_comentario(
        self,
        requerimiento_id: str,
        autor_id: str,
        rol_autor: RolUsuario,
        contenido: str,
    ) -> None:
        """Agrega un comentario al requerimiento.

        Puede provocar reapertura automática si el estado es RESUELTO
        y el autor es operador o técnico (lógica del dominio).

        Raises:
            RequerimientoNoEncontrado: si no existe el requerimiento.
            OperacionNoAutorizada:     si el rol no tiene permiso.
        """
        req = self._obtener_o_fallar(requerimiento_id)
        req.agregar_comentario(autor_id, rol_autor, contenido)
        self._guardar_y_despachar(req)

    # ── Casos de uso: consultas ───────────────────────────────────

    def obtener(self, requerimiento_id: str) -> Requerimiento:
        """Retorna el requerimiento con ese ID.

        Raises:
            RequerimientoNoEncontrado: si no existe.
        """
        return self._obtener_o_fallar(requerimiento_id)

    def listar(self) -> list[Requerimiento]:
        """Retorna todos los requerimientos del sistema."""
        return self._repo.listar()

    def listar_por_solicitante(self, solicitante_id: str) -> list[Requerimiento]:
        """Retorna los requerimientos del solicitante indicado."""
        return self._repo.listar_por_solicitante(solicitante_id)

    def listar_por_tecnico(self, tecnico_id: str) -> list[Requerimiento]:
        """Retorna los requerimientos asignados al técnico indicado."""
        return self._repo.listar_por_tecnico(tecnico_id)

    def listar_por_estado(self, estado: EstadoRequerimiento) -> list[Requerimiento]:
        """Retorna los requerimientos en el estado indicado."""
        return self._repo.listar_por_estado(estado)
