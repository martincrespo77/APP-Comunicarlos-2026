# Objetivo y Contexto

## 1. Objetivo de la fase
Definir claramente el problema a resolver en el Trabajo Práctico 5, enumerar las restricciones dictadas por la cátedra y justificar el stack tecnológico elegido para cumplir y exceder dichos requerimientos.

## 2. Contexto del Proyecto
La **Cooperativa Comunicarlos** requiere un sistema interno para la "Mesa de Ayuda". El objetivo es la gestión integral del ciclo de vida de **Requerimientos**. Estos se dividen orgánicamente en Incidentes (problemas de servicio) y Solicitudes de Servicio (pedidos nuevos). 
Se exigen cuatro roles base: Solicitante, Operador, Técnico y Supervisor, cada uno con acciones cruzadas estrictamente delimitadas por permisos.

## 3. Restricciones del Enunciado (MVP Académico)
- Entregar una solución ejecutable sin requerir servidores de terceros complejos.
- Desarrollar todos los endpoints HTTP necesarios (REST API).
- El sistema de base de datos debe ser fácilmente reproducible por los profesores (generalmente SQLite sirve a este propósito, aunque Postgres es sugerido).
- No implementar frontend real, limitándose exclusivamente a probar el ecosistema del backend.
- Pruebas manuales validadas a través de un archivo de colección.

## 4. Stack Adoptado
- **Capa de Dominio**: Python 3.12 puro (OOP limpio, sin dependencias externas explícitas).
- **Capa de Interfaces WEB**: FastAPI para el control de enrutamiento y Pydantic v2 para validación cruda de esquemas JSON entrantes/salientes.
- **Capa de Persistencia**: pymongo actuando de adaptador contra **MongoDB**. (Originalmente SQLAlchemy/SQLite; migrado a MongoDB al cierre del proyecto como prueba concreta de la arquitectura hexagonal).
- **Capa de Testing**: mongomock para tests de integración, fakes manuales para tests unitarios de servicios.
- **Gestión de Entorno**: `uv` en lugar de pip, junto a Docker para aislar la instancia en su defensa oral.
- **Validación Visual/Postman**: Bruno (`.bru`) para control de versiones en el repositorio remoto.

## 5. Criterio de trabajo por fases
Para evitar un diseño monolítico, estructuramos el trabajo en capas, procediendo estrictamente de adentro hacia afuera:
1. **Dominio**: Clases abstractas puras, diccionarios de la arquitectura "Hexagonal".
2. **Tests de Dominio**: Certeza matemática de los invariantes de los modelos sin tocar la base de datos.
3. **Repositorios y Servicios**: Lógica de aplicación que transita información entre puertos.
4. **Infraestructura**: Acoplamiento final de FastAPI endpoints a los adaptadores ORM de la Base de datos.
