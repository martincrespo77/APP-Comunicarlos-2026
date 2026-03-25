"""Lógica pura de autenticación JWT.

Este módulo NO importa FastAPI ni app.deps para evitar dependencias circulares.
Solo contiene la creación y verificación de tokens JWT.

Decisiones de diseño:
  - SECRET_KEY se lee de la variable de entorno ``SECRET_KEY``.
    Si no está configurada se usa un fallback de desarrollo con advertencia
    explícita: nunca silenciosa, siempre visible.
  - Claims mínimos: sub (usuario_id), rol, iat, exp.
    No se incluyen nombre, email ni password_hash en el token.
  - ALGORITHM HS256: simétrico, adecuado para un único servicio.
    Si en el futuro se expone una API pública multi-servicio
    migrar a RS256 con par de claves.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt

from app.compartido.dominio import RolUsuario
from app.config import get_settings

# ──────────────────────────────────────────────────────────────────────────────
#  Configuración (leída de app.config para centralizar todas las variables)
# ──────────────────────────────────────────────────────────────────────────────

# Las variables se exponen como módulo-nivel para compatibilidad con imports
# existentes en tests y en el propio módulo.
_cfg = get_settings()
SECRET_KEY: str = _cfg.SECRET_KEY
ALGORITHM: str = _cfg.ALGORITHM
EXPIRACION_MINUTOS: int = _cfg.EXPIRACION_MINUTOS


# ──────────────────────────────────────────────────────────────────────────────
#  Excepción
# ──────────────────────────────────────────────────────────────────────────────


class TokenError(Exception):
    """Token inválido, expirado o con claims obligatorios ausentes."""


# ──────────────────────────────────────────────────────────────────────────────
#  Crear token
# ──────────────────────────────────────────────────────────────────────────────


def crear_token(usuario_id: str, rol: RolUsuario) -> str:
    """Crea un JWT firmado con claims mínimos (sub, rol, iat, exp)."""
    ahora = datetime.now(timezone.utc)
    payload: dict = {
        "sub": usuario_id,
        "rol": rol.value,
        "iat": ahora,
        "exp": ahora + timedelta(minutes=EXPIRACION_MINUTOS),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


# ──────────────────────────────────────────────────────────────────────────────
#  Decodificar token
# ──────────────────────────────────────────────────────────────────────────────


def decodificar_token(token: str) -> dict:
    """Decodifica y verifica la firma y expiración de un JWT.

    Returns
    -------
    dict
        Payload del token con al menos ``sub`` y ``rol``.

    Raises
    ------
    TokenError
        Si la firma es inválida, el token está expirado, o faltan
        los claims obligatorios ``sub`` / ``rol``.
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError as exc:
        raise TokenError(str(exc)) from exc

    if "sub" not in payload or "rol" not in payload:
        raise TokenError("Claims obligatorios ausentes en el token: sub, rol.")

    return payload
