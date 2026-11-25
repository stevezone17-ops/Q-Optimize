<#
.SYNOPSIS
    Unified local development launcher for Q-Optimize (Backend + Frontend).

.DESCRIPTION
    Verifies Python virtual environment and Node dependencies, then launches
    the FastAPI backend (port 8000) and React/Vite frontend dev server in
    separate PowerShell windows.
#>
param (
    [int]$BackendPort = 8000,
    [string]$BackendHost = "127.0.0.1"
)

$ErrorActionPreference = "Stop"
$RootDir = Split-Path -Parent $MyInvocation.MyCommand.Path
if (-not $RootDir) {
    $RootDir = Get-Location
}

$BackendDir = Join-Path $RootDir "backend"
$FrontendDir = Join-Path $RootDir "frontend"
$BackendVenvPython = Join-Path $BackendDir ".venv\Scripts\python.exe"
$BackendStartScript = Join-Path $BackendDir "start.ps1"

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "  Q-Optimize Full-Stack Local Development Launcher" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

if (-not (Test-Path $BackendVenvPython)) {
    Write-Host "[ERROR] Backend virtual environment not found at: $BackendDir\.venv" -ForegroundColor Red
    Write-Host "Run the following commands first:" -ForegroundColor Yellow
    Write-Host "  cd `"$BackendDir`"" -ForegroundColor White
    Write-Host "  py -3.12 -m venv .venv" -ForegroundColor White
    Write-Host "  .\.venv\Scripts\Activate.ps1" -ForegroundColor White
    Write-Host "  pip install -r requirements.txt" -ForegroundColor White
    exit 1
}

if (-not (Test-Path (Join-Path $FrontendDir "node_modules"))) {
    Write-Host "[INFO] frontend/node_modules not found. Running npm install..." -ForegroundColor Yellow
    Push-Location $FrontendDir
    npm install
    if ($LASTEXITCODE -ne 0) {
        Pop-Location
        Write-Host "[ERROR] npm install failed." -ForegroundColor Red
        exit 1
    }
    Pop-Location
}

Write-Host "[INFO] Launching FastAPI Backend on http://$BackendHost`:$BackendPort ..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-ExecutionPolicy", "Bypass", "-File", "`"$BackendStartScript`"", "-HostName", $BackendHost, "-Port", $BackendPort

Write-Host "[INFO] Launching Vite Frontend Dev Server..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location `"$FrontendDir`"; npm run dev"

Write-Host ""
Write-Host "Both servers are starting in separate windows:" -ForegroundColor Cyan
Write-Host "  - Backend API : http://$BackendHost`:$BackendPort" -ForegroundColor White
Write-Host "  - Swagger Docs: http://$BackendHost`:$BackendPort/docs" -ForegroundColor White
Write-Host "  - Frontend UI : http://localhost:5173 (or next available port)" -ForegroundColor White
