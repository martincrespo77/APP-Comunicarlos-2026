# Validación Docker + MongoDB Real

Guía paso a paso para validar que la aplicación funciona correctamente
con Docker Compose y MongoDB 7 real (no mongomock).

---

## Prerrequisitos

- Docker Desktop instalado y corriendo
- Puerto 8000 libre en el host
- Archivo `.env` creado a partir de `.env.example`

```bash
cp .env.example .env
# Editar .env: poner un SECRET_KEY real (mín. 32 caracteres)
# Ejemplo: SECRET_KEY=clave_super_secreta_para_desarrollo_local_1234
```

---

## 1. Levantar los servicios

```bash
docker compose up --build -d
```

Verificar que ambos contenedores están healthy:

```bash
docker compose ps
```

Resultado esperado: `mongo` y `api` en estado `Up (healthy)`.

---

## 2. Health Check

```bash
curl http://localhost:8000/health
```

Resultado esperado: `{"status":"ok"}` (HTTP 200)

---

## 3. Flujo Mínimo de Pruebas HTTP Críticas

### 3.1 Crear usuario Supervisor

```bash
curl -s -X POST http://localhost:8000/usuarios/ \
  -H "Content-Type: application/json" \
  -d '{"nombre":"Admin Sistema","email":"admin@comunicarlos.com.ar","password":"Pass1234!","rol":"supervisor"}'
```

Guardar el `id` del response.

### 3.2 Login (obtener token JWT de Supervisor)

```bash
curl -s -X POST http://localhost:8000/usuarios/autenticar \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@comunicarlos.com.ar","password":"Pass1234!"}'
```

Guardar el `access_token` del response. Usarlo como `TOKEN_SUPERVISOR` en los siguientes pasos.

### 3.3 Crear usuario Técnico (como Supervisor)

```bash
curl -s -X POST http://localhost:8000/usuarios/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN_SUPERVISOR" \
  -d '{"nombre":"Juan Tecnico","email":"tecnico@comunicarlos.com.ar","password":"Pass1234!","rol":"tecnico"}'
```

Guardar el `id` del técnico creado.

### 3.4 Crear usuario Operador (como Supervisor)

```bash
curl -s -X POST http://localhost:8000/usuarios/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN_SUPERVISOR" \
  -d '{"nombre":"Pedro Operador","email":"operador@comunicarlos.com.ar","password":"Pass1234!","rol":"operador"}'
```

### 3.5 Crear usuario Solicitante (como Supervisor)

```bash
curl -s -X POST http://localhost:8000/usuarios/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN_SUPERVISOR" \
  -d '{"nombre":"Maria Solicitante","email":"solicitante@test.com","password":"Pass1234!","rol":"solicitante"}'
```

Guardar el `id` del solicitante (María) creado.

### 3.6 Login como Solicitante y crear Incidente

```bash
# Login solicitante
curl -s -X POST http://localhost:8000/usuarios/autenticar \
  -H "Content-Type: application/json" \
  -d '{"email":"solicitante@test.com","password":"Pass1234!"}'

# Usar el access_token obtenido como TOKEN_SOLICITANTE.
# Crear incidente (usar el ID de solicitante retornado)
curl -s -X POST http://localhost:8000/requerimientos/incidentes \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN_SOLICITANTE" \
  -d '{"titulo":"Se cayó el servidor","descripcion":"Error 500 en producción en el nodo de red.","solicitante_id":"ID_DE_MARIA","urgencia":"critica","categoria":"servicio_inaccesible"}'
```

Guardar el `id` del incidente del response como `ID_REQUERIMIENTO`.

### 3.7 Asignar técnico (como Operador)

```bash
# Login operador
curl -s -X POST http://localhost:8000/usuarios/autenticar \
  -H "Content-Type: application/json" \
  -d '{"email":"operador@comunicarlos.com.ar","password":"Pass1234!"}'

# Usar el access_token obtenido como TOKEN_OPERADOR.
# Asignar técnico (usa el ID del técnico creado en el paso 3.3)
curl -s -X POST http://localhost:8000/requerimientos/{ID_REQUERIMIENTO}/asignar \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN_OPERADOR" \
  -d '{"tecnico_id":"ID_DEL_TECNICO"}'
```

### 3.8 Iniciar trabajo (como Técnico)

```bash
# Login técnico
curl -s -X POST http://localhost:8000/usuarios/autenticar \
  -H "Content-Type: application/json" \
  -d '{"email":"tecnico@comunicarlos.com.ar","password":"Pass1234!"}'

# Usar el access_token obtenido como TOKEN_TECNICO.
curl -s -X POST http://localhost:8000/requerimientos/{ID_REQUERIMIENTO}/iniciar \
  -H "Authorization: Bearer $TOKEN_TECNICO"
```

### 3.9 Resolver (como Técnico)

```bash
curl -s -X POST http://localhost:8000/requerimientos/{ID_REQUERIMIENTO}/resolver \
  -H "Authorization: Bearer $TOKEN_TECNICO"
```

### 3.10 Listar requerimientos (como Supervisor)

```bash
curl -s http://localhost:8000/requerimientos/ \
  -H "Authorization: Bearer $TOKEN_SUPERVISOR"
```

Verificar que el requerimiento aparece con estado `resuelto` y tiene eventos de auditoría.

---

## 4. Verificar persistencia

```bash
# Reiniciar solo la API (la data debe sobrevivir)
docker compose restart api
sleep 10

# Volver a consultar
curl -s http://localhost:8000/requerimientos/ \
  -H "Authorization: Bearer $TOKEN_SUPERVISOR"
```

El requerimiento creado debe seguir existiendo.

---

## 5. Verificar datos en MongoDB directo

```bash
docker compose exec mongo mongosh mesa_de_ayuda --eval "db.usuarios.countDocuments({})"
docker compose exec mongo mongosh mesa_de_ayuda --eval "db.requerimientos.countDocuments({})"
docker compose exec mongo mongosh mesa_de_ayuda --eval "db.requerimientos.find().pretty()"
```

---

## 6. Limpiar

```bash
docker compose down -v   # -v elimina el volumen mongo_data
```

---

## Checklist de validación

- [ ] `docker compose ps` muestra ambos servicios healthy
- [ ] `/health` responde 200
- [ ] Crear supervisor, técnico, operador y solicitante exitosamente
- [ ] Login devuelve JWT válido
- [ ] Crear incidente como solicitante
- [ ] Asignar técnico como operador
- [ ] Iniciar y resolver como técnico
- [ ] Listar muestra estado `resuelto` con eventos
- [ ] Datos persisten tras `docker compose restart api`
- [ ] `mongosh` muestra documentos en las colecciones
