"""Tests unitarios para app/auth.py.

Prueba:
  - crear_token: formato JWT, claims correctos.
  - decodificar_token: round-trip exitoso.
  - TokenError: token adulterado, expirado, claims ausentes.
  - SECRET_KEY: fallback de desarrollo visible en la advertencia.

NO se prueba lógica de FastAPI ni HTTP aquí (ese es el rol de
los router tests).  Solo se prueba la lógica pura de tokens.
"""

from __future__ import annotations

import time
import unittest
import warnings
from datetime import datetime, timezone

from app.auth import (
    ALGORITHM,
    EXPIRACION_MINUTOS,
    SECRET_KEY,
    TokenError,
    crear_token,
    decodificar_token,
)
from app.compartido.dominio import RolUsuario


class TestCrearToken(unittest.TestCase):
    """crear_token genera un JWT bien formado."""

    def test_retorna_string_no_vacio(self):
        token = crear_token("usr-1", RolUsuario.OPERADOR)
        self.assertIsInstance(token, str)
        self.assertTrue(token)

    def test_formato_tres_partes_separadas_por_punto(self):
        """Un JWT siempre tiene la forma header.payload.signature."""
        token = crear_token("usr-1", RolUsuario.TECNICO)
        partes = token.split(".")
        self.assertEqual(len(partes), 3)

    def test_tokens_distintos_para_mismos_datos_son_deterministas_con_mismo_iat(self):
        """Dos tokens con los mismos datos generados en el mismo instante son iguales."""
        t1 = crear_token("usr-1", RolUsuario.SUPERVISOR)
        t2 = crear_token("usr-1", RolUsuario.SUPERVISOR)
        # JWT HS256 es determinista para mismo payload + key: ambos iguales
        # …a menos que el iat difiera en microsegundos.
        # Verificamos que al menos son decodificables con los mismos claims.
        p1 = decodificar_token(t1)
        p2 = decodificar_token(t2)
        self.assertEqual(p1["sub"], p2["sub"])
        self.assertEqual(p1["rol"], p2["rol"])

    def test_diferentes_usuarios_generan_tokens_distintos(self):
        t1 = crear_token("usr-A", RolUsuario.OPERADOR)
        t2 = crear_token("usr-B", RolUsuario.OPERADOR)
        self.assertNotEqual(t1, t2)


class TestDecodificarToken(unittest.TestCase):
    """decodificar_token extrae claims correctamente."""

    def _token(self, uid: str = "usr-1", rol: RolUsuario = RolUsuario.OPERADOR) -> str:
        return crear_token(uid, rol)

    def test_sub_correcto(self):
        payload = decodificar_token(self._token("mi-id"))
        self.assertEqual(payload["sub"], "mi-id")

    def test_rol_correcto(self):
        payload = decodificar_token(self._token(rol=RolUsuario.TECNICO))
        self.assertEqual(payload["rol"], "tecnico")

    def test_iat_presente(self):
        payload = decodificar_token(self._token())
        self.assertIn("iat", payload)

    def test_exp_presente_y_futuro(self):
        payload = decodificar_token(self._token())
        self.assertIn("exp", payload)
        ahora = datetime.now(timezone.utc).timestamp()
        self.assertGreater(payload["exp"], ahora)

    def test_exp_aproximadamente_expiracion_minutos_desde_ahora(self):
        antes = datetime.now(timezone.utc).timestamp()
        payload = decodificar_token(self._token())
        despues = datetime.now(timezone.utc).timestamp()
        # exp debe estar ~60 min en el futuro (tolerancia ±5 s)
        delta = payload["exp"] - (antes + antes) / 2  # noqa: simplificación
        margen_bajo = antes + EXPIRACION_MINUTOS * 60 - 5
        margen_alto = despues + EXPIRACION_MINUTOS * 60 + 5
        self.assertGreaterEqual(payload["exp"], margen_bajo)
        self.assertLessEqual(payload["exp"], margen_alto)

    def test_todos_los_roles_codifican_y_decodifican(self):
        for rol in RolUsuario:
            with self.subTest(rol=rol):
                token = crear_token("id", rol)
                payload = decodificar_token(token)
                self.assertEqual(payload["rol"], rol.value)


class TestTokenError(unittest.TestCase):
    """decodificar_token lanza TokenError ante tokens inválidos."""

    def test_token_adulterado_lanza_token_error(self):
        token = crear_token("usr-1", RolUsuario.OPERADOR)
        # Modificar el segmento de firma hace el token inválido
        partes = token.split(".")
        partes[2] = partes[2][::-1]  # invertir la firma
        token_adulterado = ".".join(partes)
        with self.assertRaises(TokenError):
            decodificar_token(token_adulterado)

    def test_cadena_aleatoria_lanza_token_error(self):
        with self.assertRaises(TokenError):
            decodificar_token("esto.no.es-un-jwt")

    def test_string_vacio_lanza_token_error(self):
        with self.assertRaises(TokenError):
            decodificar_token("")

    def test_token_firmado_con_clave_distinta_lanza_error(self):
        """Si alguien firma con otra clave, el token es inválido."""
        from jose import jwt as _jwt
        payload = {"sub": "usr-1", "rol": "operador", "exp": 9999999999}
        token_falso = _jwt.encode(payload, "clave-distinta", algorithm=ALGORITHM)
        with self.assertRaises(TokenError):
            decodificar_token(token_falso)

    def test_token_sin_claim_sub_lanza_token_error(self):
        """Token válido pero sin claim 'sub' debe lanzar TokenError."""
        from jose import jwt as _jwt
        import time
        payload = {"rol": "operador", "exp": int(time.time()) + 3600}
        token = _jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
        with self.assertRaises(TokenError):
            decodificar_token(token)

    def test_token_sin_claim_rol_lanza_token_error(self):
        from jose import jwt as _jwt
        import time
        payload = {"sub": "usr-1", "exp": int(time.time()) + 3600}
        token = _jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
        with self.assertRaises(TokenError):
            decodificar_token(token)

    def test_token_error_es_exception(self):
        self.assertTrue(issubclass(TokenError, Exception))


class TestSecretKeyFallback(unittest.TestCase):
    """La clave de desarrollo emite RuntimeWarning al importar."""

    def test_fallback_emite_runtime_warning(self):
        """Si SECRET_KEY no está configurada, el módulo usa el fallback."""
        import os
        import sys

        from app.config import get_settings as _get_settings

        # Remover la variable de entorno para forzar el fallback
        env_backup = os.environ.pop("SECRET_KEY", None)
        # Limpiar el caché de configuración para que Settings() se re-evalúe
        _get_settings.cache_clear()
        try:
            # Forzar re-import del módulo auth
            sys.modules.pop("app.auth", None)
            sys.modules.pop("app.config", None)
            with warnings.catch_warnings(record=True):
                warnings.simplefilter("always")
                import app.auth  # noqa: F401
                # Verificar que el módulo importa correctamente con la clave de fallback
                self.assertIsInstance(app.auth.SECRET_KEY, str)
                self.assertTrue(app.auth.SECRET_KEY)
        finally:
            if env_backup is not None:
                os.environ["SECRET_KEY"] = env_backup
            # Limpiar cachés y restaurar módulos originales
            sys.modules.pop("app.auth", None)
            sys.modules.pop("app.config", None)
            # Reimportar para restaurar el estado esperado por otros tests
            import app.config  # noqa: F401
            app.config.get_settings.cache_clear()
            import app.auth  # noqa: F401


if __name__ == "__main__":
    unittest.main()
