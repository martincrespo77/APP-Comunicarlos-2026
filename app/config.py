"""Configuración centralizada de la aplicación.

Todas las variables sensibles se leen desde el entorno (o un archivo ``.env``).
Es el único módulo que conoce los nombres de las variables de entorno.

Uso:
    from app.config import get_settings
    settings = get_settings()
    print(settings.MONGODB_URL)

Principio:
    Ningún otro módulo debe leer ``os.environ`` directamente para obtener
    configuración de aplicación.  Solo este módulo lo hace.
"""

from __future__ import annotations

import warnings
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict

# ──────────────────────────────────────────────────────────────────────────────
#  Clave de desarrollo (fallback)
# ──────────────────────────────────────────────────────────────────────────────

_FALLBACK_SECRET = "dev-insecure-CAMBIAR-EN-PRODUCCION-9f3a2b"


# ──────────────────────────────────────────────────────────────────────────────
#  Settings
# ──────────────────────────────────────────────────────────────────────────────


class Settings(BaseSettings):
    """Parámetros configurables del sistema.

    Todos los campos pueden sobreescribirse con variables de entorno
    del mismo nombre (case-insensitive) o desde un archivo ``.env``.
    """

    # ── Auth / JWT ──────────────────────────────────────────────────────────
    SECRET_KEY: str = _FALLBACK_SECRET
    """Clave secreta para firmar los JWT.  DEBE cambiarse en producción."""

    ALGORITHM: str = "HS256"
    """Algoritmo de firma JWT.  HS256 es simétrico y adecuado para un único servicio."""

    EXPIRACION_MINUTOS: int = 60
    """Tiempo de expiración del token en minutos."""

    # ── Persistencia — MongoDB ──────────────────────────────────────────────
    MONGODB_URL: str = "mongodb://localhost:27017"
    """URL de conexión a la instancia MongoDB."""

    MONGODB_DB_NAME: str = "mesa_de_ayuda"
    """Nombre de la base de datos MongoDB."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",          # ignorar variables de entorno desconocidas
        case_sensitive=False,    # SECRET_KEY == secret_key en el entorno
    )


# ──────────────────────────────────────────────────────────────────────────────
#  Accessor (singleton por proceso)
# ──────────────────────────────────────────────────────────────────────────────


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Retorna la instancia única de Settings (cacheada).

    Emite ``RuntimeWarning`` si SECRET_KEY tiene el valor de desarrollo
    inseguro, para que sea visible en logs al arrancar el servidor.
    """
    s = Settings()
    if s.SECRET_KEY == _FALLBACK_SECRET:
        warnings.warn(
            "[config] SECRET_KEY no configurada: se usa clave de DESARROLLO insegura. "
            "Configure la variable de entorno SECRET_KEY antes de ir a producción.",
            RuntimeWarning,
            stacklevel=2,
        )
    return s
