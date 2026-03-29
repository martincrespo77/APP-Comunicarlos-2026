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
  -d '{"nombre":"Admin","apellido":"Sistema","email":"admin@test.com","password":"Pass1234!","rol":"supervisor"}'
```

Guardar el `id` del response.

### 3.2 Login (obtener token JWT)

```bash
curl -s -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@test.com","password":"Pass1234!"}'
```

Guardar el `access_token` del response. Usarlo como `TOKEN` en los siguientes pasos.

### 3.3 Crear usuario Técnico

```bash
curl -s -X POST http://localhost:8000/usuarios/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"nombre":"Juan","apellido":"Tecnico","email":"tecnico@test.com","password":"Pass1234!","rol":"tecnico"}'
```

### 3.4 Crear usuario Empleado

```bash
curl -s -X POST http://localhost:8000/usuarios/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"nombre":"Maria","apellido":"Empleada","email":"empleada@test.com","password":"Pass1234!","rol":"empleado"}'
```

### 3.5 Login como Empleado y crear Incidente

```bash
# Login empleado
curl -s -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"empleada@test.com","password":"Pass1234!"}'

# Crear incidente (usar token del empleado)
curl -s -X POST http://localhost:8000/requerimientos/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN_EMPLEADO" \
  -d '{"tipo":"incidente","titulo":"Se cayó el servidor","descripcion":"Error 500 en producción","categoria":"hardware","nivel_urgencia":"alta"}'
```

### 3.6 Asignar técnico (como Supervisor)

```bash
curl -s -X POST http://localhost:8000/requerimientos/{ID_REQUERIMIENTO}/asignar \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"tecnico_id":"ID_DEL_TECNICO"}'
```

### 3.7 Iniciar trabajo (como Técnico)

```bash
# Login técnico
curl -s -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"tecnico@test.com","password":"Pass1234!"}'

# Iniciar
curl -s -X POST http://localhost:8000/requerimientos/{ID_REQUERIMIENTO}/iniciar \
  -H "Authorization: Bearer $TOKEN_TECNICO"
```

### 3.8 Resolver (como Técnico)

```bash
curl -s -X POST http://localhost:8000/requerimientos/{ID_REQUERIMIENTO}/resolver \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN_TECNICO" \
  -d '{"nota_resolucion":"Servidor reiniciado y funcionando"}'
```

### 3.9 Listar requerimientos

```bash
curl -s http://localhost:8000/requerimientos/ \
  -H "Authorization: Bearer $TOKEN"
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
  -H "Authorization: Bearer $TOKEN"
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
- [ ] Crear supervisor, técnico y empleado exitosamente
- [ ] Login devuelve JWT válido
- [ ] Crear incidente como empleado
- [ ] Asignar técnico como supervisor
- [ ] Iniciar y resolver como técnico
- [ ] Listar muestra estado `resuelto` con eventos
- [ ] Datos persisten tras `docker compose restart api`
- [ ] `mongosh` muestra documentos en las colecciones
