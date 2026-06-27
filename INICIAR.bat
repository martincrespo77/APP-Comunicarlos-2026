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
echo [1/7] Verificando Docker...
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Docker no esta corriendo.
    echo Abri Docker Desktop y volve a ejecutar este archivo.
    pause
    exit /b 1
)
echo       OK - Docker esta corriendo

:: ── 2. Crear .env si no existe ──────────────────────────
echo [2/7] Verificando .env...
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
echo [3/7] Levantando contenedores (esto puede tardar la primera vez)...
docker compose up -d --build
if %errorlevel% neq 0 (
    echo ERROR: Fallo docker compose up
    pause
    exit /b 1
)
echo       OK - Contenedores levantados

:: ── 4. Esperar API ──────────────────────────────────────
echo [4/7] Esperando a que la API este lista...
set intentos=0
:esperar
set /a intentos+=1
if %intentos% gtr 30 (
    echo ERROR: La API no respondio en 60 segundos.
    echo Revisa los logs con: docker compose logs api
    pause
    exit /b 1
)
curl.exe -sf http://localhost:8000/health >nul 2>&1
if %errorlevel% neq 0 (
    echo       Intento %intentos%/30 - esperando...
    timeout /t 2 /nobreak >nul
    goto esperar
)
echo       OK - API respondiendo en http://localhost:8000

:: ── 5. Crear usuarios de prueba ─────────────────────────
echo [5/7] Creando usuarios de prueba...

curl.exe -sf -X POST http://localhost:8000/usuarios/ -H "Content-Type: application/json" -d "{\"nombre\":\"Ana Supervisora\",\"email\":\"ana@comunicarlos.com.ar\",\"rol\":\"supervisor\",\"password\":\"Test1234\"}" >nul 2>&1
echo       - ana@comunicarlos.com.ar (supervisor)

curl.exe -sf -X POST http://localhost:8000/usuarios/ -H "Content-Type: application/json" -d "{\"nombre\":\"Carlos Operador\",\"email\":\"carlos@comunicarlos.com.ar\",\"rol\":\"operador\",\"password\":\"Test1234\"}" >nul 2>&1
echo       - carlos@comunicarlos.com.ar (operador)

curl.exe -sf -X POST http://localhost:8000/usuarios/ -H "Content-Type: application/json" -d "{\"nombre\":\"Maria Tecnica\",\"email\":\"maria@comunicarlos.com.ar\",\"rol\":\"tecnico\",\"password\":\"Test1234\"}" >nul 2>&1
echo       - maria@comunicarlos.com.ar (tecnico)

curl.exe -sf -X POST http://localhost:8000/usuarios/ -H "Content-Type: application/json" -d "{\"nombre\":\"Juan Solicitante\",\"email\":\"solicitante@test.com\",\"rol\":\"solicitante\",\"password\":\"Test1234\"}" >nul 2>&1
echo       - solicitante@test.com (solicitante)

echo       OK - Usuarios creados (si ya existian, se omitieron)

:: ── 6. Abrir Aplicacion ─────────────────────────────────
echo [6/7] Abriendo aplicacion en el navegador...
start http://localhost:8000/app/

:: ── 7. Opcion HTTPS ─────────────────────────────────────
echo [7/7] HTTPS...
if exist "infra\certs\localhost.pem" (
    echo       Certificados encontrados en infra\certs\
    echo       Para usar HTTPS con Caddy, ejecuta:
    echo       docker compose -f docker-compose.yml -f docker-compose.https.yml up -d
) else (
    echo       Sin certificados. Para habilitar HTTPS:
    echo       1. Instala mkcert: https://github.com/FiloSottile/mkcert
    echo       2. mkcert -install
    echo       3. mkcert -cert-file infra\certs\localhost.pem -key-file infra\certs\localhost-key.pem localhost 127.0.0.1
    echo       4. docker compose -f docker-compose.yml -f docker-compose.https.yml up -d
)

:: ── Resumen ─────────────────────────────────────────────
echo.
echo ══════════════════════════════════════════════════════
echo   APP LISTA
echo ══════════════════════════════════════════════════════
echo.  echo   APP (Frontend):  http://localhost:8000/app/echo   PORTAL:         http://localhost:8000
echo   Swagger UI:     http://localhost:8000/docs
echo   ReDoc:          http://localhost:8000/redoc
echo   UML:            http://localhost:8000/uml/
echo   Documentacion:  http://localhost:8000/documentacion/
echo.
echo   Password para todos: Test1234
echo   ─────────────────────────────────────────────────
echo   ana@comunicarlos.com.ar      (supervisor - puede todo)
echo   carlos@comunicarlos.com.ar   (operador)
echo   maria@comunicarlos.com.ar    (tecnico)
echo   solicitante@test.com         (solicitante)
echo.
echo   Detener:    docker compose down
echo   Borrar BD:  docker compose down -v
echo   HTTPS:      docker compose -f docker-compose.yml -f docker-compose.https.yml up -d
echo.
echo ══════════════════════════════════════════════════════
echo   Podes cerrar esta ventana. La app sigue corriendo.
echo ══════════════════════════════════════════════════════
pause
