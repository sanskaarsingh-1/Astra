# Manual Training Script for LEVIR-CD Bi-Temporal Change Detection
# SIH26167: Space Technology - ISRO
# Rule 2 Compliance: Human operator authorized execution only

$REPO_ROOT = (Resolve-Path "$PSScriptRoot\..\..").Path
Set-Location $REPO_ROOT

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "LEVIR-CD Bi-Temporal Change Detection (BIT) Training" -ForegroundColor Cyan
Write-Host "SIH Problem Statement: SIH26167" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

$VENV_PYTHON = Join-Path $REPO_ROOT "backend\.venv\Scripts\python.exe"

if (-not (Test-Path $VENV_PYTHON)) {
    Write-Error "Virtual environment Python not found at $VENV_PYTHON"
    exit 1
}

# Run training
& $VENV_PYTHON -m backend.models.change_detection.train_change_detection `
    --data_dir datasets/05_LEVIR_CD `
    --output_dir backend/models/change_detection/checkpoints `
    --epochs 10 `
    --batch_size 4 `
    --lr 0.0001 `
    --img_size 256

Write-Host "`nTraining process completed. Checkpoints saved to backend/models/change_detection/checkpoints/" -ForegroundColor Green
