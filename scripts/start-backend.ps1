<#
.SYNOPSIS
    Installs backend deps, seeds the database on first run, and starts the API.

.PARAMETER Port
    Port to serve the API on. Defaults to 8010 (matches frontend/.env's VITE_API_URL).

.PARAMETER Reload
    Pass to run uvicorn with --reload for local development.
#>
param(
    [int]$Port = 8010,
    [switch]$Reload
)
$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$backend = Join-Path $root "backend"

Push-Location $backend
try {
    python -m pip install -r requirements.txt
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

    if (-not (Test-Path (Join-Path $backend "cellmind.db"))) {
        Write-Host "No cellmind.db found - seeding sample data..."
        python seed.py
        if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    }

    if (-not (Test-Path (Join-Path $root "ml\artifacts\best_model.pt"))) {
        Write-Host "Note: ml/artifacts/best_model.pt not found yet - /cells/{id}/inspect and" -ForegroundColor Yellow
        Write-Host "/inference/predict will return 503 until you run scripts/train-model.ps1." -ForegroundColor Yellow
    }

    $uvicornArgs = @("-m", "uvicorn", "main:app", "--port", $Port)
    if ($Reload) { $uvicornArgs += "--reload" }

    Write-Host "Starting backend on http://localhost:$Port (docs at /docs)..."
    python @uvicornArgs
}
finally {
    Pop-Location
}
