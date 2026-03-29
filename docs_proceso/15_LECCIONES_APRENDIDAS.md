# Lecciones Aprendidas

## 1. Objetivo de la fase
Consolidar la experiencia adquirida durante el desarrollo de la Mesa de Ayuda, identificando aciertos metodológicos, errores superados y buenas prácticas asimiladas para aplicar en la carrera profesional.

## 2. Lecciones de Modelado (Arquitectura y Dominio)
- **El dominio puro vale el esfuerzo inicial:** Abandonar Pydantic en la capa de entidades (`app/*/dominio.py`) pareció doloroso al principio por la cantidad de código puro manual (`@property`, excepciones custom). Sin embargo, pagó sus dividendos de inmediato: modificar reglas de derivación o estados no rompió ni una sola validación HTTP ni tabla de la base de datos.
- **Evitar la anemia:** Un modelo anémico (solo getters y setters) habría transformado los `Servicios` en enormes scripts inmanejables. Concentrar la lógica en el Root Aggregate (`Requerimiento.asignar_tecnico()`, etc.) centraliza la verdad del negocio.
- **Eventos de Dominio:** Usar un observador interno (`_eventos_dominio`) para no acoplar el envío de correos o notificaciones a transacciones HTTP, fue uno de los saltos de calidad más grandes.

## 3. Lecciones de Testing
- **Separación del nivel de prueba:** Hacer 150+ pruebas a objetos de memoria (Dominio) toma milisegundos. Tratar de probar todas las reglas de negocio desde peticiones HTTP completas (TestClient + Database) hubiese hecho que la suite tarde minutos en correr, dañando la experiencia de desarrollo.
- **El peligro del "Test Monolito":** Al inicio, `test_requerimientos_dominio.py` se volvió enorme. Aprendimos sobre deuda técnica por volumen; los tests también deben refactorizarse y organizarse lógicamente.

## 4. Lecciones en el uso de Inteligencia Artificial
- **No pedir magia:** Pedir a la IA "haceme el backend" causa un desastre acoplado. Pedir "Refactoriza esta entidad pure-python para reflejar esta transición de estado específica" da un resultado magistral.
- **Thinking es fundamental:** Modelos estructurados (como Sonnet en modo Thinking) se equivocan mucho menos en inyección de dependencias porque "piensan" el mapeo antes de escribir código impulsivo.

## 5. Lecciones de control de alcance (MVP vs Producción)
- **Saber cuándo detenerse:** Decidimos usar SQLite a pesar de su nula capacidad para concurrencia masiva. Para el contexto evaluativo (PP5) era la decisión inteligente: facilita enormemente el despliegue al profesor sin necesidad de configuraciones obscuras. La Arquitectura Hexagonal garantiza que pasar a Postgres es solo cambiar el `.env`.
- **Colección Postman/Bruno:** La adopción de `Bruno` y dejar `bruno/` en el repo en texto plano (`.bru`) permitió documentar y versionar visualmente las peticiones de prueba sin obligar a usar plataformas cloud invasivas.

## 6. Errores cometidos y corregidos
- *Error:* Casi dejamos `bcrypt` (hasheo) dentro de la entidad `Usuario`.
- *Corrección:* Nos dimos cuenta de que el cifrado es un detalle de "Infraestructura/Seguridad". Logramos mantener al usuario puro, permitiendo testear si "está activo o no" sin gastar preciosos ciclos de CPU calculando hashes en tests de interfaz.
- *Error:* Validar reglas de base de datos en los routers.
- *Corrección:* Reducir los routers a menos de 10 líneas de código; solo reciben el req, lo delegan al servicio y devuelven HTTP codes.

## 7. Reflexión Final
Este proyecto demostró que aplicar los principios SOLID y DDD en Python (FastAPI + MongoDB) es totalmente posible y genera aplicaciones a prueba de balas. La migración completa de SQLAlchemy/SQLite a MongoDB/pymongo sin tocar dominio ni servicios fue la prueba definitiva de que la arquitectura hexagonal funcionó. El sistema resultante es defendible académica y profesionalmente ante cualquier entrevista laboral.
