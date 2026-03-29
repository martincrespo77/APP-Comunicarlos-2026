# Control y Trazabilidad

## 1. Objetivo de la fase
Documentar el progreso ordenado del proyecto, asegurar que no haya regresiones técnicas al avanzar de capas y mantener un registro de las validaciones clave.

## 2. Mapa y Matriz de Trazabilidad
Diseñamos el avance de adentro hacia afuera (Dominio -> Infraestructura), asegurando cada paso con testing automático.

| Fase | Objetivo | Archivos Tocados Principales | Tests Asociados | Resultado | Estado |
|---|---|---|---|---|---|
| 03 | Dominio Puro | `app/requerimientos/dominio.py`, `app/usuarios/dominio.py`, `app/compartido/dominio.py` | `test_requerimientos_dominio.py`, `test_usuarios_dominio.py` | Entidades inmutables, sin Pydantic | ✅ Completado |
| 04 | Auditoría Tests | `tests/test_*_dominio.py` | Todos los de dominio | 150+ tests core blindando reglas de negocio | ✅ Completado |
| 05 | Repositorios | `app/*/repositorio.py` | N/A (Interfaces) | Contratos definidos con `ABC` | ✅ Completado |
| 06 | Servicios | `app/*/servicios.py` | `test_requerimientos_servicios.py`, `test_usuarios_servicios.py` | Orquestación correcta mediante inyección de fakes | ✅ Completado |
| 07 | Schemas | `app/*/schemas.py` | `test_*_schemas.py` | DTOs de Pydantic v2 aislados del dominio | ✅ Completado |
| 08 | Routers | `app/*/router.py` | `test_*_router.py` | Endpoints HTTP con `Depends()` | ✅ Completado |
| 09 | Auth | `app/auth.py` | `test_auth.py` | Seguridad JWT por rol implementada | ✅ Completado |
| 10 | Infra & Persist. | `app/infraestructura/`, `main.py`, `config.py` | `test_infraestructura.py`, Tests de integración HTTP | Base relacional mapeada, HTTP200s en toda la API | ✅ Completado |
| 11 | Docker | `Dockerfile`, `docker-compose.yml`, `.env.example` | N/A | Contenedor levantando correctamente en puerto 8000 | ✅ Completado |
| 12 | Bruno | `bruno/*` | Pruebas manuales/semi-automáticas en UI | 57 Requests cubriendo flujos completos | ✅ Completado |

## 3. Decisiones tomadas
- **Zero Regressions:** Ninguna fase pasaba a "Completado" sin que la suite global de `pytest` diera un 100% de pases en verde.
- **TDD Parcial:** Los tests de dominio se consolidaban *después* de definir la primera interfaz del modelo, pero *antes* de saltar a la infraestructura.

## 4. Problemas detectados
- Al avanzar hacia la Fase 10 (Infraestructura), algunas funciones de los routers fallaban porque los mapeos (DTO a Dominio) requerían campos (como `id` o fecha) que la base de datos inyectaba tarde.
- Cierto acoplamiento temporal en los tests de integración causados por el reuso del mismo estado de base en memoria.

## 5. Correcciones aplicadas
- Se ajustaron las entidades del dominio para soportar identificadores nulos en memoria (antes de guardarse) y asignaciones posteriores por la capa de persistencia, sin perder pureza matemática.
- Se usó el patrón Fixture de `pytest` (en `conftest.py`) para generar un entorno de base de datos fresco para cada test HTTP.

## 6. Cómo se validó
- Integración continua local: Ejecución constante de `pytest` y `pytest --cov`.
- Control manual de imports (chequear visualmente que ningún archivo en `app/*/dominio.py` importa `pymongo`, `pydantic` o `fastapi`).

## 7. Resultado de la fase
El proyecto finalizó con 394 tests pasando impecablemente en 13 archivos distintos, entregando un MVP (Minimum Viable Product) hiper-confiable.

## 8. Lecciones aprendidas
- La matriz de trazabilidad obliga a no saltearse pasos aburridos (como aislar los tests de DTOs antes de enchufar la base de datos).
- Escribir pruebas unitarias temprano hizo que la conexión de FastAPI con la capa de persistencia fluyera sin casi bugs en tiempo de ejecución de la capa web.

## 9. Estado de cierre
Historial de trazabilidad cerrado y exitoso. Todas las fases cubiertas y funcionales.
