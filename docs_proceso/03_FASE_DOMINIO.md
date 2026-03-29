# Fase 3: Dominio

## 1. Objetivo de la fase
Fundar las bases de la arquitectura Hexagonal modelando el problema exclusivo de negocio mediante el uso de Python Puro y patrones tácticos de Domain-Driven Design (DDD). Lograr un núcleo totalmente agnóstico de frameworks (ni dependencias HTTP ni ORMs).

## 2. Por qué arrancamos por el Dominio
Es la regla fundamental del Clean Architecture. Las políticas de mayor nivel (el corazón del negocio de reparación y soporte) nunca deben depender de políticas de menor nivel (como "guardar en base de datos" o "validar correos con Regex a través de web"). Si FastAPI desaparece, la regla que afirma que "Solo un Operador puede asignar técnicos" no debe mutar.

## 3. Cómo se modeló `Requerimiento`
El `Requerimiento` es el Aggregate Root. Todas las transiciones de estado (`iniciar_trabajo()`, `registrar_comentario()`, `derivar_a()`) se disparan obligatoriamente llamando a sus propios métodos. La entidad garantiza por sí sola que nadie derive un ticket ya cerrado. Al mutar, encola internamente  en su lista _eventos_dominio objetos que registrarán una traza.

## 4. Por qué `Incidente` y `Solicitud` separados
Aunque a nivel de Base de Datos comparten muchos metadatos, a nivel Dominio actúan polimórficamente bajo el patrón State o Strategy. Por ejemplo, un Incidente tiene asociado un estricto `nivel_urgencia` (Baja, Media, Crítica) y su propio cálculo temporal, mientras que en una Solicitud estándar, medir niveles catastróficos u horas exactas no concuerda con la lógica realista.

## 5. Separación modular: Usuarios, Notificaciones y Compartido
- **Usuarios**: Existe solo para determinar el perfil (Rol) y la actividad de la persona en el sistema. Nos dimos cuenta y evitamos poner contraseñas crudas o cifradas (Bcrypt) ya que validar hashes no es rol de un Dominio puro.
- **Notificaciones**: Utiliza el patrón _Observer_ puro, creando una "radio" (Despachador de Eventos) capaz de "oír" a las entidades que acaban de realizar algún acto importante (Ej., "Ticket Creado").
- **Compartido**: `RolUsuario` se aisló de forma que tanto Usuarios como los requerimientos (al verificar roles de autorización en metodos) puedan importar el Enum sin incurrir en dependencias circulares.

## 6. Correcciones y aprendizajes intermedios
- Exterminamos activamente cualquier `@validator` perezosamente portado de **Pydantic**. Aquellas validaciones fueron movidas a la raíz de la instancia (`__post_init__` o properties nativos) o a excepciones Custom creadas específicamente por negocio.
