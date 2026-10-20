# Astra AI — Manual RSVQA Training & Evaluation Script
# SIH26167 Requirement: Single-Image Remote-Sensing VQA
#
# HARD INVARIANT: The AI agent prepares the pipeline and verifies sanity checks.
# Full multi-epoch training must be initiated manually by the human operator.

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host " Astra AI — Remote-Sensing VQA Training Pipeline" -ForegroundColor Green
Write-Host " Dataset: RSVQA-LR (77k train, 57k val, 33k test questions)" -ForegroundColor Yellow
Write-Host "==========================================================" -ForegroundColor Cyan

$VENV_PYTHON = ".\backend\.venv\Scripts\python.exe"

# 1. Quick Sanity Verification (0 backward passes, 0 epochs)
Write-Host "`n[Step 1/2] Running Pre-Flight Sanity Verification..." -ForegroundColor Magenta
& $VENV_PYTHON -m backend.models.rsvqa.train_rsvqa --sanity_check_only

if ($LASTEXITCODE -ne 0) {
    Write-Host "Sanity check failed! Aborting." -ForegroundColor Red
    exit 1
}

# 2. Production Training Command (Ready for Human Launch)
Write-Host "`n[Step 2/2] Ready for Manual Training." -ForegroundColor Green
Write-Host "To start full training manually, run:" -ForegroundColor White
Write-Host @"
& $VENV_PYTHON -m backend.models.rsvqa.train_rsvqa ``
  --annotations_dir datasets/06_RSVQA/annotations ``
  --images_dir datasets/06_RSVQA/Images_LR ``
  --output_dir backend/models/rsvqa/checkpoints ``
  --epochs 5 ``
  --batch_size 8 ``
  --lr 0.0001
"@ -ForegroundColor Yellow

Write-Host "`nEvaluation Command:" -ForegroundColor White
Write-Host @"
& $VENV_PYTHON -m backend.models.rsvqa.evaluate_rsvqa ``
  --annotations_dir datasets/06_RSVQA/annotations ``
  --images_dir datasets/06_RSVQA/Images_LR ``
  --split test ``
  --sample_limit 500 ``
  --output_json backend/models/rsvqa/eval_results.json
"@ -ForegroundColor Cyan
