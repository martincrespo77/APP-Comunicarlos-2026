"""Configuración de pytest a nivel de proyecto.

Se ejecuta ANTES de que pytest importe cualquier módulo de la aplicación,
lo que permite fijar variables de entorno necesarias para tests sin
afectar la lógica de producción.

- SECRET_KEY: evita el RuntimeWarning de clave de desarrollo insegura.
- DATABASE_URL: apunta a SQLite en archivo temporal para tests de integración.
  Los tests de routers y servicios usan dependency_overrides y nunca tocan
  esta base de datos, por lo que el valor es indiferente para ellos.
"""

import os

os.environ.setdefault("SECRET_KEY", "test-only-key-not-for-production-use-in-ci")
# SQLite en memoria: sin archivo en disco, sin residuos tras tests fallidos.
# Los tests de routers usan dependency_overrides y nunca llaman get_db(),
# por lo que este valor solo aplica a tests de infraestructura que crean
# su propio engine (también con :memory:) — este setdefault queda como
# fallback de último recurso si algún test futuro usa el engine de app.
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
