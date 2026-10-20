# Astra AI — Model Evaluation & Verification

This document summarizes the empirical verification, test suite execution, and confidence calibration results for Astra AI.

---

## 1. Test Suite Verification

The codebase includes an extensive automated test suite covering unit tests, integration pipelines, memory safety, and model provenance audits:

- **Total Backend Tests**: 121 / 121 Passing (100% clean test execution)
- **Framework**: `pytest` and `pytest-asyncio`
- **Execution Target**: FastAPI backend on Python 3.11 with PyTorch 2.x and CUDA acceleration.

### Key Test Categories
1. **Model Provenance Audit (`test_model_provenance_audit.py`)**:
   - Confirms weights load into standard PyTorch backbones without shape or state mismatch.
   - Validates official model registry schema and metadata.
2. **Geospatial Gateway & Validator (`test_validator.py`, `test_metadata.py`)**:
   - Verifies rejection of corrupted rasters, missing affine geotransforms, and unsupported MIME types.
   - Confirms CRS extraction and bounding box coordinate geometry.
3. **Report Quality & Regression (`test_report_human_readable_regression.py`)**:
   - Ensures synthesized reports are readable, factual, and strictly bound to evidence packages.
4. **Memory Safety (`test_memory_safety.py`)**:
   - Confirms VRAM garbage collection and PyTorch cache clearing after inference runs.

---

## 2. Benchmark Model Accuracies

| Task | Specialist Model | Dataset | Metric | Verified Score |
| :--- | :--- | :--- | :--- | :--- |
| **LULC (19 classes)** | ResNet-50 v2 | BigEarthNet v2.0 | Validation Accuracy | **91.79%** |
| | | | Validation Macro F1 | **70.38%** (0.7038) |
| | | | Validation Micro F1 | **76.04%** (0.7604) |
| | | | Test Accuracy | **91.67%** |
| | | | Test Macro F1 | **65.15%** (0.6515) |
| **Change Detection** | BIT ResNet-18 | LEVIR-CD | Overall Accuracy | **96.98%** |
| | | | F1 Score | **69.56%** |
| | | | IoU | **53.33%** |
| **Change VQA** | CDVQA Specialist | CDVQA | Sample Val Accuracy | **80.0%** |
| **RS-VLM Adapter** | BLIP LoRA | BigEarthNet.txt | Binary Question EM | **70.8%** |

*Note on Metric Integrity*: 91.79% is the validation accuracy at Epoch 19 of the 20-epoch training run. It is not mAP. All figures are derived directly from reproducible training evaluations logged in `backend/models/model_registry.json`.

---

## 3. Confidence Calibration (Post-Hoc Temperature Scaling)

Deep neural networks often produce overconfident probability estimates that do not reflect empirical likelihood. To ensure trustworthy human-in-the-loop decision-making, Astra applies **Temperature Scaling**:

$$\hat{p}_i = \max_{k} \sigma\left(\frac{z_i}{T}\right)_k$$

- **Optimal Calibration Temperature**: $T = 3.1515$
- **Negative Log-Likelihood (NLL) Before**: 0.5807
- **Negative Log-Likelihood (NLL) After**: 0.3263
- **Calibration Error Reduction**: **43.8%** reduction in probability misalignment.

---

## 4. End-to-End Benchmark Evaluation Cases

The platform includes 10 fully reproducible evaluation scenarios (located in [evaluation/results/](../evaluation/results)):

1. `CASE_01_LULC`: Urban fabric, inland water, and forest canopy classification on Sentinel-2 optical data.
2. `CASE_02_VRS_CAPTION`: Automated dense captioning and scene layout identification.
3. `CASE_03_GROUNDING`: Spatial bounding box grounding of specific infrastructure.
4. `CASE_04_CHANGE_DETECTION`: Bi-temporal building appearance change detection on LEVIR-CD pairs.
5. `CASE_05_CHANGE_VQA`: Multi-turn question answering over changing urban landscapes.
6. `CASE_06_CROSS_MODAL`: Optical + SAR cross-sensor verification (Sentinel-2 reflectance vs. Sentinel-1 backscatter).
7. `CASE_07_MULTI_TOOL_AREA`: Autonomous routing across LULC model and deterministic polygon area tool.
8. `CASE_08_MULTI_TOOL_CHANGE`: Change detection combined with deterministic surface area in hectares.
9. `CASE_09_LARGE_RASTER_TILING`: Memory-bounded 1024×1024 tile processing over regional satellite scenes.
10. `CASE_10_CORRUPTED_FAILSAFE`: Graceful rejection and diagnostic feedback on corrupted or non-georeferenced imagery.
