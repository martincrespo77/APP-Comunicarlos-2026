# APP Comunicarlos 2026

Repositorio del proyecto de Mesa de Ayuda de la Cooperativa Comunicarlos (Práctica Profesional 5).

## Estado de la Versión Actual
Esta versión inicial contiene la implementación completa y aislada del **Núcleo del Dominio** bajo principios de *Domain-Driven Design (DDD)* y Programación Orientada a Objetos pura en Python.

### Qué está implementado (Fase 1 completada)
- **Modelado de Dominio Puro**: No hay dependencias de bases de datos, ORMs (SQLAlchemy), frameworks web (FastAPI) ni librerías de validación (Pydantic). Las reglas de negocio están contenidas 100% en clases Python puras.
- **Entidades y Agregados**: 
  - `Requerimiento` (Aggregate Root) con subclases `Incidente` y `Solicitud`.
  - Entidad `Usuario`.
- **Value Objects**: Objetos inmutables como `Comentario` y `Evento`.
- **Shared Kernel**: Módulo `compartido` para compartir dependencias de dominio inter-módulos (Ej: `RolUsuario`).
- **Control Estricto de Invariantes**: Validaciones de transiciones de estado, permisos por roles de usuario, auditoría interna (`eventos_dominio`).
- **Testing Exhaustivo**: Suite de pruebas unitarias implementada puramente con `pytest`, cubriendo exitosamente la totalidad de las lógicas transicionales y excepciones personalizadas del dominio.

### Qué falta terminar y próximos pasos (Fase 2 y 3)
Aún no es una aplicación funcional interactable; es el "cerebro" del negocio. Los próximos pasos arquitectónicos son:

1. **Definir Puertos de Repositorio (Interfaces)**: Crear abstracciones para persistencia (Ej. `RequerimientoRepository`).
2. **Definir DTOs (Data Transfer Objects)**: Introducir `Pydantic` *estrictamente fuera del dominio* para validar el ingreso y salida de datos de la API.
3. **Desarrollar la Capa de Aplicación (Services / Use Cases)**: Orquestadores que reciben DTOs, validan con REPO, invocan reglas de la ENTIDAD y emiten eventos a NOTIFICACIONES.
4. **Implementar Adapters (Infraestructura / Routers)**: 
   - Base de datos (SQLAlchemy).
   - Servidor HTTP Web API (FastAPI).

## Configuración para Desarrollo Local
1. Instalar dependencias con `uv` o en un entorno virtual clásico.
   ```bash
   uv sync
   ```
2. Correr la suite de pruebas del dominio:
   ```bash
   pytest tests/ -v
   ```
