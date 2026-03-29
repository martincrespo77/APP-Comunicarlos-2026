# Decisiones Técnicas Clave

Este documento centraliza todas las decisiones medulares que separan al proyecto de un simple sistema monolítico trivial (CRUD básico) volviéndolo una arquitectura profesional madura.

## 1. Dominio puro y erradicación de Pydantic
La más grande y costosa determinación inicial: las entidades y lógicas de valor operan 100% sobre Python O.O. puro. Nadie valida emails ni tamaños de string mediante regex en el Dominio usando constructores extraños; la entidad resguarda transiciones conceptuales.

## 2. Shared Kernel mínimo
Lograr una relación entre `Usuarios` y `Requerimientos` inyectando dependencia mínima y saludable sin referencias cíclicas, decantando la decisión simple pero efectiva sobre usar `RolUsuario` como enumerador en un directorio llamado "Compartido".

## 3. Observer para eventos ("Bajo Acoplamiento")
Centralizamos la matriz de notificaciones a un Bus de Observadores. Cuando el negocio transita "Iniciar" o "Resolver", su único trabajo es dejar el registro formal en array (Evento) pero el encargado de orquestar el aviso de correos a futuro es la inyección per-se del servicio ajeno al dominio.

## 4. Repositorios Abstractos Obligatorios (D.I.)
Cualquier interacción a sistemas de datos fue prohibida utilizando directamente librerías externas. La construcción de un sistema Interfaz que prometía `guardar` posibilitó falsear las validaciones creando test que requerían milisegundos ignorando transacciones IO bloqueantes del disco real.

## 5. Criptografía como detalle menor
Exiliar Bcrypt (Hash Password) y Librerías Criptográficas de autenticación (JWT) demostró control preciso separando el núcleo o corazón ("Yo soy juan nivel Técnico") del detalle banal y temporal externo informático ("Verifícame mediante criptografía cuántica").

## 6. De SQLite a MongoDB: la prueba de la arquitectura
El proyecto nació con SQLite como base embebida para facilitar el despliegue académico rápido. Posteriormente se migró completamente a MongoDB (pymongo), demostrando que la inversión de dependencias y los repositorios abstractos cumplieron su propósito: solo se reescribieron 7 archivos de infraestructura (`database.py`, `repo_usuarios.py`, `repo_requerimientos.py`, `deps.py`, `main.py`, `conftest.py`, `test_infraestructura.py`), se eliminó `modelos_orm.py`, y los 394 tests siguieron pasando sin modificaciones al dominio, servicios ni routers.

## 7. Bruno sobre plataformas pesadas Oauth
Decididos en el control absoluto y transparente del ciclo de vida de nuestra documentación, elegimos Bruno (sintaxis abierta) logrando exponer como código toda interacción de usuario al proyecto.
