# Guía de Defensa Oral - PP5 (Mesa de Ayuda Comunicarlos)

Este documento es un "acordeón" detallado y estructurado para defender la arquitectura y las decisiones técnicas de tu Práctica Profesional 5.

---

## 1. Resumen de la Arquitectura
El proyecto implementa una **Arquitectura en Capas estricta**, fuertemente inspirada en **Arquitectura Hexagonal (Ports and Adapters)** y **Domain-Driven Design (DDD)**. 

Está dividida conceptualmente en tres aros concéntricos:
1. **Dominio (Interior)**: Reglas de negocio puras, entidades y excepciones core. No sabe que existe internet ni bases de datos.
2. **Aplicación (Medio)**: Los "Servicios" o "Casos de Uso". Orquestan la operación (buscan en DB, ejecutan lógica de dominio, guardan en DB), protegiendo al dominio del mundo exterior.
3. **Infraestructura / Presentación (Exterior)**: Pydantic, FastAPI, pymongo (MongoDB), Autenticación. Es el detalle de cómo entran y salen los datos.

**Regla de Oro**: Las dependencias *siempre* apuntan hacia adentro. Infraestructura conoce a Dominio, pero Dominio no conoce a Infraestructura.

---

## 2. Decisiones importantes de diseño
- **Modelado Rico (DDD)**: Se evitaron los objetos "anémicos" (clases que solo tienen getters y setters). La entidad `Requerimiento` concentra la lógica real (`iniciar_trabajo()`, `agregar_comentario()`).
- **Interfaces / Puertos**: Los servicios no interactúan con bases de datos directamente, sino con clases abstractas (Repositorios). 
- **Inyección de Dependencias**: Se usa `Depends` de FastAPI para inyectar los repositorios y servicios en los controladores, facilitando el testing aislado.
- **Auditoría Integrada**: Los requerimientos guardan `Eventos` de dominio por cada transición de estado realizada, garantizando consistencia.

---

## 3. ¿Por qué el Dominio quedó "Puro"?
*Es probable que el profesor pregunte por qué separaste los schemas Pydantic y la persistencia MongoDB de las clases puras de Python.*

**Respuesta a defender:** 
"El dominio es el corazón de la cooperativa. Si el día de mañana queremos cambiar FastAPI por otro framework HTTP, o migrar de MongoDB a otra base de datos, las reglas de cómo un técnico 'deriva' un ticket no cambian en absoluto. De hecho, el proyecto nació con SQLAlchemy/SQLite y se migró completamente a MongoDB sin tocar una sola línea del dominio ni de los servicios. Esa migración fue la prueba concreta de que la arquitectura hexagonal funcionó.
Tener Pydantic en el dominio nos ataría a validaciones JSON web; y usar pymongo en las entidades nos ataría a documentos MongoDB. Mantenerlo en 'Python Puro' asegura extrema facilidad para crear pruebas unitarias sin levantar motores de base de datos, porque las reglas de negocio están 100% aisladas."

---

## 4. ¿Por qué JWT y bcrypt están fuera del dominio?
**Respuesta a defender:**
"El cifrado de contraseñas (bcrypt) y la gestión de sesiones web (JWT) son **detalles técnicos de seguridad y entrega**, no reglas de la Mesa de Ayuda. Al dominio de 'Usuarios' solo le interesa saber que Juan es 'Técnico' y está 'Activo'. 
Cómo verificamos matemáticamente que Juan es Juan (mediante criptografía o headers HTTP) es responsabilidad exclusiva de la capa de Infraestructura (`auth.py`). Si mañana pasamos de JWT a OAuth2 o Cookies de sesión, el dominio `app/usuarios/dominio.py` ni se entera."

---

## 5. Cómo se organizan Servicios, Repositorios, Routers y Schemas
Esta es la ruta exacta (Flujo de Control) de una petición web en tu app:

1. **Routers (Presentación)**: Son los endpoints de FastAPI (`@router.post`). Reciben un JSON desde el cliente HTTP.
2. **Schemas (Contratos)**: El Router usa un modelo de Pydantic (Schema/DTO) para validar que el JSON venga bien formado (es un correo válido, el texto no está vacío).
3. **Servicios (Aplicación)**: El Router le pasa los datos limpios al Servicio. El Servicio coordina todo: 
   - Llama al Repositorio para buscar el usuario o requerimiento en la BD.
   - Llama al método de la entidad del Dominio (`req.asignar_tecnico()`).
   - Le dice al Repositorio que guarde la entidad modificada.
4. **Repositorios (Infraestructura)**: Reciben el mandato del Servicio, utilizan pymongo, serializan el objeto de Dominio a un documento MongoDB, y hacen el `replace_one()` / `find()` en la base de datos real.

---

