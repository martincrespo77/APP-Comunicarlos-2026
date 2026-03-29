# Fase 4: Tests de Dominio

## 1. Objetivo de la fase
Garantizar la protección irrefutable sobre las entidades del Agregado Raíz, testificando cada transición de estado legal, cada excepción bloqueante y el control de los eventos producidos usando `pytest`.

## 2. Estrategia de tests implementada
Los tests de la fase 4 se basan en ser puramente unitarios. Cada archivo en `tests/` replica la estructura de los módulos de `app/dominio/`. Se ejecutan sin base de datos real.

## 3. Por qué certificar el dominio antes de avanzar
Escribimos explícitamente y bloqueamos por completo la capa central en base a TDD parcial. Intentar escribir los Servicios (fase 6) sin tener la confianza absoluta de que un "Supervisor Re-asignando" dispara correctamente el evento sería crear un castillo de naipes inestable.

## 4. Qué y cuánto se validó
Se alcanzaron **más de 150 test exclusivamentes dirigidos al dominio**; más del doble de esta cifra será lograda al incluir integración.
Se validaron minuciosamente:
- A. **Invariantes e instanciación**: Que no nazca un ticket sin la descripción requerida o un usuario genérico.
- B. **Control Estricto de Rol**: Transiciones ejecutadas con roles incorrectos lanzando `RequerimientoExcepcion`.
- C. **Máquina de Estado**: Transiciones imposibles (iniciar un ticket resuelto, pedir asignación sin paso inicial).

## 5. Errores conceptuales curados gracias a la suite
Durante la implementación de estos tests notamos que algunos eventos de Re-asignación se omitían si un ticket en progreso colisionaba con otro id, o que a las listas encadenadas de eventos no se les aplicaba re-inicialización profunda. Si esto se subía en el ecosistema productivo (o peor, se detectaba durante la fase Web FastAPI) debuggear por qué un técnico no cobró el bono asociado al ticket de su tabla habría sido horrendo.
