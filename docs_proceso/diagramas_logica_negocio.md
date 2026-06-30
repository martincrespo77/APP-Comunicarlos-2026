# Lógica de Negocio — Mesa de Ayuda

A continuación se presentan los diagramas de **Flujo**, **Secuencia** y **Estado** para comprender el ciclo completo de uso de la aplicación desde cero.

## 1. Diagrama de Flujo (Paso a Paso)

Este diagrama muestra los pasos generales que toman los distintos actores en el sistema desde que se crean las cuentas hasta que un ticket es resuelto.

```mermaid
flowchart TD
    %% Definición de estilos
    classDef solicitante fill:#d1e7dd,stroke:#0f5132,stroke-width:2px;
    classDef operador fill:#cff4fc,stroke:#055160,stroke-width:2px;
    classDef tecnico fill:#fff3cd,stroke:#664d03,stroke-width:2px;
    classDef api fill:#f8d7da,stroke:#842029,stroke-width:2px;

    Inicio((Inicio)) --> R[1. Registrar Usuarios<br/>POST /usuarios]
    
    R --> S[Solicitante]:::solicitante
    R --> O[Operador]:::operador
    R --> T[Técnico]:::tecnico
    
    S --> S_AUTH[2. Autenticarse<br/>Obtener JWT]:::solicitante
    S_AUTH --> S_CREATE[3. Crear Incidente<br/>POST /requerimientos/incidentes]:::solicitante
    
    O --> O_AUTH[2. Autenticarse<br/>Obtener JWT]:::operador
    S_CREATE --> O_GET[4. Consultar Tickets Nuevos<br/>GET /requerimientos]:::operador
    O_AUTH --> O_GET
    O_GET --> O_ASIGNAR[5. Asignar Técnico<br/>POST /.../asignar]:::operador
    
    T --> T_AUTH[2. Autenticarse<br/>Obtener JWT]:::tecnico
    O_ASIGNAR --> T_GET[6. Consultar Asignaciones<br/>GET /requerimientos]:::tecnico
    T_AUTH --> T_GET
    T_GET --> T_INICIAR[7. Iniciar Trabajo<br/>POST /.../iniciar]:::tecnico
    T_INICIAR --> T_RESOLVER[8. Resolver Incidente<br/>POST /.../resolver]:::tecnico
```

## 2. Diagrama de Secuencia (Interacciones con la API)

Aquí puedes ver exactamente cómo interactúan los actores con los endpoints **GET** y **POST** de FastAPI a lo largo del tiempo.

```mermaid
sequenceDiagram
    autonumber
    actor Solicitante
    actor Operador
    actor Tecnico as Técnico
    participant API as FastAPI Backend
    
    Note over Solicitante, API: FASE 1: CREACIÓN DE USUARIO Y LOGIN
    Solicitante->>API: POST /usuarios (Datos de registro)
    API-->>Solicitante: 201 Created (ID de Usuario)
    Solicitante->>API: POST /usuarios/autenticar (Email y Password)
    API-->>Solicitante: 200 OK (Token JWT)
    
    Note over Solicitante, API: FASE 2: CREACIÓN DEL TICKET
    Solicitante->>API: POST /requerimientos/incidentes (Envía Token JWT)
    API-->>Solicitante: 201 Created (ID de Incidente)
    
    Note over Operador, API: FASE 3: ASIGNACIÓN
    Operador->>API: GET /requerimientos (Buscar tickets "NUEVO")
    API-->>Operador: 200 OK (Lista de tickets)
    Operador->>API: POST /requerimientos/{id}/asignar (ID del Técnico)
    API-->>Operador: 204 No Content
    
    Note over Tecnico, API: FASE 4: RESOLUCIÓN
    Tecnico->>API: GET /requerimientos (Buscar mis asignaciones)
    API-->>Tecnico: 200 OK (Lista de tickets)
    Tecnico->>API: POST /requerimientos/{id}/iniciar
    API-->>Tecnico: 204 No Content
    Tecnico->>API: POST /requerimientos/{id}/resolver
    API-->>Tecnico: 204 No Content
```

## 3. Diagrama de Estados (Ciclo de Vida del Ticket)

El requerimiento pasa por transiciones de estado altamente controladas en el código (reglas de dominio). Solo ciertos roles pueden gatillar estas transiciones.

```mermaid
stateDiagram-v2
    [*] --> NUEVO: Solicitante crea ticket
    
    NUEVO --> ASIGNADO: Operador asigna técnico
    
    ASIGNADO --> EN_PROGRESO: Técnico inicia trabajo
    
    EN_PROGRESO --> RESUELTO: Técnico resuelve ticket
    
    RESUELTO --> REABIERTO: Operador o Solicitante<br/>agrega un comentario
    
    REABIERTO --> EN_PROGRESO: Técnico reinicia trabajo
    
    ASIGNADO --> ASIGNADO: Técnico deriva a otro técnico
    EN_PROGRESO --> ASIGNADO: Técnico deriva a otro técnico
    REABIERTO --> ASIGNADO: Técnico deriva a otro técnico
```
