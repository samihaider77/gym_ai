# Starts GymAI locally: database (Docker), backend (port 8000) and frontend (first free of 3000-3002).
# First run installs everything. Use -Setup to force reinstall + migrations + seed.
param([switch]$Setup)

# Native tools (docker, uv, npm) write progress to stderr; check exit codes instead of failing on it.
$ErrorActionPreference = 'Continue'
function Check($what) { if ($LASTEXITCODE -ne 0) { Write-Host "`n$what failed." -ForegroundColor Red; exit 1 } }
$root = $PSScriptRoot
$backend = Join-Path $root 'backend'
$frontend = Join-Path $root 'frontend'
$python = Join-Path $backend '.venv\Scripts\python.exe'

function Step($text) { Write-Host "`n==> $text" -ForegroundColor Cyan }
function PortFree($port) {
    $client = New-Object Net.Sockets.TcpClient
    try { $client.Connect('127.0.0.1', $port); $false } catch { $true } finally { $client.Close() }
}

Step 'Starting PostgreSQL (Docker)'
docker compose -f (Join-Path $root 'docker-compose.yml') up -d db
Check 'Starting Docker (is Docker Desktop running?)'
Write-Host 'Waiting for the database to be ready...'
for ($i = 0; $i -lt 30; $i++) {
    docker exec gym_ai_postgres pg_isready -U gym_ai_user -d gym_ai_db *> $null
    if ($LASTEXITCODE -eq 0) { break }
    Start-Sleep -Seconds 1
}

$firstBackend = $Setup -or -not (Test-Path $python)
if ($firstBackend) {
    Step 'Installing backend dependencies'
    Push-Location $backend
    if (Get-Command uv -ErrorAction SilentlyContinue) {
        if (-not (Test-Path $python)) { uv venv .venv --python 3.12 }
        uv pip install -p $python -r requirements.txt
    } else {
        if (-not (Test-Path $python)) { python -m venv .venv }
        & $python -m pip install -r requirements.txt
    }
    Check 'Installing backend dependencies'
    Pop-Location
}

Step 'Applying database migrations'
Push-Location $backend
& $python -m alembic upgrade head
Check 'Database migration'
if ($firstBackend) {
    Step 'Seeding exercises'
    & $python scripts/seed_exercises.py
    & $python scripts/import_roman_urdu.py
}
Pop-Location

if ($Setup -or -not (Test-Path (Join-Path $frontend 'node_modules'))) {
    Step 'Installing frontend dependencies'
    Push-Location $frontend
    npm ci
    Check 'Installing frontend dependencies'
    Pop-Location
}

if (PortFree 8000) {
    Step 'Starting backend on http://localhost:8000'
    Start-Process powershell -WorkingDirectory $backend -ArgumentList '-NoExit', '-Command', "`$host.UI.RawUI.WindowTitle='GymAI backend'; & '$python' -m uvicorn app.main:app --reload --port 8000"
} else {
    Write-Host "`nPort 8000 is already in use, assuming the backend is running." -ForegroundColor Yellow
}

$port = @(3000, 3001, 3002, 3003) | Where-Object { PortFree $_ } | Select-Object -First 1
if (-not $port) { Write-Host 'Ports 3000-3003 are all busy. Free one and run again.' -ForegroundColor Red; exit 1 }
Step "Starting frontend on http://localhost:$port"
Start-Process powershell -WorkingDirectory $frontend -ArgumentList '-NoExit', '-Command', "`$host.UI.RawUI.WindowTitle='GymAI frontend'; npx next dev -p $port"

Write-Host "`nGymAI is starting. Open http://localhost:$port in a few seconds." -ForegroundColor Green
Write-Host 'Close the two new windows to stop it. The database keeps running in Docker (docker compose stop db).'
Start-Sleep -Seconds 6
Start-Process "http://localhost:$port"
