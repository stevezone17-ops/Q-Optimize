<#
.SYNOPSIS
    Root-level shortcut to start the Q-Optimize FastAPI backend server.

.PARAMETER HostName
    The host IP address to bind (default: 127.0.0.1).

.PARAMETER Port
    The network port to listen on (default: 8000).

.PARAMETER NoReload
    Disable auto-reload mode.
#>
param (
    [string]$HostName = "127.0.0.1",
    [int]$Port = 8000,
    [switch]$NoReload
)

$RootDir = Split-Path -Parent $MyInvocation.MyCommand.Path
if (-not $RootDir) {
    $RootDir = Get-Location
}
$BackendStart = Join-Path $RootDir "backend\start.ps1"

if (-not (Test-Path $BackendStart)) {
    Write-Host "[ERROR] Could not find backend startup script at: $BackendStart" -ForegroundColor Red
    exit 1
}

$params = @{
    HostName = $HostName
    Port     = $Port
}
if ($NoReload) {
    $params["NoReload"] = $true
}

& $BackendStart @params
