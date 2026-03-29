# Índice General

## 1. Objetivo de este documento
Este es el archivo maestro de la documentación del proceso de desarrollo de la **Mesa de Ayuda - Cooperativa Comunicarlos** (PP5). Su propósito es organizar y guiar la lectura de todos los artefactos generados durante el ciclo de vida del proyecto.

## 2. Qué contiene la carpeta
La carpeta `docs_proceso` contiene un registro detallado de cada fase del proyecto, desde la concepción del dominio hasta el despliegue final y la defensa oral. Cada archivo resume las decisiones técnicas, problemas encontrados, y correcciones aplicadas en esa etapa específica.

## 3. En qué orden leerla
Para comprender la evolución y la justificación de la arquitectura, se recomienda el siguiente orden de lectura:

### I. Introducción y Estrategia
1. `01_OBJETIVO_Y_CONTEXTO.md`: Entender qué estamos resolviendo y con qué restricciones.
2. `02_ESTRATEGIA_DE_TRABAJO_CON_IA.md`: Conocer cómo nos apoyamos en IA para lograr un nivel profesional.
3. `14_DECISIONES_TECNICAS_CLAVE.md`: Resumen rápido de las grandes apuestas del proyecto.

### II. Fases Secuenciales de Desarrollo
4. `03_FASE_DOMINIO.md`: El corazón del negocio (Entidades puras).
5. `04_FASE_TESTS_DOMINIO.md`: Cómo blindamos las reglas de negocio.
6. `05_FASE_REPOSITORIOS_ABSTRACTOS.md`: Contratos de persistencia.
7. `06_FASE_SERVICIOS.md`: Casos de uso y orquestación.
8. `07_FASE_SCHEMAS_Y_DTOS.md`: Contratos de entrada y salida (Pydantic).
9. `08_FASE_ROUTERS.md`: Controladores y endpoints HTTP (FastAPI).
10. `09_FASE_AUTH_JWT.md`: Seguridad y permisos.
11. `10_FASE_INFRAESTRUCTURA_Y_PERSISTENCIA.md`: Bases de datos e implementación (originalmente SQLAlchemy, migrado a MongoDB).
12. `11_FASE_DOCKER_Y_DESPLIEGUE.md`: Contenerización y ejecución.
13. `12_FASE_COLECCION_BRUNO.md`: Pruebas de integración visual y uso.

### III. Cierre y Evaluación
14. `13_CONTROL_Y_TRAZABILIDAD.md`: Matriz de avance y control de calidad.
15. `15_LECCIONES_APRENDIDAS.md`: Reflexión sobre aciertos y errores.
16. `16_ESTADO_FINAL_Y_PENDIENTES.md`: Qué se logró y qué quedó pendiente.
17. `17_GUIA_PARA_DEFENSA_ORAL.md`: Hoja de ruta para la exposición final.

## 4. Dónde encontrar información clave
- **Trazabilidad y Estado Final**: Revisar los archivos `13_CONTROL_Y_TRAZABILIDAD.md` y `16_ESTADO_FINAL_Y_PENDIENTES.md`.
- **Reflexiones y Lecciones**: Archivo `15_LECCIONES_APRENDIDAS.md`.
- **Preparación para exponer**: Archivo `17_GUIA_PARA_DEFENSA_ORAL.md`.
