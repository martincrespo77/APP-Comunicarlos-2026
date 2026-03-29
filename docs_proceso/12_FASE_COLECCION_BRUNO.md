# Fase 12: Colección Bruno (Testing E2E Manual)

## 1. Objetivo de la fase
Reemplazar y dejar explícitamente documentados los tests de aceptación en un formato visible que pudiese testear todas nuestras interacciones y flujos cruzados tal cual lo hace un Front End real contra el Servidor de API, eliminando test manual superficial usando la frágil UI de Swagger.

## 2. Por qué Bruno
A diferencia de colecciones populares monolíticas JSON inmensas incrustadas en base de datos propietarias (Ej. Postman), **Bruno** utiliza archivos legibles, puramente de texto plano (`.bru`) que conviven fluidamente dentro de nuestra carpeta Git del repositorio (`/bruno`). Permitiendo un control de versiones de la API en el mismo instante en el que los ingenieros modifican o testean una nueva petición.

## 3. Estructura de la Colección (57 Requests)
Se categorizó metodológicamente en carpetas secuenciales dictando el orden maestro de una sesión de demo para el profesor:
- 01 -> Estado de Salud
- 02 -> Creaciones asimétricas de los Usuarios
- 03 -> Autenticaciones e inicio de sesión obteniendo portadores (Tokens Bearer).
- 04 a 09 -> Ciclo de Vida: Abarca desde crear incidentes, listar como supervisor un error perjudicial intermedio, hasta derivarlo cerrando su camino feliz en estado Resuelto. 

## 4. Variables reutilizables
Para ejecutar tests rápidos en Bruno se declararon en `Local.bru` un ambiente variable; en lugar de pegar infinitamente copias de los códigos JWT en headers repetitivos por 50 llamadas, la API lee dinámicamente de variables globales como `token_operador`, `id_incidente_creado` optimizando colosalmente la demostración oral con un par de clics y reduciendo riesgos frente a fallos humanos. 

## 5. Estado de Cierre
Todo el sistema está abarcado; tanto caminos nobles y exitosos (flujos felices 200) como choques adrede programados: Probando, con 401 y 403, que no es lícito intentar "iniciar" un ticket por su número si estás logeado como `Solicitante` sin credenciales de Técnico. Bruno materializa de primera mano la impenetrable seguridad forjada al nivel de Servicios.
