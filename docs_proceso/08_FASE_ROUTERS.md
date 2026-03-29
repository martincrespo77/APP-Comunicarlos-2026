# Fase 8: Routers (Presentación HTTP)

## 1. Objetivo de la fase
Exponer las capacidades de nuestros Servicios (Capa de Aplicación) a través de los puertos web (FastAPI), traduciendo los DTOs a lenguaje Python interno y mapeando las excepciones esperadas a códigos de error HTTP formales.

## 2. Por qué los routers quedaron "delgados"
Un router "gordo" haría que validar la asignación de un técnico u obtener sus atributos sea un monstruo ilegible en el controlador web. Nuestro diseño garantiza que los endpoints consistan típicamente en solo tres pasos:
A) Recibir Input Pydantic (Validación automática de Sintaxis).
B) Invocar al `_Servicio` o Caso de Uso correspondiente inyectado, transfiriendo los valores crudos.
C) Retornar la clase `OutputSchema` elegida.

## 3. Uso de dependencias (`Depends`)
El archivo principal de infraestructura web es un orquestador de inyección: en lugar de instanciar Servicios manualmente con dependencias de infraestructura, FastAPI inyecta limpiamente `Depends(get_requerimiento_service)` al momento en que entra un Request. Esto facilitó poder sobreescribir dependencias en los tests e inyectar *Fake Repositorios*.

## 4. Mapeo de errores HTTP
Las excepciones arrojadas por las Entidades (Ej: `TransicionInvalidaExcepcion`) viajan a través del catch del Service de Forma transparente, o son atrapadas por Middleware global del Router y mutadas mágicamente en HTTP status `400 Bad Request`. Excepciones puramente de infraestructura (como un Id no encontrado en la base de datos) se convierten en claros `404 Not Found`.

## 5. Resultado de la fase
- Endpoints totalmente funcionales documentados autómaticamente en Swagger (`/docs`).
- Controladores libres de ruido de base de datos, altamente testeables con `httpx.TestClient`.
