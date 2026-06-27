# Arquitectura

## Organización: DDD Modular (Bounded Contexts)

El proyecto sigue una arquitectura **Domain-Driven Design modular**, donde cada módulo de negocio encapsula su propia estructura de capas:

```
app/
├── compartido/         ← Shared Kernel (tipos compartidos)
├── usuarios/           ← Bounded Context: Usuarios
│   ├── dominio.py      (entidad Usuario)
│   ├── servicios.py    (casos de uso)
│   ├── repositorio.py  (ABC)
│   ├── router.py       (endpoints HTTP)
│   ├── schemas.py      (DTOs Pydantic)
│   └── excepciones.py
├── requerimientos/     ← Bounded Context: Requerimientos
│   ├── dominio.py      (Requerimiento, Incidente, Solicitud, VOs)
│   ├── servicios.py    (casos de uso)
│   ├── repositorio.py  (ABC)
│   ├── router.py       (endpoints HTTP)
│   ├── schemas.py      (DTOs Pydantic)
│   └── excepciones.py
├── notificaciones/     ← Observer Pattern
│   └── dominio.py      (DespachadorEventos, ObservadorRequerimiento)
├── infraestructura/    ← Implementaciones concretas
│   ├── database.py     (conexión MongoDB)
│   ├── repo_usuarios.py
│   └── repo_requerimientos.py
├── auth.py             ← JWT (crear / verificar tokens)
├── config.py           ← Settings centralizadas (pydantic-settings)
└── deps.py             ← Inyección de dependencias FastAPI
```

## Principios aplicados

- **Inversión de dependencias**: los servicios dependen de ABCs (repositorios abstractos), no de MongoDB.
- **Shared Kernel mínimo**: solo `RolUsuario` es compartido entre bounded contexts.
- **Separación de capas**: dominio puro → servicios → DTOs → HTTP.
- **Encapsulamiento**: atributos privados con `_` y propiedades de solo lectura.

## Patrones de diseño

| Patrón | Implementación |
|--------|---------------|
| **Observer** | `DespachadorEventos` + `ObservadorRequerimiento` |
| **Factory** | `RequerimientoFactory` (método estático) |
| **Repository** | ABCs + implementaciones MongoDB |
| **DTO** | Schemas Pydantic (`*In` / `*Out`) |
| **Dependency Injection** | `Depends()` de FastAPI en `deps.py` |
