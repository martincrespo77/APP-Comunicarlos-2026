# Modelo de Dominio

## Shared Kernel

### `RolUsuario` (Enum)
Roles del sistema reconocidos por ambos bounded contexts:
- `SOLICITANTE` — crea requerimientos
- `OPERADOR` — asigna y gestiona
- `TECNICO` — resuelve
- `SUPERVISOR` — supervisa y puede reabrir

## Bounded Context: Usuarios

### Entidad `Usuario`
Representa un actor del sistema con rol fijo.

| Atributo | Tipo | Descripción |
|----------|------|-------------|
| `id` | str (UUID) | Identificador único |
| `nombre` | str | Nombre completo |
| `email` | str | Email (corporativo para operador/técnico) |
| `rol` | RolUsuario | Rol asignado |
| `password_hash` | str | Hash bcrypt (opaco al dominio) |
| `activo` | bool | Cuenta activa/desactivada |
| `fecha_creacion` | datetime | Registro |
| `ultimo_acceso` | datetime | Último login |

**Reglas de negocio:**
- Operadores y técnicos deben usar email `@comunicarlos.com.ar`
- Nombre y email no pueden estar vacíos
- Email debe contener `@`

## Bounded Context: Requerimientos

### Entidad `Requerimiento` (ABC — raíz de agregado)
Encapsula el ciclo de vida completo de un pedido de soporte.

**Subclases concretas:**
- `Incidente` — tiene `urgencia` (Critica/Importante/Menor) y `categoria_incidente`
- `Solicitud` — tiene `categoria_solicitud` (Alta/Baja servicio)

### Value Objects
- **`Comentario`** — inmutable, append-only
- **`Evento`** — auditoría inmutable de cada acción

### Ciclo de vida (estado)

```
ABIERTO → ASIGNADO → EN_PROGRESO → RESUELTO
                                      ↓
          ASIGNADO ← ──────── REABIERTO
```

Implementado como **Enum + diccionario de transiciones válidas**, verificado en cada cambio de estado.

## Notificaciones (Observer)

- `ObservadorRequerimiento` — interfaz ABC
- `DespachadorEventos` — despacha eventos a todos los observadores registrados
