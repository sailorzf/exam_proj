# exam-system management script
param(
    [Parameter(Position=0)]
    [ValidateSet('start','stop','restart','status')]
    [string]$Action = 'start'
)

$BackendPort = 8000
$FrontendPort = 5173
$BackendDir = "$PSScriptRoot\backend"
$FrontendDir = "$PSScriptRoot\frontend"

function Kill-Port {
    param([int]$Port)
    $conns = netstat -ano | Select-String ":$Port .*LISTENING"
    if ($conns) {
        $pids = $conns | ForEach-Object { ($_ -split '\s+')[-1] } | Select-Object -Unique
        foreach ($pid in $pids) {
            Write-Host "  Killing PID $pid on port $Port" -ForegroundColor Yellow
            taskkill //F //PID $pid 2>$null
        }
        Start-Sleep -Seconds 1
    }
}

function Kill-Uvicorn {
    $procs = Get-Process -Name 'uvicorn' -ErrorAction SilentlyContinue
    if ($procs) {
        Write-Host "  Stopping uvicorn processes" -ForegroundColor Yellow
        Stop-Process -Name 'uvicorn' -Force -ErrorAction SilentlyContinue
        Start-Sleep -Seconds 1
    }
}

function Kill-Vite {
    # Kill node processes running vite (child of npx vite)
    $procs = Get-Process -Name 'node' -ErrorAction SilentlyContinue | Where-Object {
        $_.CommandLine -match 'vite' -or $_.MainWindowTitle -match 'vite'
    }
    if (-not $procs) {
        # Fallback: check port
        Kill-Port -Port $FrontendPort
    } else {
        Write-Host "  Stopping vite (node) processes" -ForegroundColor Yellow
        $procs | Stop-Process -Force -ErrorAction SilentlyContinue
        Start-Sleep -Seconds 1
    }
}

function Stop-Services {
    Write-Host "=== Stopping services ===" -ForegroundColor Cyan
    Kill-Uvicorn
    Kill-Port -Port $BackendPort
    Kill-Vite
    Kill-Port -Port $FrontendPort
    Write-Host "All services stopped." -ForegroundColor Green
}

function Start-Backend {
    Write-Host "=== Starting backend (port $BackendPort) ===" -ForegroundColor Cyan
    Push-Location $BackendDir
    $job = Start-Process -FilePath 'uvicorn' -ArgumentList 'main:app', '--reload', '--host', '0.0.0.0', '--port', $BackendPort.ToString() -NoNewWindow -PassThru
    Write-Host "  Backend PID: $($job.Id)" -ForegroundColor Green
    Pop-Location
    # Wait for ready
    Write-Host "  Waiting for backend..." -NoNewline
    for ($i = 0; $i -lt 30; $i++) {
        try {
            $r = Invoke-WebRequest -Uri "http://localhost:$BackendPort/docs" -TimeoutSec 1 -UseBasicParsing
            if ($r.StatusCode -eq 200) { Write-Host " OK" -ForegroundColor Green; return $true }
        } catch {}
        Start-Sleep -Seconds 1
        Write-Host '.' -NoNewline
    }
    Write-Host " TIMEOUT" -ForegroundColor Red
    return $false
}

function Start-Frontend {
    Write-Host "=== Starting frontend (port $FrontendPort) ===" -ForegroundColor Cyan
    Push-Location $FrontendDir
    # Clean vite cache
    $cacheDir = Join-Path $FrontendDir 'node_modules\.vite'
    if (Test-Path $cacheDir) { Remove-Item -Recurse -Force $cacheDir }
    $job = Start-Process -FilePath 'npx' -ArgumentList 'vite', '--port', $FrontendPort.ToString() -NoNewWindow -PassThru
    Write-Host "  Frontend PID: $($job.Id)" -ForegroundColor Green
    Pop-Location
    # Wait for ready
    Write-Host "  Waiting for frontend..." -NoNewline
    for ($i = 0; $i -lt 30; $i++) {
        try {
            $r = Invoke-WebRequest -Uri "http://localhost:$FrontendPort" -TimeoutSec 1 -UseBasicParsing
            if ($r.StatusCode -eq 200) { Write-Host " OK" -ForegroundColor Green; return $true }
        } catch {}
        Start-Sleep -Seconds 1
        Write-Host '.' -NoNewline
    }
    Write-Host " TIMEOUT" -ForegroundColor Red
    return $false
}

function Start-Services {
    $ok1 = Start-Backend
    $ok2 = Start-Frontend
    if ($ok1 -and $ok2) {
        Write-Host "`n=== All services started ===" -ForegroundColor Green
        Write-Host "  Backend:  http://localhost:$BackendPort"
        Write-Host "  Frontend: http://localhost:$FrontendPort"
    } else {
        Write-Host "`n=== Some services failed to start ===" -ForegroundColor Red
    }
}

function Show-Status {
    Write-Host "=== Service Status ===" -ForegroundColor Cyan
    $bp = netstat -ano | Select-String ":$BackendPort .*LISTENING"
    $fp = netstat -ano | Select-String ":$FrontendPort .*LISTENING"
    if ($bp) { Write-Host "  Backend ($BackendPort):  Running" -ForegroundColor Green } else { Write-Host "  Backend ($BackendPort):  Stopped" -ForegroundColor Red }
    if ($fp) { Write-Host "  Frontend ($FrontendPort): Running" -ForegroundColor Green } else { Write-Host "  Frontend ($FrontendPort): Stopped" -ForegroundColor Red }
}

switch ($Action) {
    'start'   { Start-Services }
    'stop'    { Stop-Services }
    'restart' { Stop-Services; Start-Sleep -Seconds 2; Start-Services }
    'status'  { Show-Status }
}
