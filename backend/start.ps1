<#
.SYNOPSIS
    Starts the Q-Optimize FastAPI backend server with automatic environment detection.

.DESCRIPTION
    Reliably locates and activates the Python virtual environment (.venv), verifies
    core dependencies, configures PYTHONPATH, and launches the FastAPI application.

.PARAMETER HostName
    The host IP address to bind (default: 127.0.0.1).

.PARAMETER Port
    The network port to listen on (default: 8000).

.PARAMETER NoReload
    Disable auto-reload mode (useful for production/benchmark runs).
#>
param (
    [string]$HostName = "127.0.0.1",
    [int]$Port = 8000,
    [switch]$NoReload
)

$ErrorActionPreference = "Stop"

# 1. Determine script and project paths reliably
$BackendDir = Split-Path -Parent $MyInvocation.MyCommand.Path
if (-not $BackendDir) {
    $BackendDir = Get-Location
}
$RootDir = Split-Path -Parent $BackendDir

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "  Q-Optimize Backend Startup Utility" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "[INFO] Backend directory : $BackendDir"
Write-Host "[INFO] Root directory    : $RootDir"

# 2. Locate virtual environment (.venv)
$VenvCandidatePaths = @(
    (Join-Path $BackendDir ".venv"),
    (Join-Path $RootDir ".venv"),
    (Join-Path $BackendDir "venv"),
    (Join-Path $RootDir "venv")
)

$VenvDir = $null
foreach ($path in $VenvCandidatePaths) {
    if (Test-Path (Join-Path $path "Scripts\python.exe")) {
        $VenvDir = $path
        break
    }
}

if (-not $VenvDir) {
    Write-Host "[ERROR] No valid Python virtual environment found!" -ForegroundColor Red
    Write-Host "Checked paths:" -ForegroundColor Yellow
    foreach ($p in $VenvCandidatePaths) {
        Write-Host "  - $p" -ForegroundColor Gray
    }
    Write-Host ""
    Write-Host "To create and configure the virtual environment, run:" -ForegroundColor Yellow
    Write-Host "  cd `"$BackendDir`"" -ForegroundColor White
    Write-Host "  py -3.12 -m venv .venv" -ForegroundColor White
    Write-Host "  .\.venv\Scripts\Activate.ps1" -ForegroundColor White
    Write-Host "  pip install -r requirements.txt" -ForegroundColor White
    exit 1
}

Write-Host "[INFO] Virtual env found : $VenvDir" -ForegroundColor Green

# 3. Activate virtual environment
$ActivateScript = Join-Path $VenvDir "Scripts\Activate.ps1"
if (Test-Path $ActivateScript) {
    Write-Host "[INFO] Activating virtual environment..." -ForegroundColor Gray
    & $ActivateScript
} else {
    # Fallback: prepend virtual environment Scripts to PATH
    $env:PATH = "$((Join-Path $VenvDir 'Scripts'));$env:PATH"
    $env:VIRTUAL_ENV = $VenvDir
}

# 4. Display Python executable and version
$PythonExe = Join-Path $VenvDir "Scripts\python.exe"
$PythonVersion = & $PythonExe --version 2>&1
Write-Host "[INFO] Python Executable : $PythonExe" -ForegroundColor Cyan
Write-Host "[INFO] Python Version    : $PythonVersion" -ForegroundColor Cyan

# 5. Configure PYTHONPATH
$ExistingPythonPath = $env:PYTHONPATH
if ($ExistingPythonPath) {
    $env:PYTHONPATH = "$RootDir;$BackendDir;$ExistingPythonPath"
} else {
    $env:PYTHONPATH = "$RootDir;$BackendDir"
}

# 6. Verify required dependencies
Write-Host "[INFO] Verifying backend dependencies..." -ForegroundColor Gray
$CheckImportsScript = @"
import sys
required = [
    'fastapi', 'uvicorn', 'pydantic', 'pydantic_settings',
    'qiskit', 'scipy', 'sklearn', 'pymongo', 'motor',
    'dotenv', 'email_validator', 'httpx'
]
missing = []
for pkg in required:
    try:
        __import__(pkg)
    except ImportError:
        missing.append(pkg)

if missing:
    print(','.join(missing))
    sys.exit(1)
sys.exit(0)
"@

$MissingPackages = & $PythonExe -c $CheckImportsScript 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Missing required dependencies: $MissingPackages" -ForegroundColor Red
    Write-Host "Please install them via:" -ForegroundColor Yellow
    Write-Host "  & `"$PythonExe`" -m pip install -r `"$BackendDir\requirements.txt`"" -ForegroundColor White
    exit 1
}
Write-Host "[INFO] Dependencies check passed." -ForegroundColor Green

# 7. Start FastAPI server
$ReloadFlag = if ($NoReload) { "" } else { "--reload" }
Write-Host "----------------------------------------------------------" -ForegroundColor Gray
Write-Host "Starting Q-Optimize Backend on http://$HostName`:$Port" -ForegroundColor Green
Write-Host "API Documentation: http://$HostName`:$Port/docs" -ForegroundColor Cyan
Write-Host "Health Check     : http://$HostName`:$Port/health/live" -ForegroundColor Cyan
Write-Host "Press Ctrl+C to terminate." -ForegroundColor Yellow
Write-Host "----------------------------------------------------------" -ForegroundColor Gray

Set-Location $BackendDir

if ($ReloadFlag) {
    & $PythonExe -m uvicorn app.main:app --host $HostName --port $Port --reload
} else {
    & $PythonExe -m uvicorn app.main:app --host $HostName --port $Port
}
