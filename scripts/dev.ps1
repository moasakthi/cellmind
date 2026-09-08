<#
.SYNOPSIS
    Starts the backend and frontend together, each in its own PowerShell window.

.PARAMETER BackendPort
    Port for the backend API. Defaults to 8010 (matches frontend/.env's VITE_API_URL).
#>
param(
    [int]$BackendPort = 8010
)
$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot

Write-Host "Launching CellMind backend and frontend in separate windows..."

Start-Process powershell -ArgumentList @(
    "-NoExit", "-Command",
    "& '$(Join-Path $root 'scripts\start-backend.ps1')' -Port $BackendPort -Reload"
)
Start-Process powershell -ArgumentList @(
    "-NoExit", "-Command",
    "& '$(Join-Path $root 'scripts\start-frontend.ps1')'"
)

Write-Host "Backend:  http://localhost:$BackendPort/docs"
Write-Host "Frontend: http://localhost:5173 (Vite uses the next free port, e.g. 5174, if that's taken)"
