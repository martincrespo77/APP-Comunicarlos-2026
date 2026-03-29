"""Paquete de infraestructura concreta.

Contiene las implementaciones MongoDB de los repositorios y la configuración
de conexión a la base de datos.

Módulos:
  - database.py            → conexión MongoClient, init de índices
  - repo_usuarios.py       → RepositorioUsuarioMongo
  - repo_requerimientos.py → RepositorioRequerimientoMongo

Regla de dependencias (invariante):
  Este paquete puede importar desde ``app.usuarios.*``, ``app.requerimientos.*``
  y ``app.config``, pero NUNCA al revés.
  El dominio y los servicios no conocen este paquete.
"""
