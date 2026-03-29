# Estrategia de Trabajo con IA

## 1. Objetivo de la fase
Documentar cómo se integraron herramientas de Inteligencia Artificial Generativa en el ciclo de vida del proyecto para diseñar, auditar, refactorizar e implementar el código de manera profesional y controlada.

## 2. Qué se hizo
Se adoptó un enfoque de "Pair Programming" con modelos avanzados de IA, asignando roles específicos a cada modelo según sus fortalezas cognitivas, evitando la generación masiva de código (zero-shot) sin validación arquitectónica.

### Modelos Utilizados:
- **Claude 3.7 Sonnet (Thinking) / Claude Sonnet 4.6 (Thinking):**
  - *Uso:* Diseño arquitectónico de alto nivel, refactorizaciones profundas (extirpación de Pydantic del dominio), diseño de interfaces (Ports and Adapters) y auditoría estricta de principios Solid y DDD.
  - *Por qué:* Su capacidad de razonamiento prolongado permite visualizar el impacto de dependencias y asegurar que la inversión de dependencias sea correcta antes de escribir una sola línea de código.
- **Otros Modelos de Asistencia (como asistentes integrados en IDE o agentes locales):**
  - *Uso:* Ejecutar tareas repetitivas, generar tests unitarios basados en entidades ya consolidadas, comandos Docker y automatización de la documentación.

## 3. Decisiones tomadas
- **División de tareas estructurada:** Nunca se pidió "hacer el backend entero". Se avanzó estrictamente capa por capa: Dominio -> Tests -> Contratos -> Servicios -> Presentación -> Infraestructura.
- **Validación Humana como cuello de botella intencional:** La IA proponía diseños (ej. cómo modelar el agregado `Requerimiento` o `RolUsuario`), se discutía la propuesta, se ajustaba, y solo entonces se permitía la codificación.
- **Auditoría cruzada:** Constantemente se le pedía a la IA que auditara su propio diseño previo buscando faltas de pureza (ej. "Revisa si nos quedó algún @validator de pydantic escondido en las entidades").

## 4. Problemas detectados
- **Alucinaciones de acoplamiento:** Ocasionalmente, los modelos asumían el uso de SQLAlchemy directo en los servicios o devolvían Modelos ORM desde los casos de uso por ser el patrón más común (MVC clásico), violando la arquitectura hexagonal deseada.
- **Tests superficiales:** Al delegar la creación de la suite de tests, la IA inicialmente generaba "happy paths" sin probar verdaderamente los invariantes o los errores de estado (ej. transiciones no permitidas en `Requerimiento`).

## 5. Correcciones aplicadas
- Se introdujeron prompts de corrección estrictos ("Recuerda que estamos en Dominio Puro, Pydantic está prohibido aquí, usa @property y genéricos de Python").
- Se forzó a la IA a auditar la suite de tests (ver `368578c2...`) para detectar redundancias, falsos positivos y asegurar que las transiciones de estado fallaran correctamente.

## 6. Cómo se validó
- Cada iteración con IA fue validada mediante la ejecución independiente de `pytest`. Si los tests pasaban y la revisión manual confirmaba la pureza de dependencias, la fase se daba por terminada.
- Se usó el comando `tree` o herramientas de inspección del flujo de dependencias para garantizar visualmente que `app/dominio` no importara nada de `app/infraestructura`.

## 7. Resultado de la fase
Una sinergia altamente productiva: se logró construir una arquitectura compleja (Hexagonal + DDD), con más de 380 tests unitarios y de integración robustos, en un tiempo que manualmente habría sido inviable para este alcance, sin ceder en calidad ni conocimiento técnico del código resultante (el código generado fue comprendido y justificado).

## 8. Lecciones aprendidas
- La IA es excelente escribiendo código, pero sin una arquitectura predefinida por el humano, tiende al código espagueti o monolítico.
- Desacoplar el dominio primero es la mejor manera de aprovechar a la IA: una vez que el objeto puro está de acuerdo a las reglas de negocio, la IA genera los tests y los casos de uso a la perfección.

## 9. Estado de cierre
Fase metodológica finalizada. La estrategia demostró ser efectiva y se mantendrá como metodología estándar para proyectos futuros.