## 6. Qué cubren los tests (394 Tests passing)
La suite de pruebas es un punto fortísimo de este proyecto. Se pueden dividir en dos bloques:
- **Test Unitarios del Dominio (La mayoría)**: Prueban las reglas de negocio base creando objetos en memoria. Ej: ¿Qué pasa si un Técnico intenta "asignarse" a sí mismo (debería fallar, es rol de Operador)? 
- **Test de Integración (Routers/Servicios)**: Usando el `TestClient` (`httpx`) de FastAPI y repositorios fake en memoria, verifican que el endpoint HTTP funcione de principio a fin (devuelva un HTTP 200 o HTTP 400), probando Pydantic y el Router a la vez, sin necesidad de Docker ni de enviar correos reales. Los tests de infraestructura usan `mongomock` (MongoDB en memoria) para verificar los repositorios concretos.

---

## 7. Cómo defender Docker, MongoDB y Bruno
- **¿Por qué Docker?** "Garantiza un ambiente estandarizado. Al profesor o a cualquier evaluador le basta ejecutar `docker compose up` y el sistema levanta la API junto con MongoDB, garantizando la misma versión de base de datos y Python. Es estándar en la industria ('works on my machine')."
- **¿Por qué Bruno (y no Postman)?** "Bruno es de código abierto, ultraligero y guarda la colección directamente en archivos `.bru` estructurados (en lugar de un JSON invisible). Esto permite que mi colección viva dentro del repositorio Git junto con mi código, pudiendo versionarla y auditarla como código normal."
- **¿Por qué MongoDB como Base de Datos?** "MongoDB como base documental permite almacenar el agregado completo (requerimiento + eventos + comentarios) en un solo documento, lo que garantiza escrituras atómicas sin transacciones complejas. El esquema flexible facilita la evolución del modelo sin migraciones. Además, `docker compose up` levanta MongoDB automáticamente junto con la API, sin configuración extra para el evaluador."
- **¿Por qué se migró de SQLite/SQLAlchemy a MongoDB?** "El proyecto nació con SQLite como MVP rápido. La migración a MongoDB fue una decisión deliberada que además sirvió como prueba concreta de que la Arquitectura Hexagonal funciona: solo se tocaron 7 archivos de infraestructura, sin modificar una sola línea del dominio, servicios ni routers. Los 394 tests siguieron pasando sin cambios."

---

## 8. Preguntas "Picantes" que podría hacer el profesor

**Pregunta 1:** *"Veo que tenés mucho código separado: un Schema para validar, un Servicio, y una Entidad. ¿No es sobre-ingeniería para hacer un simple alta de un Requerimiento?"*
**Sugerencia de respuesta:**
"Si esto fuera un CRUD básico (Crear, Leer, Actualizar, Borrar) como un blog, sí, sería sobre-ingeniería. Pero una Mesa de Ayuda involucra máquinas de estado complejas: permisos cruzados, derivaciones, re-asignaciones y registro de eventos. Escribir esa lógica estructurada en un 'controlador web acoplado a SQL' se vuelve espagueti rápidamente. Dividirlo paga su precio inmediatamente en facilidad de testing: hoy tenemos casi 400 pruebas porque es facilísimo testear componentes aislados."

**Pregunta 2:** *"¿Qué pasa si 5 operadores guardan un requerimiento al mismo tiempo en producción?"*
**Sugerencia de respuesta:**
"MongoDB maneja la concurrencia de escritura de forma nativa. Cada requerimiento se almacena como un documento atómico completo (con eventos y comentarios embebidos), por lo que `replace_one()` es una operación atómica a nivel de documento. No hay riesgo de locks de archivo como con SQLite ni necesidad de transacciones multi-tabla como con un motor relacional. Para escenarios de alta concurrencia, MongoDB escala horizontalmente con replica sets."

**Pregunta 3:** *"En `servicios.py`, para asignar un técnico, veo que buscás el ticket en DB, lo cargás a memoria, le aplicás la operación y luego lo volvés a grabar. ¿No es más eficiente hacer un `update_one({$set: {tecnico_id: X}})` directo en MongoDB?"*
**Sugerencia de respuesta:**
"Hacer un update directo es más rápido para el CPU, sí, pero es un anti-patrón en DDD llamado 'Data-Driven Design'. Si hago el update directo, me salto **todas** las validaciones de negocio de nuestra entidad (como comprobar si el requerimiento estaba bloqueado, y evitar que se genere el Evento de Auditoría obligatorio). Preferimos ceder unos microsegundos de RAM y CPU para garantizar absoluta consistencia del negocio mediante el uso del Aggregate Root."

**Pregunta 4:** *"¿Por qué separo Incidentes de Solicitudes si usan básicamente la misma tabla/lógica?"*
**Sugerencia de respuesta:**
"Porque a nivel *Concepto de Negocio*, aunque compartan campos (título, descripción), tienen comportamientos e invariantes distintos. Un Incidente **obliga** a definir un nivel de 'Urgencia', mientras que exigir urgencia en pedir un teclado nuevo (Solicitud) no tiene sentido en nuestro dominio. El polimorfismo nos garantiza tratar la lógica de SLA según corresponda."
