# ─────────────────────────────────────────────────────────────────────────────
#  iniciar-y-probar.ps1 — Levanta la app con Docker y crea usuarios de prueba
#
#  Uso:   .\iniciar-y-probar.ps1
#  Requisitos: Docker Desktop corriendo
# ─────────────────────────────────────────────────────────────────────────────

$ErrorActionPreference = "Stop"
$API = "http://localhost:8000"

# ── Colores ──────────────────────────────────────────────────────────────────
function Write-Step($msg) { Write-Host "`n>> $msg" -ForegroundColor Cyan }
function Write-Ok($msg)   { Write-Host "   OK: $msg" -ForegroundColor Green }
function Write-Err($msg)  { Write-Host "   ERROR: $msg" -ForegroundColor Red }
function Write-Info($msg)  { Write-Host "   $msg" -ForegroundColor Yellow }

# ── 1. Verificar que Docker esté corriendo ───────────────────────────────────
Write-Step "Verificando Docker..."
try {
    docker info *> $null
    Write-Ok "Docker esta corriendo"
} catch {
    Write-Err "Docker no esta corriendo. Abri Docker Desktop y volve a ejecutar."
    exit 1
}

# ── 2. Crear .env si no existe ───────────────────────────────────────────────
Write-Step "Verificando archivo .env..."
if (-not (Test-Path ".env")) {
    @"
SECRET_KEY=clave-de-prueba-local-12345
MONGODB_URL=mongodb://mongo:27017
MONGODB_DB_NAME=mesa_de_ayuda
"@ | Set-Content -Path ".env" -Encoding UTF8
    Write-Ok "Archivo .env creado"
} else {
    Write-Ok "Archivo .env ya existe"
}

# ── 3. Levantar contenedores ─────────────────────────────────────────────────
Write-Step "Levantando contenedores con docker-compose..."
docker compose up -d --build

if ($LASTEXITCODE -ne 0) {
    Write-Err "Fallo docker compose up"
    exit 1
}
Write-Ok "Contenedores levantados"

# ── 4. Esperar a que la API responda ─────────────────────────────────────────
Write-Step "Esperando a que la API este lista..."
$maxIntentos = 30
$intento = 0
$lista = $false

while ($intento -lt $maxIntentos) {
    $intento++
    try {
        $resp = Invoke-RestMethod -Uri "$API/health" -Method GET -TimeoutSec 3
        if ($resp.status -eq "ok") {
            $lista = $true
            break
        }
    } catch {
        # API aun no responde
    }
    Write-Host "   Intento $intento/$maxIntentos - esperando..." -ForegroundColor Gray
    Start-Sleep -Seconds 2
}

if (-not $lista) {
    Write-Err "La API no respondio despues de $($maxIntentos * 2) segundos."
    Write-Info "Revisa los logs con: docker compose logs api"
    exit 1
}
Write-Ok "API respondiendo en $API"

# ── 5. Crear usuarios de prueba ──────────────────────────────────────────────
Write-Step "Creando usuarios de prueba..."

$usuarios = @(
    @{ nombre = "Ana Supervisora";  email = "supervisor@test.com";  rol = "supervisor";   password = "Test1234" }
    @{ nombre = "Carlos Operador";  email = "operador@test.com";    rol = "operador";     password = "Test1234" }
    @{ nombre = "Maria Tecnica";    email = "tecnico@test.com";     rol = "tecnico";      password = "Test1234" }
    @{ nombre = "Juan Solicitante"; email = "solicitante@test.com"; rol = "solicitante";  password = "Test1234" }
)

foreach ($u in $usuarios) {
    $body = $u | ConvertTo-Json
    try {
        $resp = Invoke-RestMethod -Uri "$API/usuarios/" -Method POST `
            -Body $body -ContentType "application/json" -TimeoutSec 10
        Write-Ok "$($u.rol): $($u.email) (id: $($resp.id))"
    } catch {
        $status = $_.Exception.Response.StatusCode.value__
        if ($status -eq 409) {
            Write-Info "$($u.rol): $($u.email) ya existe (409 Conflict)"
        } else {
            Write-Err "$($u.rol): $($u.email) - Status $status - $_"
        }
    }
}

# ── 6. Obtener token de ejemplo (supervisor) ─────────────────────────────────
Write-Step "Obteniendo token de prueba (supervisor)..."
try {
    $loginBody = @{ email = "supervisor@test.com"; password = "Test1234" } | ConvertTo-Json
    $tokenResp = Invoke-RestMethod -Uri "$API/usuarios/autenticar" -Method POST `
        -Body $loginBody -ContentType "application/json" -TimeoutSec 10
    $token = $tokenResp.access_token
    Write-Ok "Token obtenido"
} catch {
    Write-Err "No se pudo autenticar: $_"
    $token = $null
}

# ── 7. Resumen final ─────────────────────────────────────────────────────────
Write-Host ""
Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Magenta
Write-Host "  APP MESA DE AYUDA - LISTA PARA PROBAR" -ForegroundColor Magenta
Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Magenta
Write-Host ""
Write-Host "  Swagger UI:   $API/docs" -ForegroundColor White
Write-Host "  ReDoc:        $API/redoc" -ForegroundColor White
Write-Host "  Health:       $API/health" -ForegroundColor White
Write-Host ""
Write-Host "  CREDENCIALES DE PRUEBA (password: Test1234 para todos):" -ForegroundColor Yellow
Write-Host "  ─────────────────────────────────────────────────────" -ForegroundColor Gray
Write-Host "  Supervisor:   supervisor@test.com" -ForegroundColor White
Write-Host "  Operador:     operador@test.com" -ForegroundColor White
Write-Host "  Tecnico:      tecnico@test.com" -ForegroundColor White
Write-Host "  Solicitante:  solicitante@test.com" -ForegroundColor White
Write-Host ""

if ($token) {
    Write-Host "  TOKEN SUPERVISOR (para copiar y pegar en Swagger):" -ForegroundColor Yellow
    Write-Host "  ─────────────────────────────────────────────────────" -ForegroundColor Gray
    Write-Host "  Bearer $token" -ForegroundColor Green
    Write-Host ""
}

Write-Host "  COMANDOS UTILES:" -ForegroundColor Yellow
Write-Host "  ─────────────────────────────────────────────────────" -ForegroundColor Gray
Write-Host "  Ver logs:       docker compose logs -f api" -ForegroundColor White
Write-Host "  Detener todo:   docker compose down" -ForegroundColor White
Write-Host "  Borrar datos:   docker compose down -v" -ForegroundColor White
Write-Host ""

# ── 8. Abrir navegador en Swagger ────────────────────────────────────────────
$abrir = Read-Host "Abrir Swagger en el navegador? (s/n)"
if ($abrir -eq "s" -or $abrir -eq "S") {
    Start-Process "$API/docs"
}
