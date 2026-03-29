"""Configuración de pytest a nivel de proyecto.

Se ejecuta ANTES de que pytest importe cualquier módulo de la aplicación,
lo que permite fijar variables de entorno necesarias para tests sin
afectar la lógica de producción.

- SECRET_KEY: evita el RuntimeWarning de clave de desarrollo insegura.
- MONGODB_URL / MONGODB_DB_NAME: valores por defecto para tests.
  Los tests de routers y servicios usan dependency_overrides y fakes,
  por lo que no tocan MongoDB.  Solo aplican a tests de infraestructura
  que usan mongomock.
"""

import os

os.environ.setdefault("SECRET_KEY", "test-only-key-not-for-production-use-in-ci")
os.environ.setdefault("MONGODB_URL", "mongodb://localhost:27017")
os.environ.setdefault("MONGODB_DB_NAME", "mesa_de_ayuda_test")
