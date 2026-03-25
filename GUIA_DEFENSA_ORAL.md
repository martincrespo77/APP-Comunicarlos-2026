# Guía de Defensa Oral - PP5 (Mesa de Ayuda Comunicarlos)

Este documento es un "acordeón" detallado y estructurado para defender la arquitectura y las decisiones técnicas de tu Práctica Profesional 5.

---

## 1. Resumen de la Arquitectura
El proyecto implementa una **Arquitectura en Capas estricta**, fuertemente inspirada en **Arquitectura Hexagonal (Ports and Adapters)** y **Domain-Driven Design (DDD)**. 

Está dividida conceptualmente en tres aros concéntricos:
1. **Dominio (Interior)**: Reglas de negocio puras, entidades y excepciones core. No sabe que existe internet ni bases de datos.
2. **Aplicación (Medio)**: Los "Servicios" o "Casos de Uso". Orquestan la operación (buscan en DB, ejecutan lógica de dominio, guardan en DB), protegiendo al dominio del mundo exterior.
3. **Infraestructura / Presentación (Exterior)**: Pydantic, FastAPI, SQLAlchemy, Autenticación. Es el detalle de cómo entran y salen los datos.

**Regla de Oro**: Las dependencias *siempre* apuntan hacia adentro. Infraestructura conoce a Dominio, pero Dominio no conoce a Infraestructura.

---

## 2. Decisiones importantes de diseño
- **Modelado Rico (DDD)**: Se evitaron los objetos "anémicos" (clases que solo tienen getters y setters). La entidad `Requerimiento` concentra la lógica real (`iniciar_trabajo()`, `agregar_comentario()`).
- **Interfaces / Puertos**: Los servicios no interactúan con bases de datos directamente, sino con clases abstractas (Repositorios). 
- **Inyección de Dependencias**: Se usa `Depends` de FastAPI para inyectar los repositorios y servicios en los controladores, facilitando el testing aislado.
- **Auditoría Integrada**: Los requerimientos guardan `Eventos` de dominio por cada transición de estado realizada, garantizando consistencia.

---

## 3. ¿Por qué el Dominio quedó "Puro"?
*Es probable que el profesor pregunte por qué separaste los modelos de SQLAlchemy/Pydantic de las clases puras de Python.*

**Respuesta a defender:** 
"El dominio es el corazón de la cooperativa. Si el día de mañana queremos cambiar FastAPI por otro framework HTTP, o migrar de SQLite a PostgreSQL o incluso MongoDB, las reglas de cómo un técnico 'deriva' un ticket no cambian en absoluto. 
Tener Pydantic en el dominio nos ataría a validaciones JSON web; y usar SQLAlchemy en las entidades nos ataría a tablas relacionales. Mantenerlo en 'Python Puro' asegura extrema facilidad para crear pruebas unitarias sin levantar motores de base de datos, porque las reglas de negocio están 100% aisladas."

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
4. **Repositorios (Infraestructura)**: Reciben el mandato del Servicio, utilizan SQLAlchemy, mapean el objeto de Dominio a una fila SQL, y hacen el `commit()` en la base de datos real.

---

## 6. Qué cubren los tests (384 Tests passing)
La suite de pruebas es un punto fortísimo de este proyecto. Se pueden dividir en dos bloques:
- **Test Unitarios del Dominio (La mayoría)**: Prueban las reglas de negocio base creando objetos en memoria. Ej: ¿Qué pasa si un Técnico intenta "asignarse" a sí mismo (debería fallar, es rol de Operador)? 
- **Test de Integración (Routers/Servicios)**: Usando el `TestClient` (`httpx`) de FastAPI y una base SQLite en memoria, verifican que el endpoint HTTP funcione de principio a fin (devuelva un HTTP 200 o HTTP 400), probando la base de datos, Pydantic y el Router a la vez, sin necesidad de Docker ni de enviar correos reales.

---

