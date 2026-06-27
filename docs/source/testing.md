# Testing

## Estrategia

Los tests cubren **todas las capas** de la aplicación:

| Capa | Archivos | Qué se testea |
|------|----------|---------------|
| Dominio | `test_requerimientos_dominio`, `test_usuarios_dominio`, `test_compartido_dominio` | Invariantes de negocio, transiciones, validaciones |
| Servicios | `test_requerimientos_servicios`, `test_usuarios_servicios` | Casos de uso con repositorios mockeados |
| Schemas | `test_requerimientos_schemas`, `test_usuarios_schemas` | Serialización/deserialización DTOs |
| Routers | `test_requerimientos_router`, `test_usuarios_router` | Endpoints HTTP con TestClient |
| Auth | `test_auth` | Creación y verificación de JWT |
| Notificaciones | `test_notificaciones_dominio` | Observer/DespachadorEventos |
| Excepciones | `test_requerimientos_excepciones` | Jerarquía de errores |
| Infraestructura | `test_infraestructura` | Repos MongoDB con mongomock |

## Ejecución

```bash
# Todos los tests
pytest

# Con cobertura
pytest --cov=app

# Solo dominio
pytest tests/test_*_dominio.py -v
```

## Principios

- **Sin I/O**: los tests de dominio y servicios no tocan base de datos ni red.
- **Inyección de fakes**: los servicios reciben repositorios in-memory triviales.
- **mongomock**: los tests de infraestructura usan mongomock como reemplazo de MongoDB.
