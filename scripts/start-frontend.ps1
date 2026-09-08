<#
.SYNOPSIS
    Installs frontend deps (if needed) and starts the Vite dev server.
#>
$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$frontend = Join-Path $root "frontend"

Push-Location $frontend
try {
    if (-not (Test-Path (Join-Path $frontend "node_modules"))) {
        Write-Host "No node_modules found - running npm install..."
        npm install
        if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    }

    npm run dev
}
finally {
    Pop-Location
}
