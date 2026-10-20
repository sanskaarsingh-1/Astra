# Astra AI / SatQuery AI — Offline Evaluation Suite
## SIH26167 | Space Technology (ISRO SAC)

### Overview
This offline evaluation suite allows evaluators and engineers to execute reproducible benchmark queries against the full SatQuery AI engine without requiring the Next.js web frontend or external cloud connectivity.

The evaluation suite directly executes the production FastAPI orchestration pipeline (`_run_investigation`), specialist neural networks (ResNet-50 v2, BIT Siamese ResNet-18, VRSBench, BLIP LoRA VLM), and deterministic geospatial tools.

---

### Environment Setup

#### 1. Prerequisites
- Python 3.11+
- NVIDIA CUDA-capable GPU recommended (developed & verified on RTX 5060 Laptop GPU, 8GB VRAM)
- Local Python virtual environment at `backend/.venv` (or equivalent environment with `torch`, `rasterio`, `fastapi`, `pydantic`, `peft`)

#### 2. Environment Variables
Set `PYTHONPATH` to include the project root and backend directory:
```powershell
# Windows PowerShell
$env:PYTHONPATH = "$PWD;$PWD\backend"

# Linux / Bash
export PYTHONPATH="$PWD:$PWD/backend"
```

---

### CLI Usage Guide

#### A. Single Optical or SAR Scene Query
```bash
python evaluation/run_eval.py \
  --image evaluation/test_data/representative_cartosat_optical.tif \
  --query "What type of land cover dominates this scene?"
```

#### B. Bi-Temporal Change Detection Query
```bash
python evaluation/run_eval.py \
  --image-a evaluation/test_data/representative_bitemporal_t1.tif \
  --image-b evaluation/test_data/representative_bitemporal_t2.tif \
  --query "What changed between these two dates?"
```

#### C. Optical + SAR Cross-Modal Fusion Query
```bash
python evaluation/run_eval.py \
  --optical evaluation/test_data/representative_cartosat_optical.tif \
  --sar evaluation/test_data/representative_risat_sar.tif \
  --query "Compare optical and SAR observations for surface structures."
```

#### D. Batch Evaluation via Manifest
Execute all 10 standard evaluation cases in one command:
```bash
python evaluation/run_eval.py \
  --manifest evaluation/evaluation_manifest.json \
  --output-dir evaluation/results \
  --format all
```

---

### Evaluation Manifest Structure
The manifest (`evaluation/evaluation_manifest.json`) defines 10 representative tasks:
1. `CASE_01_LULC`: Land cover characterization (ResNet-50 v2 BigEarthNet, calibrated $T=3.1515$).
2. `CASE_02_VRS_CAPTION`: Remote-sensing scene description (VRSBench captioning).
3. `CASE_03_GROUNDING`: Object localization (VRSBench visual grounding bbox regression).
4. `CASE_04_CHANGE_DETECTION`: Pixel-level bi-temporal surface change detection (Siamese BIT).
5. `CASE_05_CHANGE_VQA`: Bi-temporal visual question answering (CDVQA).
6. `CASE_06_CROSS_MODAL`: Optical reflectance fused with SAR backscatter geometry.
7. `CASE_07_MULTI_TOOL_AREA`: Multi-tool: LULC classification + deterministic area metrology.
8. `CASE_08_MULTI_TOOL_CHANGE`: Multi-specialist: Change detection + LULC + changed area calculation.
9. `CASE_09_LARGE_RASTER_TILING`: Windowed $O(1)$ memory tiling on a large mosaic without whole-scene downsampling.
10. `CASE_10_CORRUPTED_FAILSAFE`: Graceful interception of unparsable GeoTIFF headers with diagnostic failure reporting.

---

### Output Artifacts
All evaluation runs output structured artifacts to `--output-dir` (default: `evaluation/results/`):
- `[case_id]_result.json`: Machine-readable JSON summary including latency, tools invoked, models used, and confidence status.
- `[case_id]_report.md`: Publication-grade Markdown report including all 13 investigation sections.
- `[case_id]_report.html`: Publication-grade semantic HTML report with embedded `@media print` styling for clean browser "Print to PDF".
- `batch_evaluation_summary.json`: Master index of all batch manifest runs.

---

### Representative Test Data
Representative synthetic rasters approximating Cartosat-2S and RISAT-1A sensor characteristics are located in `evaluation/test_data/`:
- `representative_cartosat_optical.tif` (512x512, 3-band, 1.0m GSD, EPSG:32643)
- `representative_risat_sar.tif` (512x512, 1-band C-Band amplitude with radar speckle, EPSG:32643)
- `representative_bitemporal_t1.tif` and `representative_bitemporal_t2.tif` (Bi-temporal pair with simulated urban expansion)
- `representative_large_scene.tif` (1200x1200px GeoTIFF for windowed tiling verification)
- `corrupted_sample.tif` (Malformed header for fail-safe validation)

To re-generate or modify test datasets:
```bash
python evaluation/generate_test_data.py
```

*Note: In accordance with SIH rules, these datasets are strictly synthetic representative benchmarks and are NOT hidden ISRO/SAC test data.*

---

### Model Weights Notice
Because production model checkpoints exceed 1.5 GB in total (ResNet-50 v2, BIT Siamese ResNet-18, LoRA VLM, VRSBench), model weights are stored in their native project locations:
- `backend/models/bigearthnet_resnet50_v2_full/best_model.pth`
- `backend/models/change_detection/checkpoints/best_model.pth`
- `backend/models/remote_sensing_vlm/checkpoints/best_adapter/adapter_model.safetensors`
The evaluation CLI automatically references these local paths.
