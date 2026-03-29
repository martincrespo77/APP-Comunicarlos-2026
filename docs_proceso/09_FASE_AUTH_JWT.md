# Fase 9: Autorización y JWT

## 1. Objetivo de la fase
Proteger los endpoints del Router asegurando autenticación del portador de token (Stateless Security) e implementando un motor robusto de autorización por roles (Solicitante, Técnico, Operador, Supervisor).

## 2. Por qué JWT y por qué bcrypt quedaron fuera del dominio
Como explicamos en instancias anteriores, hashear la contraseña (`bcrypt`) y modelar un token Firmado (`Jose`/JWT) son detalles de criptografía informática en contexto HTTP. Nuestro core (Mesa de Ayuda de Reparación) no debe conocer qué significa un Token Bearer. Por eso viven estrictamente en un módulo `auth.py` de la capa de Infraestructura, ajenos al perfil real en base de datos.

## 3. Claims del token
El JWT que generamos porta lo estadísticamente útil sin caer en abusos de información.
Payload estándar:
- `sub`: Identificación única universal (UUID) del usuario.
- `rol`: El string derivado del enum `RolUsuario` para evitar consultar la DB en requests repetitivos.
- `exp`: Tiempo en Epoch Unix que define cuándo debe descartarse de parte del cliente.

## 4. `get_current_user` y autorización por rol
FastAPI brilla con su generador de inyección. Con este método inquirimos si el usuario que llama lleva su credencial activa e íntegra.
Adicionalmente generamos clausuras como `RequireRole(RolUsuario.TECNICO)` capaces de bloquear el endpoint inmediatamente y expeler `HTTP 403 Forbidden` cuando el usuario autenticado (con Token Válido 200 - OK) asume una acción para la que no posee permisos jerárquicos.

## 5. Resultado de la fase
El proyecto se volvió monolíticamente tenso frente a intromisiones sin autorización, discriminando rigurosamente a los usuarios no encontrados (`401 Unauthorized`) de aquellos entrometidos sin permisos de acción específicos (`403 Forbidden`). Esto cierra el pasaje general del nivel de Presentación HTTP.
