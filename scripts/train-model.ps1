<#
.SYNOPSIS
    Builds the train/val/test split and trains the solar-panel fault classifier.
    Writes ml/artifacts/best_model.pt, label_map.json, and metrics.json.
#>
$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$ml = Join-Path $root "ml"

if (-not (Test-Path (Join-Path $root "training_data\Faulty_solar_panel"))) {
    Write-Error "training_data\Faulty_solar_panel not found - this pipeline needs the source images to train on."
    exit 1
}

Push-Location $ml
try {
    python -m pip install -r requirements.txt
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

    python split_dataset.py
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

    python train.py
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}
finally {
    Pop-Location
}
