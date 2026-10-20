# Manual Training Script for Optical+SAR Cross-Modal Specialist
# SIH26167: Space Technology - ISRO
# Rule 2 Compliance: Human operator authorized execution only

$REPO_ROOT = (Resolve-Path "$PSScriptRoot\..\..").Path
Set-Location $REPO_ROOT

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "Optical + SAR Cross-Modal Specialist Training Pipeline" -ForegroundColor Cyan
Write-Host "SIH Problem Statement: SIH26167" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

$VENV_PYTHON = Join-Path $REPO_ROOT "backend\.venv\Scripts\python.exe"

if (-not (Test-Path $VENV_PYTHON)) {
    Write-Error "Virtual environment Python not found at $VENV_PYTHON"
    exit 1
}

# Run training
& $VENV_PYTHON -m backend.models.cross_modal.train_cross_modal `
    --epochs 3 `
    --batch_size 4 `
    --lr 0.0001

Write-Host "`nCross-Modal training process completed." -ForegroundColor Green
