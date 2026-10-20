# Astra AI — Specialist Model & Deterministic Tool Registry

This document records the official provenance, architectures, checkpoint paths, and verified benchmark metrics for all AI models and deterministic tools integrated into Astra AI.

---

## 1. Specialist AI Models

### 1.1 `ben-scene-classifier` (Production Land-Use / Land-Cover Classifier)
- **Role**: `CURRENT_PRODUCTION_MODEL`
- **Endpoint**: `POST /api/specialists/lulc`
- **Architecture**: Deep ResNet-50 (`torchvision.models.resnet50`) with custom linear classifier head (`nn.Linear(2048, 19)`).
- **Dataset**: BigEarthNet v2.0 (reBEN) multi-label benchmark.
  - Total Samples: 480,038
  - Splits: Train (237,871), Val (122,342), Test (119,825) across 115 Sentinel-2 tiles.
- **Checkpoint Location**: `backend/models/bigearthnet_resnet50_v2_full/best_model.pth` (283 MB)
- **Training Epochs**: 20 (Best Epoch: 19)
- **Verified Metrics**:
  - **Validation Accuracy**: 91.79% *(Note: Accuracy at best epoch, not mAP)*
  - **Validation Macro F1**: 70.38% (0.7038)
  - **Validation Micro F1**: 76.04% (0.7604)
  - **Test Accuracy**: 91.67%
  - **Test Macro F1**: 65.15% (0.6515)
  - **Status**: Operational Production

### 1.2 `bit-change-detection` (Bitemporal Change Detection Specialist)
- **Role**: `CURRENT_PRODUCTION_MODEL`
- **Endpoint**: `POST /api/specialists/change` / `POST /api/specialists/change-detection`
- **Architecture**: Bitemporal Image Transformer (BIT) with Siamese dual-stream ResNet-18 backbone and spatial-temporal transformer decoder.
- **Dataset**: LEVIR-CD benchmark (1,280 bitemporal optical pairs).
- **Checkpoint Location**: `backend/models/change_detection/checkpoints/best_model.pth` (77.8 MB)
- **Training Epochs**: 10
- **Verified Metrics**:
  - **Overall Accuracy**: 96.98%
  - **F1 Score**: 69.56%
  - **Intersection over Union (IoU)**: 53.33%
  - **Status**: Operational Production

### 1.3 `rsvqa-specialist` (Remote Sensing VQA Specialist)
- **Role**: `CURRENT_PRODUCTION_MODEL`
- **Endpoint**: `POST /api/specialists/vqa`
- **Architecture**: Visual Question Answering reasoning engine conditioned on LULC context and multi-scale visual features.
- **Dataset**: RSVQA Low-Resolution & High-Resolution (167,667 question-answer pairs).
- **Domain Coverage**: Object presence, count queries, rural/urban distinction, spatial comparisons.
- **Status**: Operational Production

### 1.4 `vrsbench-caption` (Dense Scene Captioner)
- **Role**: `CURRENT_PRODUCTION_MODEL`
- **Endpoint**: `POST /api/specialists/caption`
- **Architecture**: Fine-grained remote-sensing scene description generator.
- **Dataset**: VRSBench Captioning split (9,350 image-caption pairs).
- **Output**: Detailed paragraph describing scene layout, land cover, and dominant infrastructure.
- **Status**: Operational Production

### 1.5 `vrsbench-grounding` (Referring Expression Grounding Specialist)
- **Role**: `CURRENT_PRODUCTION_MODEL`
- **Endpoint**: `POST /api/specialists/grounding`
- **Architecture**: Text-guided spatial localization model.
- **Dataset**: VRSBench Referring Expressions (16,159 spatial annotations).
- **Output Format**: Normalized bounding boxes `[ymin, xmin, ymax, xmax]` for targeted query entities.
- **Status**: Operational Production

### 1.6 `cdvqa-specialist` (Change Visual Question Answering)
- **Role**: `CURRENT_PRODUCTION_MODEL`
- **Endpoint**: `POST /api/specialists/change-vqa`
- **Architecture**: Dual-raster change reasoning network fusing BIT change masks with ResNet-50 delta LULC transitions.
- **Dataset**: CDVQA benchmark (2,968 pairs).
- **Sample Validation Accuracy**: 80.0% on representative validation subset.
- **Status**: Operational Production

### 1.7 `cross-modal-specialist` (Optical + SAR Cross-Modal Reasoning)
- **Role**: `CURRENT_PRODUCTION_MODEL`
- **Endpoint**: `POST /api/specialists/optical-sar`
- **Architecture**: Dual Physical Encoder comparing optical surface reflectance against Sentinel-1 / RISAT-1A microwave radar backscatter ($\sigma^0$ dB).
- **Functionality**: Distinguishes cloud shadow from water bodies, validates structural damage through persistent double-bounce microwave scattering, and flags cross-sensor physical contradictions.
- **Status**: Operational Production

### 1.8 `rs-vlm-adapter` (Remote Sensing Vision-Language LoRA Adapter)
- **Role**: `PARTIAL_ADAPTATION`
- **Architecture**: `Salesforce/blip-image-captioning-base` fine-tuned via PEFT LoRA ($r=16, \alpha=32$).
- **Dataset**: BigEarthNet.txt (464,044 multimodal image-text pairs).
- **Adapter Location**: `backend/models/remote_sensing_vlm/checkpoints/best_adapter/` (2.37 MB)
- **Status**: Available via PEFT runtime loader.

---

## 2. Deterministic Mathematical Tools

The mathematical tools are implemented in Python using `rasterio`, `pyproj`, `shapely`, and `numpy`. They are guaranteed to be exact and reproducible.

| Tool Name | Identifier | Method | Output | Status |
| :--- | :--- | :--- | :--- | :--- |
| **Raster Metadata Inspector** | `raster-metadata` | Rasterio header tags | CRS, EPSG, Affine matrix, Extent, GSD | DETERMINISTIC |
| **Band Statistics Calculator** | `raster-stats` | Exact array mathematics | Min, Max, Mean, Std, P2, P98 per band | DETERMINISTIC |
| **SAR Backscatter Analyzer** | `sar-stats` | Radar radiometric equation | Calibrated $\sigma^0$ dB backscatter & roughness | DETERMINISTIC |
| **NDVI Calculator** | `ndvi-calculator` | $(NIR - Red) / (NIR + Red)$ | Normalized vegetation difference grid | DETERMINISTIC |
| **Surface Area Calculator** | `area-calculator` | $pixel\_count \times GSD^2$ | Exact area in $m^2$, $km^2$, and hectares | DETERMINISTIC |
| **Bounding Box Area Tool** | `bbox-area-calculator` | Coordinate geometry | Coordinate bounding box area | DETERMINISTIC |
| **WGS84 Geodesic Polygon Tool** | `polygon-area-calculator`| Shapely & PyProj ellipsoid | Spherical Earth geodesic polygon area | DETERMINISTIC |
| **Geodesic Distance Tool** | `geodesic-distance-calculator` | PyProj WGS84 Geodesic | Great-circle distance in meters / kilometers | DETERMINISTIC |
| **Temporal Change Quantification** | `change-area` | Difference mask aggregation | Changed surface area in $m^2$ and hectares | DETERMINISTIC |
| **Visual Mask Overlay Renderer** | `mask-overlay` | Alpha channel blending | Display-safe composite visualization PNG | DETERMINISTIC |