## 7. Cómo defender Docker, SQLite y Bruno
- **¿Por qué Docker?** "Garantiza un ambiente estandarizado. Al profesor o a cualquier evaluador le basta ejecutar `docker compose up` y el sistema levanta garantizando la misma versión de base de datos y Python. Es estándar en la industria ("works on my machine")."
- **¿Por qué Bruno (y no Postman)?** "Bruno es de código abierto, ultraligero y guarda la colección directamente en archivos `.bru` estructurados (en lugar de un JSON invisible). Esto permite que mi colección viva dentro del repositorio Git junto con mi código, pudiendo versionarla y auditarla como código normal."
- **¿Por qué SQLite como Base de Datos?** "Decisión consciente para un MVP (Minimum Viable Product) académico. SQLite nos da un motor relacional sólido sin requerir configuración externa pesada, facilitando enormemente la corrección y pruebas del docente. La ventaja de nuestra Arquitectura Hexagonal es que migrar a PostgreSQL (dejado propuesto en el `docker-compose.yml`) solo requiere cambiar una cadena de texto en un archivo `.env`, el código de la app Python permanece intacto."

---

## 8. Preguntas "Picantes" que podría hacer el profesor

**Pregunta 1:** *"Veo que tenés mucho código separado: un Schema para validar, un Servicio, y una Entidad. ¿No es sobre-ingeniería para hacer un simple alta de un Requerimiento?"*
**Sugerencia de respuesta:**
"Si esto fuera un CRUD básico (Crear, Leer, Actualizar, Borrar) como un blog, sí, sería sobre-ingeniería. Pero una Mesa de Ayuda involucra máquinas de estado complejas: permisos cruzados, derivaciones, re-asignaciones y registro de eventos. Escribir esa lógica estructurada en un 'controlador web acoplado a SQL' se vuelve espagueti rápidamente. Dividirlo paga su precio inmediatamente en facilidad de testing: hoy tenemos casi 400 pruebas porque es facilísimo testear componentes aislados."

**Pregunta 2:** *"Si uso SQLite en vez de Postgres, ¿qué pasa si 5 operadores guardan un requerimiento al mismo tiempo en producción?"*
**Sugerencia de respuesta:**
"Fallaría debido a los bloqueos de escritura (locks) inherentes a SQLite si hay concurrencia pesada. Soy consciente de esa limitación técnica: SQLite fue elegido **exclusivamente como base embebida para facilitar el despliegue del trabajo práctico**. La arquitectura prevé esto: nuestros repositorios inyectan sesiones de SQLAlchemy agnósticas, preparadas para un motor robusto como PostgreSQL con sólo enchufarlo a nivel infraestructura."

**Pregunta 3:** *"En `servicios.py`, para asignar un técnico, veo que buscás el ticket en DB, lo cargás a memoria, le aplicás la operación y luego lo volvés a grabar. ¿No es más eficiente hacer un simple `UPDATE requerimientos SET tecnico_id = X` directo en un query SQL?"*
**Sugerencia de respuesta:**
"Hacer un UPDATE directo es más rápido para el CPU, sí, pero es un anti-patrón en DDD llamado 'Data-Driven Design'. Si hago el UPDATE directo, me salto **todas** las validaciones de negocio de nuestra entidad (como comprobar si el requerimiento estaba bloqueado, y evitar que se genere el Evento de Auditoría obligatorio). Preferimos ceder unos microsegundos de RAM y CPU para garantizar absoluta consistencia del negocio mediante el uso del Aggregate Root."

**Pregunta 4:** *"¿Por qué separo Incidentes de Solicitudes si usan básicamente la misma tabla/lógica?"*
**Sugerencia de respuesta:**
"Porque a nivel *Concepto de Negocio*, aunque compartan campos (título, descripción), tienen comportamientos e invariantes distintos. Un Incidente **obliga** a definir un nivel de 'Urgencia', mientras que exigir urgencia en pedir un teclado nuevo (Solicitud) no tiene sentido en nuestro dominio. El polimorfismo nos garantiza tratar la lógica de SLA según corresponda."
