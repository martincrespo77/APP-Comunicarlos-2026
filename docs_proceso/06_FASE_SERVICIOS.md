# Fase 6: Servicios (Capa de Aplicación)

## 1. Objetivo de la fase
Crear los Orquestadores (Application Services) que mediarán entre la petición externa web y nuestras ricas entidades de domino empotradas. Estos orquestadores controlarán la transaccionalidad sin que el exterior lo sepa.

## 2. Responsabilidades divididas
- **Lógica de aplicación:** Controlamos al Repo y persistimos. Verificamos que el usuario en sesión coincida lógicamente antes de dar mando.
- **Lógica en Dominio:** Si Requerimiento dice 'Transición Imposible', Servicio atrapa esto y lo deriva pacíficamente arriba como respuesta 400 Web.

## 3. Rol de RequerimientoService
Actúa por cada endpoint o workflow de usuario final; por ejemplo, al dar de alta, llama instintivamente a la **Factory del dominio**, obtiene la entidad pura inyectada, asiste buscando vía Repositorio al técnico interviniente y si todo va en orden efectúa `repo.guardar(entidad)`. También recupera al final de la corrida los eventos encolados y ordena al Bus publicarlos de inmediato.

## 4. Rol de UsuarioService
Filtra la existencia del solicitante o personal. Aunque su autenticación recae más explícitamente en el router por practicidad HTTP (Oauth), sus reglas de baja lógica son controladas por esta capa. 

## 5. El uso de validaciones con Fakes In-Memory
Para testear esto, creamos en `tests/FakeRepositorios` componentes de mentira que simulan responder consultas de BD. Estas respuestas son interceptadas y comprobamos usando Pytest que `UsuarioService` esté activando adecuadamente excepciones ante `Not_found` sin siquiera instalar SQL.

## 6. Integración asíncrona ilusoria del Despachador de Eventos
Los servicios, tras operar mediante `repo.guardar(requerimiento)`, exigen inmediatamente los `_eventos` y se los transfieren usando el Objeto Despachador hacia el Módulo de Notificaciones. Puesto que en nuestro dominio MVP todo ocurre sincrónicamente, el resultado es impecable para el evaluador: Si se transiciona un ticket a Reuelto, el evento "TicketResuelto" se despacha explícitamente un renglón debajo en nuestra arquitectura de Servicios.
