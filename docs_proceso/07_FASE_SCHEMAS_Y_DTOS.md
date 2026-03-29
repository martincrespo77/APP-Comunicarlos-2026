# Fase 7: Schemas y DTOs

## 1. Objetivo de la fase
Establecer los Data Transfer Objects (DTOs) para blindar el paso fronterizo entre las peticiones HTTP (archivos JSON o requests crudos en Postman) y la estricta pureza de nuestros servicios internos. 

## 2. El exilio voluntario de Pydantic
Mencionamos extensamente en nuestras lecciones aprendidas que a *Pydantic V2* se lo excluyó radicalmente del Dominio. Entonces, su "hogar principal" floreció aquí. Las clases de Schema nacen puramente como barreras físicas: Un `RequerimientoCrearInput` hereda de la clase fundamental BaseModel. 

## 3. Schemas de entrada y salida aislados
De los endpoints web recibimos y escupimos exclusivas instancias de Pydantic, jamás modelos de SQLAlchemy y **jamás nuestras Entidades puras**.
Por ejemplo:
- Para salida creamos `RequerimientoOutput`, que mapea propiedades de la clase central hacia una representación JSON asimilable (convirtiendo enums, ids extraños, o desestibando metadatos para la carga front-end).

## 4. Por qué los Routers agradecen esto
Teniendo a su disposición los Archivos de Schemas, el trabajo principal del framework web (Fastapi en Fase 8) disminuye a un absurdo minimalista. Gracias a Pydantic V2, nuestra validación web contra strings raros o integers esperados es resuelta por la capa C oculta de Fastapi; nuestros Controladores asumen que el "Json es perfecto y validado" antes de ejecutar una sola línea Python contra nuestras preciadas defensas de negocio.
