# Astra AI — Manual RS-VLM Training & Evaluation Script
# SIH26167 Mandatory Requirement: Remote-Sensing VLM Adaptation on BigEarthNet.txt
#
# HARD INVARIANT: The AI agent prepares the pipeline and verifies sanity checks.
# Full training must be initiated manually by the human operator.

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host " Astra AI — Remote-Sensing VLM Training & Evaluation" -ForegroundColor Green
Write-Host " Dataset: BigEarthNet.txt (464k pairs, 9.6M texts)" -ForegroundColor Yellow
Write-Host " Base Model: Salesforce/blip-image-captioning-base (Local / 990MB)" -ForegroundColor Yellow
Write-Host "==========================================================" -ForegroundColor Cyan

$VENV_PYTHON = ".\backend\.venv\Scripts\python.exe"

# 1. Quick Sanity Verification (0 backward passes, 0 epochs)
Write-Host "`n[Step 1/3] Running Pre-Flight Sanity Verification..." -ForegroundColor Magenta
& $VENV_PYTHON -m backend.models.remote_sensing_vlm.train_vlm_lora --sanity_check_only

if ($LASTEXITCODE -ne 0) {
    Write-Host "Sanity check failed! Aborting." -ForegroundColor Red
    exit 1
}

# 2. Calibrated 1000-Step Training Command (Includes responsive tqdm progress bar)
Write-Host "`n[Step 2/3] Calibrated Training (1,000 steps = 8,000 samples, ~4.5 mins on RTX 5060):" -ForegroundColor Green
Write-Host @"
& $VENV_PYTHON -m backend.models.remote_sensing_vlm.train_vlm_lora ``
  --parquet_path datasets/02_BigEarthNet_txt/BigEarthNet.txt/BigEarthNet.txt.parquet ``
  --images_dir datasets/processed/bigearthnet_resnet50_full ``
  --output_dir backend/models/remote_sensing_vlm/checkpoints ``
  --base_model Salesforce/blip-image-captioning-base ``
  --epochs 1 ``
  --batch_size 8 ``
  --max_steps 1000 ``
  --lr 0.0002 ``
  --lora_r 16 ``
  --lora_alpha 32
"@ -ForegroundColor Yellow

# 3. Benchmark Accuracy Evaluation Command
Write-Host "`n[Step 3/3] Benchmark Evaluation (Calculates Exact Match % and Substring %):" -ForegroundColor Green
Write-Host @"
& $VENV_PYTHON -m backend.models.remote_sensing_vlm.evaluate_vlm ``
  --adapter_path backend/models/remote_sensing_vlm/checkpoints/best_adapter ``
  --sample_limit 50
"@ -ForegroundColor Cyan
