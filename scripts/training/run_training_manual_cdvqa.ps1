# Manual Training Script for CDVQA (Change-Based Visual Question Answering)
# SIH26167: Space Technology - ISRO
# Rule 2 Compliance: Human operator authorized execution only

$REPO_ROOT = (Resolve-Path "$PSScriptRoot\..\..").Path
Set-Location $REPO_ROOT

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "CDVQA Specialist Training Pipeline" -ForegroundColor Cyan
Write-Host "SIH Problem Statement: SIH26167" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

$VENV_PYTHON = Join-Path $REPO_ROOT "backend\.venv\Scripts\python.exe"

if (-not (Test-Path $VENV_PYTHON)) {
    Write-Error "Virtual environment Python not found at $VENV_PYTHON"
    exit 1
}

# Run training
& $VENV_PYTHON -m backend.models.cdvqa.train_cdvqa `
    --annotations_dir datasets/04_CDVQA/CDVQA-main `
    --images_dir datasets/04_CDVQA/images `
    --split Train `
    --epochs 3 `
    --batch_size 4 `
    --lr 0.0001

Write-Host "`nCDVQA training process completed." -ForegroundColor Green
