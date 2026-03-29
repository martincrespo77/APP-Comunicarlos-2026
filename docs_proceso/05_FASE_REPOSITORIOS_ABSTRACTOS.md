# Fase 5: Repositorios Abstractos

## 1. Objetivo de la fase
Definir los contratos mediante los cuales la Aplicación (y sus Entidades puras) interactuarán con sistemas externos de memoria o bases de datos, utilizando las abstracciones del Principio de Inversión de Dependencias (la 'D' en SOLID).

## 2. Por qué se crearon contratos antes de infraestructura
Para "proteger" a la capa de servicios. Un servicio (`RequerimientoService`) debe pedirle a algo externo "búscame el ID 4". Ese servicio NO debe saber si ese ticket está almacenado en SQLite, un archivo en la memoria del PC o un caché global en la red; su código se basará en contratos e interfaces abstractas. 

## 3. Qué interfaces se definieron
Dentro de la carpeta de dominio de nuestros módulos, se dictó la existencia de clases usando `abc.ABC` de Python:
- `RequerimientoRepository(ABC)`: con métodos `obtener_por_id()`, `guardar()`, y `listar()`.
- `UsuarioRepository(ABC)`: con métodos básicos idénticos, más métodos vitales directos como `verificar_existencia_por_email()`.

## 4. Por qué el método `guardar()` se diseñó tipo "upsert"
Al nivel de abstracción presente, a nuestra clase servicio no le "importa" si el ticket creado es nuevo (una inserción global) o si provino de base de datos e hizo una transición menor a 'Resuelto' (una mera actualización o parche). Exigimos entonces de contrato a un adaptador subyacente que maneje de forma universal la intención de "asegurar el guardado", reduciendo variables temporales en los Casos de Uso.

## 5. Resultado de la fase
El aislamiento es real. En la Fase 6 (Servicios), hemos inyectado clases simuladas "RequerimientoRepositoryFake" para poder hacer tests en tiempo récord operando contra simples subdiccionarios en RAM. Ese es el verdadero éxito del Repositorio Abstracto.
