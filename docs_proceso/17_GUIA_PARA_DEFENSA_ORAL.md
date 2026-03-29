# Guía para Defensa Oral

El objetivo de este documento es preparar un discurso sólido y estructurado para la presentación y defensa de la Práctica Profesional 5 (Mesa de Ayuda Comunicarlos). Sintetiza las decisiones y está diseñado como un "acordeón" conceptual.

---

## 1. Recorrido del Proyecto: El "Elevator Pitch"
"Este proyecto resuelve la gestión de incidentes y solicitudes para la cooperativa, pero su verdadero valor no es funcional, sino arquitectónico. Decidí implementar una **Arquitectura en Capas estricta**, guiada por el **Domain-Driven Design (DDD)**. No es simplemente un CRUD rápido en FastAPI; es un sistema donde las reglas de negocio del Dominio viven en objetos de Python Puro, aislados 100% de la base de datos (MongoDB/pymongo) y de la web (Pydantic / Web HTTP). La prueba definitiva: migramos de SQLAlchemy/SQLite a MongoDB sin tocar una sola línea de dominio ni servicios."

## 2. Decisiones Técnicas y su Justificación (El "Por qué")

### a. Exclusión de Pydantic y SQLAlchemy del Dominio
- **La Pregunta:** *¿No es escribir de más tener una entidad pura, un Schema de Pydantic y un Modelo de base de datos separados?*
- **La Justificación:** "Previene el acoplamiento tóxico. De hecho, migramos exitosamente de SQLAlchemy/SQLite a MongoDB/pymongo y las reglas de que 'un técnico no se auto-asigna' no cambiaron ni una línea. Esa es la prueba concreta de que la separación funciona."

### b. Elección de MongoDB como Base de Datos
- **La Pregunta:** *¿Por qué MongoDB y no una base relacional como Postgres?*
- **La Justificación:** "Nuestros requerimientos son documentos ricos con eventos y comentarios embebidos — un ajuste natural para un modelo documental. MongoDB facilita el despliegue con Docker (`docker compose up`) y la estructura flexible se alinea con el dominio. Originalmente usábamos SQLite; la migración completa a MongoDB demostró que la arquitectura hexagonal con repositorios abstractos cumplió su propósito."

### c. Autenticación y Criptografía (JWT y bcrypt) en Infraestructura
- **La Pregunta:** *¿Por qué el hasheo y el token aparecen tan 'afuera' del dominio de Usuarios?*
- **La Justificación:** "Porque el Dominio define 'quién' es el rol, no 'cómo' el mundo exterior demuestra ser ese rol matemáticamente. JWT es un detalle de HTTP. Si en 2 años migramos a OAuth2, mi entidad `Usuario` ni siquiera lo nota."

### d. Bruno para la recolección de pruebas HTTP
- **La Justificación:** "A diferencia de Postman, Bruno guarda la configuración de los endpoints en sintaxis abierta de texto plano (`.bru`). Esto me permite versionar y sincronizar mis escenarios de prueba directamente con el repositorio en GitHub (Git)."

## 3. Fortalezas del Sistema
- **Testing Blindado:** 394 tests ejecutando en milisegundos gracias a la posibilidad de inyectar dependencias y de testear "objetos puros" en la suite unitaria.
- **Ruteo anémico, modelos ricos:** Los `@router` son simples 'repartidores'. Las entidades son las que validan transiciones de estado complejas usando `Factory` y máquinas de estado en código.
- **Trazabilidad de Eventos:** El uso del patrón _Observer_ permite que un requerimiento al ser "Resuelto" acumule un evento de dominio, sin enviar Mails de verdad acoplando clases.

## 4. Límites Conscientes (Saber admitir lo que falta)
- **Concurrencia extrema:** MongoDB maneja mejor la concurrencia que SQLite, pero en escenarios de altísima carga se necesitarían replica sets y sharding.
- **Paginación:** Las listas actuales devuelven todo (Ideal para la demo, pero en producción real exigiríamos `limit/offset` en las consultas de los repos).

## 5. Preguntas Difíciles que enfrentarás
1. **P:** *"¿Por qué `Incidente` y `Solicitud` son clases diferentes si casi tienen los mismos datos en DB?"*
   - **R:** Porque el polimorfismo DDD se hace por *comportamiento*. A un Incidente se le exige Nivel de Urgencia; a una solicitud de "mouse nuevo" no debemos forzarla a tener Urgencia Crítica.
2. **P:** *"Si el Servicio recupera de la base, llama a la entidad y vuelve a guardar a la base, no sería más rápido hacer un `UPDATE tabla SET x=Y` directamente?"*
   - **R:** "Sí en CPU, un absoluto 'no' en diseño. Actualizar directo mediante `update_one($set)` (Data-Driven) destruye el encapsulamiento y nos saltea los disparadores de auditoría y validaciones de estado que protege la Entidad en memoria."

## 6. Dinámica sugerida en la DEMO
1. Mostrar el código por encima (mostrar que Dominio NO importa framework).
2. Levantar la aplicación con Docker (`docker compose up`).
3. Correr los \~400 tests en consola para demostrar robustez.
4. Abrir la interfaz Bruno y correr el ciclo de vida de un requerimiento normal (asignar -> iniciar -> resolver).
