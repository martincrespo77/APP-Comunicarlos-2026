# Diagrama de Clases - Capa de Aplicación

Este diagrama modela detalladamente la capa de aplicación, abarcando los **Servicios de Aplicación** (casos de uso), los **Puertos / Interfaces de Repositorios** de los que dependen, y los **Schemas (DTOs)** utilizados para la entrada y salida de datos del sistema.

```mermaid
classDiagram
    direction TB

    %% NAMESPACE: USUARIOS
    namespace app_usuarios {
        class UsuarioService {
            <<service>>
            -_repo RepositorioUsuario
            -_hasher Callable
            -_verificador Callable
            +registrar(nombre: str, email: str, rol: RolUsuario, password_plano: str) str
            +autenticar(email: str, password_plano: str) Usuario
            +obtener(usuario_id: str) Usuario
            +listar(skip: int, limit: int) list~Usuario~
            +desactivar(usuario_id: str) void
        }

        class RepositorioUsuario {
            <<interface>>
            +guardar(usuario: Usuario)* void
            +obtener_por_id(usuario_id: str)* Usuario
            +obtener_por_email(email: str)* Usuario
            +listar(skip: int, limit: int)* list~Usuario~
        }

        class UsuarioCrearIn {
            <<dto>>
            +nombre str
            +email EmailStr
            +rol RolUsuario
            +password str
        }

        class UsuarioAutenticarIn {
            <<dto>>
            +email EmailStr
            +password str
        }

        class UsuarioOut {
            <<dto>>
            +id str
            +nombre str
            +email str
            +rol RolUsuario
            +activo bool
            +fecha_creacion datetime
            +ultimo_acceso datetime
            +desde_entidad(usuario: Usuario)$ UsuarioOut
        }

        class TokenOut {
            <<dto>>
            +access_token str
            +token_type str
        }
    }

    %% NAMESPACE: REQUERIMIENTOS
    namespace app_requerimientos {
        class RequerimientoService {
            <<service>>
            -_repo RepositorioRequerimiento
            -_despachador DespachadorEventos
            -_obtener_o_fallar(requerimiento_id: str) Requerimiento
            -_guardar_y_despachar(requerimiento: Requerimiento) void
            +crear_incidente(titulo: str, descripcion: str, solicitante_id: str, urgencia: Urgencia, categoria: CategoriaIncidente) str
            +crear_solicitud(titulo: str, descripcion: str, solicitante_id: str, categoria: CategoriaSolicitud) str
            +asignar_tecnico(requerimiento_id: str, tecnico_id: str, actor_id: str, rol_actor: RolUsuario) void
            +iniciar_trabajo(requerimiento_id: str, tecnico_id: str) void
            +resolver(requerimiento_id: str, tecnico_id: str) void
            +derivar(requerimiento_id: str, tecnico_origen_id: str, tecnico_destino_id: str, motivo: str) void
            +agregar_comentario(requerimiento_id: str, autor_id: str, rol_autor: RolUsuario, contenido: str) void
            +obtener(requerimiento_id: str) Requerimiento
            +listar(skip: int, limit: int) list~Requerimiento~
            +listar_por_solicitante(solicitante_id: str, skip: int, limit: int) list~Requerimiento~
            +listar_por_tecnico(tecnico_id: str, skip: int, limit: int) list~Requerimiento~
            +listar_por_estado(estado: EstadoRequerimiento, skip: int, limit: int) list~Requerimiento~
        }

        class RepositorioRequerimiento {
            <<interface>>
            +guardar(requerimiento: Requerimiento)* void
            +obtener_por_id(requerimiento_id: str)* Requerimiento
            +listar(skip: int, limit: int)* list~Requerimiento~
            +listar_por_solicitante(solicitante_id: str, skip: int, limit: int)* list~Requerimiento~
            +listar_por_tecnico(tecnico_id: str, skip: int, limit: int)* list~Requerimiento~
            +listar_por_estado(estado: EstadoRequerimiento, skip: int, limit: int)* list~Requerimiento~
        }

        class IncidenteCrearIn {
            <<dto>>
            +titulo str
            +descripcion str
            +solicitante_id str
            +urgencia Urgencia
            +categoria CategoriaIncidente
        }

        class SolicitudCrearIn {
            <<dto>>
            +titulo str
            +descripcion str
            +solicitante_id str
            +categoria CategoriaSolicitud
        }

        class AsignarTecnicoIn {
            <<dto>>
            +tecnico_id str
        }

        class DerivarRequerimientoIn {
            <<dto>>
            +tecnico_destino_id str
            +motivo str
        }

        class ComentarioAgregarIn {
            <<dto>>
            +contenido str
        }

        class EventoOut {
            <<dto>>
            +id str
            +tipo TipoEvento
            +actor_id str
            +detalle str
            +fecha datetime
            +desde_entidad(evento: Evento)$ EventoOut
        }

        class ComentarioOut {
            <<dto>>
            +id str
            +autor_id str
            +rol_autor RolUsuario
            +contenido str
            +fecha datetime
            +desde_entidad(comentario: Comentario)$ ComentarioOut
        }

        class RequerimientoOut {
            <<dto>>
            +id str
            +titulo str
            +descripcion str
            +tipo TipoRequerimiento
            +estado EstadoRequerimiento
            +solicitante_id str
            +operador_id str
            +tecnico_asignado_id str
            +fecha_creacion datetime
            +fecha_actualizacion datetime
            +urgencia Urgencia
            +categoria_incidente CategoriaIncidente
            +categoria_solicitud CategoriaSolicitud
            +comentarios list~ComentarioOut~
            +eventos list~EventoOut~
            +desde_entidad(req: Requerimiento)$ RequerimientoOut
        }
    }

    %% Dependencias Usuarios
    UsuarioService ..> RepositorioUsuario : usa
    UsuarioService ..> UsuarioCrearIn : consume
    UsuarioService ..> UsuarioAutenticarIn : consume

    %% Dependencias Requerimientos
    RequerimientoService ..> RepositorioRequerimiento : usa
    RequerimientoService ..> IncidenteCrearIn : consume
    RequerimientoService ..> SolicitudCrearIn : consume
    RequerimientoService ..> AsignarTecnicoIn : consume
    RequerimientoService ..> DerivarRequerimientoIn : consume
    RequerimientoService ..> ComentarioAgregarIn : consume

    RequerimientoOut "1" *-- "*" ComentarioOut
    RequerimientoOut "1" *-- "*" EventoOut
```
