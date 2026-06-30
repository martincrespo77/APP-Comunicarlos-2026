# Diagnóstico del Estado del Proyecto (PP5)

## 1. Resumen Ejecutivo del Estado Actual
El repositorio se encuentra en un estado **excelente** en cuanto a pureza arquitectónica del **Core/Dominio**. Se ha completado con éxito la transición hacia un modelo Orientado a Objetos puro siguiendo principios de *Domain-Driven Design (DDD)*. El código no presenta dependencias de frameworks externos, bases de datos ni HTTP en sus entidades y value objects. Existe una suite de testing unitario extensa y focalizada explícitamente en el dominio.

## 2. Estructura Detectada del Proyecto
El proyecto está estructurado de manera modular y limpia en dos ramas principales:
- `app/` (Código fuente)
  - `compartido/dominio.py`: Shared Kernel, con `RolUsuario`.
  - `notificaciones/dominio.py`: Entidades/Value Objects de notificaciones.
  - `requerimientos/`: Contiene el agregado principal (`dominio.py`) y sus excepciones personalizadas (`excepciones.py`).
  - `usuarios/dominio.py`: Entidad `Usuario`.
- `tests/` (Suite de Testing)
  - Tests unitarios separados espejando fielmente la estructura del dominio (`test_requerimientos_dominio.py`, `test_usuarios_dominio.py`, etc.).
- `pyproject.toml` y `uv.lock`: Configuración limpia, usando `pytest` sin contaminación de librerías extras todavía.

## 3. Qué ya está bien resuelto
- **Pureza del Dominio**: Se abandonó `Pydantic` en el dominio. Las entidades y Value Objects (como `Comentario` o `Evento`) son objetos Python puros (`@property`, inmutabilidad estricta, encapsulamiento).
- **Control de Invariantes**: Las validaciones complejas de negocio (transiciones de estado, permisos por rol, reglas de reasignación) ocurren en la raíz del agregado (`Requerimiento`).
- **Patrón Open/Closed**: Uso correcto de clases base abstractas (`Requerimiento`) y polimorfismo (`Incidente`, `Solicitud`) junto con `RequerimientoFactory`.
- **Eventos de Dominio**: El agregado registra sus propios eventos `_eventos_dominio` listos para ser despachados por capa de aplicación o servicios. No hay side-effects (envío de mails real) dentro de la entidad, lo cual es de manual DDD.

## 4. Qué problemas o inconsistencias detectaste
No hay errores graves, pero se detectan posibles señales de **deuda técnica por volumen**:
- El archivo `test_requerimientos_dominio.py` es excesivamente grande (aprox. 45 KB). Esto significa que concentra demasiadas responsabilidades en un solo archivo.
- **Sugerencia**: Debería dividirse en el futuro cercano (e.g., `test_requerimientos_estados.py`, `test_requerimientos_comentarios.py`, `test_requerimientos_factory.py`).
- **Falta de DTOs en capa superior**: Dado que el dominio no usa Pydantic, habrá que tener especial cuidado en crear DTOs de entrada/salida precisos cuando se empiece la capa de servicios.

## 5. Qué fase del proyecto considerás cerrada
- **Modelado de dominio**: Completado. Las entidades, relaciones lógicas y reglas de negocio están definidas y codificadas.
- **Refactor del dominio**: Completado. La extirpación de Pydantic/frameworks fue exitosa.

## 6. Qué fase está actualmente en curso
- **Testing unitario del dominio**: Técnicamente se encuentra en la etapa de cierre o auditoría final. La cobertura explícita de cada regla de negocio y excepción de requerimientos parece estar implementada en su totalidad.

## 7. Qué fase debería continuar ahora y por qué
Debe continuar la **Preparación para Service / Repository / Router**.
**Por qué**: El dominio ya no puede seguir creciendo en el vacío. Para que el caso de uso funcione realmente, se necesita orquestar los objetos puros del dominio: buscarlos de una persistencia, enviarle comandos, recolectar sus eventos de dominio y guardarlos, así como también despachar notificaciones.

## 8. Lista priorizada de próximos pasos
1. **Definir Puertos de Repositorio (Interfaces)**: Crear `app/requerimientos/repositorio.py` (o similar) definiendo clases abstractas `class RequerimientoRepository(ABC)`.
2. **Definir DTOs (Data Transfer Objects)**: Crear esquemas `Pydantic` *estrictamente fuera del dominio* para validar el ingreso/salida de datos de los casos de uso.
3. **Desarrollar la Capa de Aplicación (Services / Use Cases)**: Orquestadores que reciben DTOs, validan con REPO, invocan a la ENTIDAD y envían eventos a NOTIFICACIONES.
4. **Testing de Servicios con Repos In-Memory**: Testear la lógica de aplicación inyectando "Fakes" sin conectar DB real todavía.
5. **Implementar Adapters (Infraestructura / Routers)**: FastAPI y base de datos (SQLAlchemy).

## 9. Riesgos si se avanza sin corregir ciertos puntos
- Si se salta directamente a la infraestructura sin definir la capa de Servicios y Repositorios como intermediarios, se corre el riesgo **altísimo** de volver a acoplar Pydantic, HTTP o SQLAlchemy dentro del código puro del dominio, tirando a la basura el esfuerzo del refactor.
- El monolito de testing de `test_requerimientos_dominio.py` puede volverse inmanejable ante el mínimo cambio de negocio afectando la productividad.

## 10. Recomendación de modelo de IA para el siguiente paso
**Claude Sonnet 4.6 (Thinking) / Claude 3.7 Sonnet (Thinking)**
- **Justificación**: La próxima fase implica "Arquitectura", "Diseño de Interfaces (Ports and Adapters)" e "Inversión de Dependencias" (Dependency Injection). Estos temas arquitectónicos se benefician enormemente de modelos con capacidades avanzadas de "Reasoning" o "Thinking". Claude Sonnet en modo Thinking es excepcional planificando interfaces de repositorios que respeten invariantes estrictas del DDD y orquestando lógica de aplicación sin caer en soluciones perezosas acopladas a base de datos.
