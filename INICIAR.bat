@echo off
chcp 65001 >nul 2>&1
title Mesa de Ayuda - Iniciando...
cd /d "%~dp0"

echo.
echo ══════════════════════════════════════════════════════
echo   MESA DE AYUDA - Inicio automatico
echo ══════════════════════════════════════════════════════
echo.

:: ── 1. Verificar Docker ─────────────────────────────────
echo [1/6] Verificando Docker...
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Docker no esta corriendo.
    echo Abri Docker Desktop y volve a ejecutar este archivo.
    pause
    exit /b 1
)
echo       OK - Docker esta corriendo

:: ── 2. Crear .env si no existe ──────────────────────────
echo [2/6] Verificando .env...
if not exist ".env" (
    (
        echo SECRET_KEY=clave-de-prueba-local-12345
        echo MONGODB_URL=mongodb://mongo:27017
        echo MONGODB_DB_NAME=mesa_de_ayuda
    ) > .env
    echo       OK - .env creado
) else (
    echo       OK - .env ya existe
)

:: ── 3. Levantar contenedores ────────────────────────────
echo [3/6] Levantando contenedores (esto puede tardar la primera vez)...
docker compose up -d --build
if %errorlevel% neq 0 (
    echo ERROR: Fallo docker compose up
    pause
    exit /b 1
)
echo       OK - Contenedores levantados

:: ── 4. Esperar API ──────────────────────────────────────
echo [4/6] Esperando a que la API este lista...
set intentos=0
:esperar
set /a intentos+=1
if %intentos% gtr 30 (
    echo ERROR: La API no respondio en 60 segundos.
    echo Revisa los logs con: docker compose logs api
    pause
    exit /b 1
)
curl -sf http://localhost:8000/health >nul 2>&1
if %errorlevel% neq 0 (
    echo       Intento %intentos%/30 - esperando...
    timeout /t 2 /nobreak >nul
    goto esperar
)
echo       OK - API respondiendo en http://localhost:8000

:: ── 5. Crear usuarios de prueba ─────────────────────────
echo [5/6] Creando usuarios de prueba...

curl -sf -X POST http://localhost:8000/usuarios/ -H "Content-Type: application/json" -d "{\"nombre\":\"Ana Supervisora\",\"email\":\"supervisor@test.com\",\"rol\":\"supervisor\",\"password\":\"Test1234\"}" >nul 2>&1
echo       - supervisor@test.com

curl -sf -X POST http://localhost:8000/usuarios/ -H "Content-Type: application/json" -d "{\"nombre\":\"Carlos Operador\",\"email\":\"operador@test.com\",\"rol\":\"operador\",\"password\":\"Test1234\"}" >nul 2>&1
echo       - operador@test.com

curl -sf -X POST http://localhost:8000/usuarios/ -H "Content-Type: application/json" -d "{\"nombre\":\"Maria Tecnica\",\"email\":\"tecnico@test.com\",\"rol\":\"tecnico\",\"password\":\"Test1234\"}" >nul 2>&1
echo       - tecnico@test.com

curl -sf -X POST http://localhost:8000/usuarios/ -H "Content-Type: application/json" -d "{\"nombre\":\"Juan Solicitante\",\"email\":\"solicitante@test.com\",\"rol\":\"solicitante\",\"password\":\"Test1234\"}" >nul 2>&1
echo       - solicitante@test.com

echo       OK - Usuarios creados (si ya existian, se omitieron)

:: ── 6. Abrir navegador ──────────────────────────────────
echo [6/6] Abriendo Swagger UI...
start http://localhost:8000/docs

:: ── Resumen ─────────────────────────────────────────────
echo.
echo ══════════════════════════════════════════════════════
echo   APP LISTA - Swagger abierto en el navegador
echo ══════════════════════════════════════════════════════
echo.
echo   Password para todos: Test1234
echo.
echo   supervisor@test.com   (puede todo)
echo   operador@test.com     (gestiona requerimientos)
echo   tecnico@test.com      (resuelve requerimientos)
echo   solicitante@test.com  (crea requerimientos)
echo.
echo   Detener todo:   docker compose down
echo   Borrar datos:   docker compose down -v
echo.
echo ══════════════════════════════════════════════════════
echo   Podes cerrar esta ventana. La app sigue corriendo.
echo ══════════════════════════════════════════════════════
pause
