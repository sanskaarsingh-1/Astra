# Astra AI — Remote Sensing Dataset Ecosystem

This document details the public benchmarks, satellite datasets, licensing terms, and directory conventions used in Astra AI.

---

## 1. Primary Datasets

### 1.1 BigEarthNet v2.0 (reBEN)
- **Primary Subsystem**: LULC Specialist (`ben-scene-classifier`)
- **Sensor**: Sentinel-2 (Multispectral VNIR/SWIR) & Sentinel-1 (C-Band SAR)
- **Scale**: 480,038 image patches across 115 Sentinel-2 tiles covering 10 European countries.
- **Classes**: 19 Corine Land Cover (CLC) classes.
- **License**: Creative Commons Attribution 4.0 International (CC BY 4.0).
- **Official Source**: [BigEarthNet.net](https://bigearthnet.net/) / TU Berlin.
- **Expected Directory**: `datasets/01_BigEarthNet_v2/`

### 1.2 BigEarthNet.txt
- **Primary Subsystem**: Vision-Language LoRA Adapter (`rs-vlm-adapter`)
- **Scale**: 464,044 paired image-text captions formatted in Parquet files.
- **License**: CC BY 4.0.
- **Expected Directory**: `datasets/02_BigEarthNet_txt/`

### 1.3 LEVIR-CD
- **Primary Subsystem**: Bi-temporal Change Detection (`bit-change-detection`)
- **Sensor**: Very High Resolution (VHR) Optical imagery (0.5m GSD).
- **Scale**: 1,280 bitemporal image pairs (1024 × 1024 pixels) with binary change masks.
- **Application**: Urban expansion, building appearance, and infrastructure changes over 5 to 14 year intervals.
- **License**: Academic research license.
- **Expected Directory**: `datasets/05_LEVIR_CD/`

### 1.4 CDVQA (Change Detection Visual Question Answering)
- **Primary Subsystem**: Change-VQA Specialist (`cdvqa-specialist`)
- **Scale**: 2,968 bitemporal image pairs with question-answer triplets grounded in physical change masks.
- **Expected Directory**: `datasets/04_CDVQA/`

### 1.5 RSVQA (Remote Sensing Visual Question Answering)
- **Primary Subsystem**: RSVQA Specialist (`rsvqa-specialist`)
- **Sensors**: Sentinel-2 (LR) and High-Resolution aerial imagery (HR).
- **Scale**: 167,667 question-answer pairs covering Presence, Count, Rural/Urban, and Comparison queries.
- **License**: Academic research license.
- **Expected Directory**: `datasets/06_RSVQA/`

### 1.6 VRSBench
- **Primary Subsystem**: Captioning & Grounding Specialists (`vrsbench-caption`, `vrsbench-grounding`)
- **Scale**: 29,614 high-resolution satellite scenes with 9,350 captions and 16,159 referring expression bounding boxes.
- **Expected Directory**: `datasets/03_VRSBench/`

### 1.7 Indian Earth Observation Satellite Data (ISRO)
- **Sensors**: Cartosat-2S (Panchromatic High-Resolution Optical, 0.65m) and RISAT-1A / EOS-04 (C-Band Synthetic Aperture Radar).
- **Role**: Validating multimodal optical-SAR fusion, speckle filtering, and cross-sensor reasoning.

---

## 2. Directory Layout & Git Policy

Due to bandwidth, storage, and licensing constraints, raw dataset archives are **never committed to Git**. The repository maintains strict `.gitignore` rules while preserving directory structure via `.gitkeep`:

```text
datasets/
├── 01_BigEarthNet_v2/       # Downloaded separately via official scripts
├── 02_BigEarthNet_txt/      # HuggingFace Parquet downloads
├── 03_VRSBench/             # VRSBench benchmark splits
├── 04_CDVQA/                # CDVQA image pairs & JSON manifests
├── 05_LEVIR_CD/             # LEVIR-CD train/val/test splits
├── 06_RSVQA/                # RSVQA low/high res splits
├── manifests/               # Lightweight JSON metadata (committed)
└── processed/               # Cached PyTorch dataset indices
```

---

## 3. How to Obtain Datasets for Training

To download and prepare datasets for local model fine-tuning:

```powershell
cd training
python scripts/download_datasets.py --dataset bigearthnet --data-dir ../datasets
python scripts/prepare_dataset.py --config configs/change_detection/levir_cd.yaml
```
For inference and demonstration purposes, lightweight sample GeoTIFF rasters are pre-packaged in [single_image/](../single_image) and [evaluation/test_data/](../evaluation/test_data).
