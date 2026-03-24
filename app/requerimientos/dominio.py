"""Dominio del módulo de requerimientos.

Contiene enums, value objects, entidades y factory del agregado Requerimiento.
Dominio puro: sin dependencias de frameworks, persistencia ni HTTP.

RolUsuario se importa desde el shared kernel (``app.compartido.dominio``)
y se re-exporta desde este módulo por compatibilidad con imports existentes.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
from uuid import uuid4

from app.compartido.dominio import RolUsuario
from app.requerimientos.excepciones import (
    OperacionNoAutorizada,
    RequerimientoError,
    TransicionEstadoInvalida,
)

# Re-export de compatibilidad: permite que el código existente que haga
# ``from app.requerimientos.dominio import RolUsuario`` siga funcionando
# sin cambios, aunque el enum vive en ``app.compartido.dominio``.
__all__ = ["RolUsuario"]


# ═══════════════════════════════════════════════════════════
#  ENUMS
# ═══════════════════════════════════════════════════════════


class EstadoRequerimiento(Enum):
    """Estados del ciclo de vida de un requerimiento.

    Transiciones válidas::

        ABIERTO → ASIGNADO → EN_PROGRESO → RESUELTO
                                              ↓
                  ASIGNADO ← ─ ─ ─ ─ ─ REABIERTO

    ``EN_PROGRESO`` diferencia el momento en que el técnico acepta
    trabajar activamente del momento en que fue asignado pero aún
    no inició.  Esto permite al supervisor monitorear requerimientos
    asignados sin actividad (posible indicador de SLA incumplido).
    """

    ABIERTO = "abierto"
    ASIGNADO = "asignado"
    EN_PROGRESO = "en_progreso"
    RESUELTO = "resuelto"
    REABIERTO = "reabierto"


class TipoRequerimiento(Enum):
    """Discriminador de tipo para el polimorfismo Incidente / Solicitud."""

    INCIDENTE = "incidente"
    SOLICITUD = "solicitud"


class Urgencia(Enum):
    """Niveles de urgencia aplicables exclusivamente a incidentes.

    Valores alineados al TP de la cátedra.
    """

    CRITICA = "critica"
    IMPORTANTE = "importante"
    MENOR = "menor"


class CategoriaIncidente(Enum):
    """Clasificación de incidentes según el TP."""

    SERVICIO_INACCESIBLE = "servicio_inaccesible"
    BLOQUEO_SIM = "bloqueo_sim"
    PERDIDA_O_DESTRUCCION_EQUIPO = "perdida_o_destruccion_equipo"


class CategoriaSolicitud(Enum):
    """Clasificación de solicitudes según el TP."""

    ALTA_SERVICIO = "alta_servicio"
    BAJA_SERVICIO = "baja_servicio"


class TipoEvento(Enum):
    """Tipos de eventos de auditoría registrados en un requerimiento."""

    CREACION = "creacion"
    ASIGNACION = "asignacion"
    REASIGNACION = "reasignacion"
    DERIVACION = "derivacion"
    INICIO_TRABAJO = "inicio_trabajo"
    COMENTARIO = "comentario"
    RESOLUCION = "resolucion"
    REAPERTURA = "reapertura"


# ═══════════════════════════════════════════════════════════
#  VALUE OBJECTS (inmutables)
# ═══════════════════════════════════════════════════════════


class Comentario:
    """Value object inmutable que representa un comentario en un requerimiento.

    Una vez creado no se puede modificar ni eliminar.
    Se expone mediante propiedades de solo lectura.
    """

    def __init__(
        self,
        autor_id: str,
        rol_autor: RolUsuario,
        contenido: str,
        *,
        id: str | None = None,
        fecha: datetime | None = None,
    ) -> None:
        if not contenido or not contenido.strip():
            raise ValueError("El contenido del comentario no puede estar vacío.")

        self._id = id or str(uuid4())
        self._autor_id = autor_id
        self._rol_autor = rol_autor
        self._contenido = contenido.strip()
        self._fecha = fecha or datetime.now()

    @property
    def id(self) -> str:
        return self._id

    @property
    def autor_id(self) -> str:
        return self._autor_id

    @property
    def rol_autor(self) -> RolUsuario:
        return self._rol_autor

    @property
    def contenido(self) -> str:
        return self._contenido

    @property
    def fecha(self) -> datetime:
        return self._fecha

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Comentario):
            return NotImplemented
        return self._id == other._id

    def __hash__(self) -> int:
        return hash(self._id)

    def __repr__(self) -> str:
        return (
            f"Comentario(id={self._id!r}, autor={self._autor_id!r}, "
            f"fecha={self._fecha.isoformat()})"
        )


class Evento:
    """Value object inmutable de auditoría.

    Registra cada acción relevante sobre un requerimiento.
    Append-only: nunca se elimina ni modifica.
    """

    def __init__(
        self,
        tipo: TipoEvento,
        actor_id: str,
        detalle: str,
        *,
        id: str | None = None,
        fecha: datetime | None = None,
    ) -> None:
        self._id = id or str(uuid4())
        self._tipo = tipo
        self._actor_id = actor_id
        self._detalle = detalle
        self._fecha = fecha or datetime.now()

    @property
    def id(self) -> str:
        return self._id

    @property
    def tipo(self) -> TipoEvento:
        return self._tipo

    @property
    def actor_id(self) -> str:
        return self._actor_id

    @property
    def detalle(self) -> str:
        return self._detalle

    @property
    def fecha(self) -> datetime:
        return self._fecha

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Evento):
            return NotImplemented
        return self._id == other._id

    def __hash__(self) -> int:
        return hash(self._id)

    def __repr__(self) -> str:
        return (
            f"Evento(tipo={self._tipo.value}, actor={self._actor_id!r}, "
            f"fecha={self._fecha.isoformat()})"
        )


# ═══════════════════════════════════════════════════════════
#  ENTIDAD — Requerimiento (raíz de agregado)
# ═══════════════════════════════════════════════════════════


class Requerimiento(ABC):
    """Raíz de agregado que representa un requerimiento en la mesa de ayuda.

    Encapsula el ciclo de vida completo: asignación, trabajo, resolución,
    derivación y reapertura.  Protege todas las invariantes de negocio
    a través de sus métodos públicos.

    **Eventos de dominio**: cada operación deposita eventos en una cola
    interna (``_eventos_dominio``) que el Service puede recolectar
    mediante ``recolectar_eventos()`` para despachar a observadores
    (e.g. notificaciones a supervisores).

    No se instancia directamente — usar ``Incidente`` o ``Solicitud``
    (preferentemente vía ``RequerimientoFactory``).
    """

    _TRANSICIONES_VALIDAS: dict[EstadoRequerimiento, set[EstadoRequerimiento]] = {
        EstadoRequerimiento.ABIERTO: {EstadoRequerimiento.ASIGNADO},
        EstadoRequerimiento.ASIGNADO: {
            EstadoRequerimiento.EN_PROGRESO,
            EstadoRequerimiento.ASIGNADO,  # derivación / reasignación
        },
        EstadoRequerimiento.EN_PROGRESO: {
            EstadoRequerimiento.RESUELTO,
            EstadoRequerimiento.ASIGNADO,  # derivación / reasignación
        },
        EstadoRequerimiento.RESUELTO: {EstadoRequerimiento.REABIERTO},
        EstadoRequerimiento.REABIERTO: {EstadoRequerimiento.ASIGNADO},
    }

    def __init__(
        self,
        titulo: str,
        descripcion: str,
        solicitante_id: str,
        *,
        id: str | None = None,
        estado: EstadoRequerimiento = EstadoRequerimiento.ABIERTO,
        operador_id: str | None = None,
        tecnico_asignado_id: str | None = None,
        fecha_creacion: datetime | None = None,
        fecha_actualizacion: datetime | None = None,
        registrar_creacion: bool = True,
    ) -> None:
        if not titulo or not titulo.strip():
            raise ValueError("El título no puede estar vacío.")
        if not descripcion or not descripcion.strip():
            raise ValueError("La descripción no puede estar vacía.")

        # ── Validación de consistencia estado / técnico ──
        _estados_con_tecnico = {
            EstadoRequerimiento.ASIGNADO,
            EstadoRequerimiento.EN_PROGRESO,
            EstadoRequerimiento.RESUELTO,
        }
        if estado in _estados_con_tecnico and tecnico_asignado_id is None:
            raise RequerimientoError(
                f"Estado {estado.value} requiere un técnico asignado."
            )
        _estados_sin_tecnico = {
            EstadoRequerimiento.ABIERTO,
            EstadoRequerimiento.REABIERTO,
        }
        if estado in _estados_sin_tecnico and tecnico_asignado_id is not None:
            raise RequerimientoError(
                f"Estado {estado.value} no puede tener técnico asignado."
            )

        ahora = datetime.now()
        self._id = id or str(uuid4())
        self._titulo = titulo.strip()
        self._descripcion = descripcion.strip()
        self._estado = estado
        self._solicitante_id = solicitante_id
        self._operador_id = operador_id
        self._tecnico_asignado_id = tecnico_asignado_id
        self._comentarios: list[Comentario] = []
        self._eventos: list[Evento] = []
        self._eventos_dominio: list[Evento] = []
        self._fecha_creacion = fecha_creacion or ahora
        self._fecha_actualizacion = fecha_actualizacion or ahora

        if registrar_creacion:
            self._registrar_evento(
                TipoEvento.CREACION,
                solicitante_id,
                self._detalle_creacion(),
            )

    # ── Propiedades ──

    @property
    def id(self) -> str:
        return self._id

    @property
    def titulo(self) -> str:
        return self._titulo

    @property
    def descripcion(self) -> str:
        return self._descripcion

    @property
    def estado(self) -> EstadoRequerimiento:
        return self._estado

    @property
    def solicitante_id(self) -> str:
        return self._solicitante_id

    @property
    def operador_id(self) -> str | None:
        return self._operador_id

    @property
    def tecnico_asignado_id(self) -> str | None:
        return self._tecnico_asignado_id

    @property
    def comentarios(self) -> tuple[Comentario, ...]:
        """Retorna los comentarios como tupla inmutable."""
        return tuple(self._comentarios)

    @property
    def eventos(self) -> tuple[Evento, ...]:
        """Retorna los eventos de auditoría como tupla inmutable."""
        return tuple(self._eventos)

    @property
    def fecha_creacion(self) -> datetime:
        return self._fecha_creacion

    @property
    def fecha_actualizacion(self) -> datetime:
        return self._fecha_actualizacion

    @property
    @abstractmethod
    def tipo(self) -> TipoRequerimiento:
        """Discriminador de tipo (INCIDENTE o SOLICITUD)."""

    @abstractmethod
    def _detalle_creacion(self) -> str:
        """Genera el texto de detalle para el evento CREACION."""

    # ── Eventos de dominio (para Observer / notificaciones) ──

    def recolectar_eventos(self) -> list[Evento]:
        """Retorna y vacía los eventos pendientes de despachar.

        El Service invoca este método después de cada operación
        para obtener los eventos producidos y pasarlos al
        ``DespachadorEventos``, que los envía a los observadores
        registrados (e.g. ``NotificadorSupervisor``).
        """
        pendientes = list(self._eventos_dominio)
        self._eventos_dominio.clear()
        return pendientes

    # ── Métodos internos ──

    def _validar_transicion(self, nuevo_estado: EstadoRequerimiento) -> None:
        """Verifica que la transición de estado sea válida."""
        estados_destino = self._TRANSICIONES_VALIDAS.get(self._estado, set())
        if nuevo_estado not in estados_destino:
            raise TransicionEstadoInvalida(
                f"No se puede pasar de {self._estado.value} a {nuevo_estado.value}."
            )

    def _registrar_evento(
        self, tipo: TipoEvento, actor_id: str, detalle: str
    ) -> Evento:
        """Crea un evento, lo agrega al historial de auditoría y a la
        cola de eventos de dominio pendientes de despacho."""
        evento = Evento(tipo=tipo, actor_id=actor_id, detalle=detalle)
        self._eventos.append(evento)
        self._eventos_dominio.append(evento)
        self._fecha_actualizacion = datetime.now()
        return evento

    # ── Comportamiento de negocio ──

    def asignar_tecnico(
        self, tecnico_id: str, actor_id: str, rol_actor: RolUsuario
    ) -> Evento:
        """Asigna o reasigna un técnico al requerimiento.

        Solo un OPERADOR puede ejecutar esta acción.
        Válido desde ABIERTO, REABIERTO (primera asignación)
        o desde ASIGNADO, EN_PROGRESO (reasignación por operador).

        Retorna el evento de auditoría generado.
        """
        if rol_actor != RolUsuario.OPERADOR:
            raise OperacionNoAutorizada(
                "Solo un operador puede asignar o reasignar técnicos."
            )

        estados_permitidos = {
            EstadoRequerimiento.ABIERTO,
            EstadoRequerimiento.REABIERTO,
            EstadoRequerimiento.ASIGNADO,
            EstadoRequerimiento.EN_PROGRESO,
        }
        if self._estado not in estados_permitidos:
            raise TransicionEstadoInvalida(
                f"No se puede asignar técnico en estado {self._estado.value}."
            )

        if self._tecnico_asignado_id == tecnico_id:
            raise RequerimientoError(
                "El técnico indicado ya es el técnico asignado."
            )

        es_reasignacion = self._tecnico_asignado_id is not None
        tecnico_anterior = self._tecnico_asignado_id

        self._tecnico_asignado_id = tecnico_id
        self._operador_id = actor_id
        self._estado = EstadoRequerimiento.ASIGNADO

        if es_reasignacion:
            return self._registrar_evento(
                TipoEvento.REASIGNACION,
                actor_id,
                f"Reasignado de técnico {tecnico_anterior} a {tecnico_id}",
            )
        return self._registrar_evento(
            TipoEvento.ASIGNACION,
            actor_id,
            f"Técnico {tecnico_id} asignado",
        )

    def iniciar_trabajo(self, tecnico_id: str) -> Evento:
        """El técnico asignado comienza a trabajar en el requerimiento.

        Solo válido desde ASIGNADO y solo por el técnico asignado.
        """
        self._validar_transicion(EstadoRequerimiento.EN_PROGRESO)

        if self._tecnico_asignado_id != tecnico_id:
            raise OperacionNoAutorizada(
                "Solo el técnico asignado puede iniciar el trabajo."
            )

        self._estado = EstadoRequerimiento.EN_PROGRESO
        return self._registrar_evento(
            TipoEvento.INICIO_TRABAJO,
            tecnico_id,
            "Trabajo iniciado",
        )

    def resolver(self, tecnico_id: str) -> Evento:
        """Marca el requerimiento como resuelto.

        Solo válido desde EN_PROGRESO y solo por el técnico asignado.
        """
        self._validar_transicion(EstadoRequerimiento.RESUELTO)

        if self._tecnico_asignado_id != tecnico_id:
            raise OperacionNoAutorizada(
                "Solo el técnico asignado puede resolver el requerimiento."
            )

        self._estado = EstadoRequerimiento.RESUELTO
        return self._registrar_evento(
            TipoEvento.RESOLUCION,
            tecnico_id,
            "Requerimiento resuelto",
        )

    def derivar(
        self, tecnico_origen_id: str, tecnico_destino_id: str, motivo: str
    ) -> Evento:
        """Deriva el requerimiento a otro técnico (interconsulta).

        Solo el técnico actualmente asignado puede derivar.
        Válido desde ASIGNADO o EN_PROGRESO.
        El estado vuelve a ASIGNADO para que el nuevo técnico inicie su ciclo.
        """
        if not motivo or not motivo.strip():
            raise RequerimientoError(
                "El motivo de la derivación no puede estar vacío."
            )

        if self._estado not in (
            EstadoRequerimiento.ASIGNADO,
            EstadoRequerimiento.EN_PROGRESO,
        ):
            raise TransicionEstadoInvalida(
                f"No se puede derivar en estado {self._estado.value}."
            )

        if self._tecnico_asignado_id != tecnico_origen_id:
            raise OperacionNoAutorizada(
                "Solo el técnico asignado puede derivar el requerimiento."
            )

        if tecnico_origen_id == tecnico_destino_id:
            raise RequerimientoError(
                "No se puede derivar al mismo técnico."
            )

        self._tecnico_asignado_id = tecnico_destino_id
        self._estado = EstadoRequerimiento.ASIGNADO
        return self._registrar_evento(
            TipoEvento.DERIVACION,
            tecnico_origen_id,
            f"Derivado de {tecnico_origen_id} a {tecnico_destino_id}. "
            f"Motivo: {motivo}",
        )

    def agregar_comentario(
        self, autor_id: str, rol_autor: RolUsuario, contenido: str
    ) -> Comentario:
        """Agrega un comentario al requerimiento.

        Validaciones de permiso:
        - Un solicitante solo puede comentar su propio requerimiento.
        - Un técnico solo puede comentar si es el técnico asignado.
        - Un supervisor no participa directamente en la resolución.
        - Un operador puede comentar cualquier requerimiento.

        Regla de reapertura: si el requerimiento está RESUELTO y el autor
        es operador o técnico, se reabre automáticamente (estado → REABIERTO)
        y se limpia el técnico asignado para forzar nueva asignación.

        Un comentario de solicitante sobre un requerimiento resuelto
        NO provoca reapertura.

        Retorna el comentario creado.
        """
        # ── Validaciones de permiso ──
        if rol_autor == RolUsuario.SUPERVISOR:
            raise OperacionNoAutorizada(
                "El supervisor no puede comentar requerimientos directamente."
            )

        if rol_autor == RolUsuario.SOLICITANTE and autor_id != self._solicitante_id:
            raise OperacionNoAutorizada(
                "Un solicitante solo puede comentar sus propios requerimientos."
            )

        if rol_autor == RolUsuario.TECNICO and autor_id != self._tecnico_asignado_id:
            raise OperacionNoAutorizada(
                "Un técnico solo puede comentar requerimientos asignados a él."
            )

        # ── Crear comentario ──
        comentario = Comentario(
            autor_id=autor_id,
            rol_autor=rol_autor,
            contenido=contenido,
        )
        self._comentarios.append(comentario)

        self._registrar_evento(
            TipoEvento.COMENTARIO,
            autor_id,
            f"Comentario agregado por {rol_autor.value}",
        )

        # ── Reapertura automática ──
        if self._estado == EstadoRequerimiento.RESUELTO and rol_autor in (
            RolUsuario.OPERADOR,
            RolUsuario.TECNICO,
        ):
            self._estado = EstadoRequerimiento.REABIERTO
            self._tecnico_asignado_id = None
            self._registrar_evento(
                TipoEvento.REAPERTURA,
                autor_id,
                "Requerimiento reabierto por comentario",
            )

        return comentario

    # ── Identidad ──

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Requerimiento):
            return NotImplemented
        return self._id == other._id

    def __hash__(self) -> int:
        return hash(self._id)

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}(id={self._id!r}, "
            f"estado={self._estado.value}, tipo={self.tipo.value})"
        )


# ═══════════════════════════════════════════════════════════
#  SUBCLASES CONCRETAS
# ═══════════════════════════════════════════════════════════


class Incidente(Requerimiento):
    """Requerimiento de tipo incidente.  Siempre tiene urgencia."""

    def __init__(
        self,
        titulo: str,
        descripcion: str,
        solicitante_id: str,
        urgencia: Urgencia,
        categoria: CategoriaIncidente,
        **kwargs,
    ) -> None:
        # Atributos propios ANTES de super().__init__ porque
        # _detalle_creacion() los necesita durante la inicialización.
        self._urgencia = urgencia
        self._categoria_incidente = categoria
        super().__init__(titulo, descripcion, solicitante_id, **kwargs)

    @property
    def tipo(self) -> TipoRequerimiento:
        return TipoRequerimiento.INCIDENTE

    @property
    def urgencia(self) -> Urgencia:
        return self._urgencia

    @property
    def categoria(self) -> CategoriaIncidente:
        return self._categoria_incidente

    def _detalle_creacion(self) -> str:
        return (
            f"Incidente creado — urgencia: {self._urgencia.value}, "
            f"categoría: {self._categoria_incidente.value}"
        )


class Solicitud(Requerimiento):
    """Requerimiento de tipo solicitud.  No tiene urgencia."""

    def __init__(
        self,
        titulo: str,
        descripcion: str,
        solicitante_id: str,
        categoria: CategoriaSolicitud,
        **kwargs,
    ) -> None:
        # Atributo propio ANTES de super().__init__ porque
        # _detalle_creacion() lo necesita durante la inicialización.
        self._categoria_solicitud = categoria
        super().__init__(titulo, descripcion, solicitante_id, **kwargs)

    @property
    def tipo(self) -> TipoRequerimiento:
        return TipoRequerimiento.SOLICITUD

    @property
    def categoria(self) -> CategoriaSolicitud:
        return self._categoria_solicitud

    def _detalle_creacion(self) -> str:
        return f"Solicitud creada — categoría: {self._categoria_solicitud.value}"


# ═══════════════════════════════════════════════════════════
#  FACTORY
# ═══════════════════════════════════════════════════════════


class RequerimientoFactory:
    """Factory Method para crear requerimientos.

    Encapsula la lógica de inicialización garantizando que:
    - Todo incidente tiene urgencia.
    - Toda solicitud NO tiene urgencia.
    - Se genera automáticamente el evento de CREACION (en __init__).
    - El estado inicial siempre es ABIERTO.
    """

    @staticmethod
    def crear_incidente(
        titulo: str,
        descripcion: str,
        solicitante_id: str,
        urgencia: Urgencia,
        categoria: CategoriaIncidente,
    ) -> Incidente:
        """Crea un incidente con su evento de creación."""
        return Incidente(
            titulo=titulo,
            descripcion=descripcion,
            solicitante_id=solicitante_id,
            urgencia=urgencia,
            categoria=categoria,
        )

    @staticmethod
    def crear_solicitud(
        titulo: str,
        descripcion: str,
        solicitante_id: str,
        categoria: CategoriaSolicitud,
    ) -> Solicitud:
        """Crea una solicitud con su evento de creación."""
        return Solicitud(
            titulo=titulo,
            descripcion=descripcion,
            solicitante_id=solicitante_id,
            categoria=categoria,
        )
