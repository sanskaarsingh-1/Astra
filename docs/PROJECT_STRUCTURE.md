# Astra AI / SatQuery AI: Project Directory Architecture

**Problem Statement**: SIH26167 — *SatQuery AI: Interactive Vision-Language Assistant for Multimodal Remote Sensing Image Analysis through Text Queries*  
**Organization**: Indian Space Research Organisation (ISRO) / Space Applications Centre (SAC)  

This document outlines the directory structure and responsibilities of each module in the repository.

---

## High-Level Repository Layout

```
astra-ai/
├── backend/                  # Production inference, model gateway, API & orchestrator
├── frontend/                 # Next.js 14 web application & Earth View GIS HUD
├── training/                 # Model adaptation, fine-tuning pipelines & configs
├── datasets/                 # Remote sensing datasets (BigEarthNet, LEVIR-CD, CDVQA, etc.)
├── evaluation/               # Independent benchmark evaluation runner & manifests
├── models/                   # Root model weights (ben_classifier.pth)
├── scripts/                  # Data engineering & training helper scripts
├── live_testing/             # SIH live evaluation test prompts, checklists & demo imagery
├── docs/                     # Technical specifications, handover & provenance documentation
├── reports/                  # Evaluation snapshots & metric reports
├── uploads/                  # Runtime upload directory (gitignored)
├── outputs/                  # Runtime inference outputs (gitignored)
├── launch.ps1                # Full-stack orchestrator launcher (GPU backend + tunnel)
└── package.json              # Root project scripts
```

---

## 1. `backend/` — Inference & Multi-Specialist Orchestration

The backend is built with FastAPI and runs on Python 3.11 with NVIDIA CUDA GPU acceleration.

```
backend/
├── main.py                   # FastAPI server entrypoint & REST API endpoints
├── config.py                 # System configurations, thresholds & directory bindings
├── gateway/                  # Modality detection, CRS extraction & affine validation
├── orchestrator/             # Gemini 3.8 / 1.5 Pro investigation planner & schemas
├── models/                   # Specialist deep-learning models & PyTorch checkpoints
│   ├── baseline/             # ResNet-18 baseline classifier
│   ├── bigearthnet_resnet50_v2_full/ # Production ResNet-50 v2 multi-label classifier
│   ├── change_detection/     # BIT (Bitemporal Image Transformer) ResNet-18 model
│   ├── cross_modal/          # Optical (Cartosat/S2) + SAR (RISAT/S1) fusion specialist
│   ├── captioning/           # Remote sensing image captioning specialist
│   ├── cdvqa/                # Change-detection visual question answering specialist
│   ├── remote_sensing_vlm/   # Adapted BLIP / LoRA VLM specialist
│   └── rsvqa/                # Remote sensing VQA with casualty guardrails
├── engine/                   # Specialist execution engines & deterministic geospatial tools
│   └── tools/                # Area calculations, NDVI, NDWI, SAR polarimetry
├── evidence/                 # Multi-modal evidence assembler & visual card builder
├── report/                   # Senior analyst synthesis, markdown & HTML report exporter
├── services/                 # Model memory manager & dynamic GPU allocation
└── tests/                    # Comprehensive PyTest test suite (unit + integration)
```

---

## 2. `frontend/` — Interactive Web Application & Earth View

The frontend is built on Next.js 14 (App Router), React 18, Tailwind CSS, and MapLibre GL JS.

```
frontend/
├── src/
│   ├── app/                  # Next.js App Router pages
│   │   ├── page.tsx          # Homepage ("Ask satellites what changed")
│   │   ├── earth/page.tsx    # Earth View (OpenStreetMap 2D + 3D Globe + Disasters)
│   │   ├── analyze/page.tsx  # SatQuery AI interactive multimodal analysis workspace
│   │   ├── mission/page.tsx  # ISRO SAC problem statement & system architecture
│   │   └── roster/page.tsx   # Team roster & specialist portfolio
│   ├── components/
│   │   ├── earth/            # MapLibre map, HUD, disaster drawers & detail cards
│   │   ├── investigate/      # Evidence viewer, model registry modal & report card
│   │   └── ui/               # Reusable UI primitives (FlowButton, Limelight, etc.)
│   ├── lib/
│   │   ├── earth/            # OpenStreetMap tile providers & disaster feed connectors
│   │   └── api-config.ts     # Dynamic backend URL resolution (Local / Cloudflare Tunnel)
│   └── data/                 # Static presets and team data
├── public/                   # Public assets, web-optimized videos, fonts & team portraits
└── package.json              # Frontend dependencies and Next.js scripts
```

---

## 3. `training/` — Specialist Model Fine-Tuning Pipeline

Encapsulates data ingestion, training pipelines, and parameter-efficient fine-tuning (PEFT/LoRA).

```
training/
├── configs/                  # Hyperparameter YAML/JSON configs for model training
├── datasets/                 # Ingestion manifests and preprocessing transforms
├── models/                   # Pre-training checkpoint definitions & LoRA adapter targets
├── pipelines/                # Training loop implementations (PyTorch / Accelerate)
└── scripts/                  # Individual training launch scripts
```

---

## 4. `docs/` — Documentation & Architectural Records

```
docs/
├── earth-view/               # Earth View architecture, feeds & data provenance
├── implementation/           # SIH audit reports & OpenStreetMap migration handover
├── environment/              # Diagnostic GPU environment snapshots
└── third-party/              # Licenses and third-party attribution notices
```

---

## 5. Development & Deployment Workflows

- **Start Full Stack**: Run `.\launch.ps1` from repository root.
- **Run Backend Tests**:
  ```powershell
  $env:PYTHONPATH="<repo-root>;<repo-root>\backend"; .\backend\.venv\Scripts\python.exe -m pytest backend/tests/
  ```
- **Build Frontend**:
  ```powershell
  cd frontend; npm run build
  ```
- **Manual Training**:
  ```powershell
  .\scripts\training\run_training_manual_cdvqa.ps1
  .\scripts\training\run_training_manual_change_detection.ps1
  .\scripts\training\run_training_manual_cross_modal.ps1
  ```
