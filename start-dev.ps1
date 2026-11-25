<#
.SYNOPSIS
    Unified local development launcher for Q-Optimize (Backend + Frontend).

.DESCRIPTION
    Verifies backend Python .venv and frontend node_modules, launches the FastAPI
    backend in a dedicated PowerShell window on port 8000, and starts the Vite
    frontend development server in the current terminal.
#>
param (
    [int]$BackendPort = 8000
)

$ErrorActionPreference = "Stop"
$RootDir = Split-Path -Parent $MyInvocation.MyCommand.Path
if (-not $RootDir) {
    $RootDir = Get-Location
}

$BackendStart = Join-Path $RootDir "backend\start.ps1"
$FrontendDir = Join-Path $RootDir "frontend"

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "  Q-Optimize Full-Stack Development Launcher" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

if (-not (Test-Path $BackendStart)) {
    Write-Host "[ERROR] Missing backend startup script: $BackendStart" -ForegroundColor Red
    exit 1
}

if (-not (Test-Path (Join-Path $FrontendDir "node_modules"))) {
    Write-Host "[INFO] Installing frontend dependencies (npm install)..." -ForegroundColor Yellow
    npm install --prefix $FrontendDir
}

Write-Host "[INFO] Launching FastAPI Backend in a new PowerShell window (Port $BackendPort)..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-ExecutionPolicy", "Bypass", "-File", "`"$BackendStart`"", "-Port", "$BackendPort"

Write-Host "[INFO] Starting Vite Frontend Dev Server..." -ForegroundColor Green
Write-Host "  Backend API : http://localhost:$BackendPort/docs" -ForegroundColor Cyan
Write-Host "  Frontend UI : http://localhost:5173 (or next available port)" -ForegroundColor Cyan
Write-Host "----------------------------------------------------------" -ForegroundColor Gray

Set-Location $FrontendDir
npm run dev
