"""Paquete de infraestructura concreta.

Contiene:
  - database.py       → engine SQLAlchemy, Base ORM, init_db
  - modelos_orm.py    → tablas ORM (sin lógica de negocio)
  - repo_usuarios.py  → implementación SQL de RepositorioUsuario
  - repo_requerimientos.py → implementación SQL de RepositorioRequerimiento

Regla de dependencias:
  Este paquete puede importar desde ``app.usuarios.*``, ``app.requerimientos.*``
  y ``app.config``, pero NUNCA al revés.
  El dominio y los servicios no conocen este paquete.
"""
