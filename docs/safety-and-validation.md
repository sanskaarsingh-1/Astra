# Astra AI — Safety, Validation & Guardrails Architecture

This document describes the validation pipeline, failure handling mechanisms, and ethical AI principles embedded in Astra AI.

---

## 1. Input Gateway Validation Checks

Every image submitted to the platform passes through rigorous multi-level validation in `backend/gateway/validator.py`:

1. **File Format & MIME Validation**:
   - Rejects non-raster files, arbitrary binary payloads, and mismatched file extensions.
   - Requires valid GeoTIFF / TIFF / PNG / JPEG formats.
2. **Raster Integrity & Readability**:
   - Tests raster opening via `rasterio`. Catches corrupted files before execution starts.
3. **Coordinate Reference System (CRS) & Affine Transform**:
   - Extracts valid EPSG coordinate reference systems and affine 6-parameter transformation matrices.
   - Flags non-georeferenced imagery so the user is informed that physical coordinates are local pixel-based.
4. **Ground Sample Distance (GSD)**:
   - Validates pixel resolution in meters. Prevents dividing by zero in area calculations.
5. **Modality & Pair Compatibility**:
   - For bitemporal investigations (e.g., LEVIR-CD change detection), validates that T1 and T2 images share identical or overlapping bounding boxes and coordinate frames.
   - For optical-SAR investigations, validates optical reflectance vs. radar channel dimensions.

---

## 2. Core Safety & Transparency Principles

- **Zero Fake Inference**: Specialist models execute real PyTorch inference on GPU/CPU. When a model is unavailable or in fallback mode, the system explicitly reports its operational state.
- **No Hallucinated Geospatial Measurements**: All quantitative metrics (surface area, distance, bounding box coordinates) are strictly calculated by deterministic mathematical tools. The LLM synthesizer is prohibited from inventing numbers.
- **Confidence Calibration**: Outputs are accompanied by calibrated posterior probabilities using Temperature Scaling ($T = 3.1515$), avoiding artificial overconfidence.
- **Failure Transparency**: If a pipeline step encounters an exception, it does not silently fabricate an answer. Instead, it logs the failure in the evidence package and returns a structured failure report with actionable troubleshooting steps.
