# Astra AI — System Architecture & Technical Design

## 1. Architectural Overview & Philosophy

**Astra AI (SatQuery AI)** is an agentic, multimodal remote sensing intelligence platform designed for the **Indian Space Research Organisation (ISRO) Space Applications Centre (SAC)** under **Smart India Hackathon 2026 (Problem Statement: SIH26167)**.

Traditional remote sensing workflows force domain experts to manually handle image preprocessing, calibrate GIS metadata, hand-pick task-specific neural networks, and execute offline GIS scripts. Monolithic general-purpose Vision-Language Models (VLMs), on the other hand, frequently hallucinate spatial dimensions, misinterpret multispectral sensor physics, and generate inaccurate numerical estimates.

Astra solves this dilemma through a **Decoupled Three-Pillar Architecture**:
1. **Frontend Experience**: Next.js 14 App Router with 2D/3D Earth View GIS and SatQuery AI investigation interface.
2. **Production Inference Gateway**: FastAPI backend coordinating the Gemini Agentic Planner, locally-hosted specialist deep learning models, deterministic geospatial tools, and confidence calibration.
3. **Training & Fine-Tuning Pipeline**: Offline pipelines for dataset preparation, PEFT LoRA adapters, model evaluation, and checkpoint registration.

---

## 2. The Three Pillars

```mermaid
flowchart TB
    subgraph PILLAR_1 ["PILLAR 1: FRONTEND (Next.js 14)"]
        UI_HOME[Interactive Showcase & Landing]
        UI_EARTH[Earth View GIS: 2D OSM & 3D Globe]
        UI_ANALYZE[SatQuery AI Investigation Workspace]
        UI_ROSTER[Model Roster & Registry Viewer]
    end

    subgraph PILLAR_2 ["PILLAR 2: PRODUCTION GATEWAY (FastAPI)"]
        GW_VALIDATE[Input Gateway: Format & CRS Validation]
        ORCH_PLAN[Gemini Agentic Planner: DAG Generator]
        
        subgraph SPECIALISTS ["Locally-Hosted Specialist Models"]
            M_LULC[LULC: ResNet-50 v2]
            M_CD[Change Detection: BIT ResNet-18]
            M_VQA[RSVQA Specialist]
            M_CAP[VRSBench Scene Captioner]
            M_GRD[VRSBench Spatial Grounding]
            M_XM[Optical-SAR Fusion Specialist]
        end

        subgraph TOOLS ["Deterministic Mathematical Engine"]
            T_AREA[Exact Surface Area (ha, m²)]
            T_GEO[PyProj Geodesic Calculations]
            T_NDVI[Spectral Index Arithmetic]
            T_SAR[Calibrated Sigma0 Backscatter]
        end

        EV_ENGINE[Evidence Assembler & Provenance Tracker]
        CALIB[Confidence Calibration (Temperature Scaling)]
        SYNTH[LLM Report Synthesizer & Exporter]
    end

    subgraph PILLAR_3 ["PILLAR 3: TRAINING & DATASETS"]
        DATA_REBEN[BigEarthNet v2.0 - 480k Samples]
        DATA_LEVIR[LEVIR-CD Bitemporal Pairs]
        DATA_VRS[VRSBench & CDVQA Datasets]
        TRAIN_SCRIPTS[PyTorch / PEFT LoRA Training Harness]
        REG_JSON[model_registry.json Checkpoint Catalog]
    end

    UI_ANALYZE -->|Multipart Upload + Query| GW_VALIDATE
    GW_VALIDATE --> ORCH_PLAN
    ORCH_PLAN --> SPECIALISTS
    ORCH_PLAN --> TOOLS
    SPECIALISTS --> EV_ENGINE
    TOOLS --> EV_ENGINE
    EV_ENGINE --> CALIB
    CALIB --> SYNTH
    SYNTH -->|SSE Stream / JSON / Reports| UI_ANALYZE
    REG_JSON -.->|Approved Weights| SPECIALISTS
```

---

## 3. The 5-Stage Investigation Pipeline

Every user query undergoes an auditable 5-stage pipeline:

```text
┌─────────────────┐     ┌──────────────────┐     ┌──────────────────┐
│ STAGE 1:        │     │ STAGE 2:         │     │ STAGE 3:         │
│ Input Gateway & │ ──> │ Agentic Graph    │ ──> │ Parallel Task    │
│ Spatial Audit   │     │ Planning         │     │ Dispatch         │
└─────────────────┘     └──────────────────┘     └──────────────────┘
                                                           │
                                                           ▼
┌─────────────────┐     ┌──────────────────┐     ┌──────────────────┐
│ STAGE 5:        │     │ STAGE 4:         │     │ (Intermediate:   │
│ Synthesis &     │ <── │ Evidence &       │ <── │ Calibration &    │
│ Multi-Format    │     │ Provenance       │     │ Deterministic    │
│ Reporting       │     │ Aggregation      │     │ Math)            │
└─────────────────┘     └──────────────────┘     └──────────────────┘
```

1. **Stage 1 — Input Gateway & Spatial Audit**:
   - Parses GeoTIFF spatial headers using `rasterio`.
   - Validates CRS, EPSG affine matrices, resolution (Ground Sample Distance in meters), and band arrangements.
   - Rejects corrupted, non-georeferenced, or physically unsupportable requests (e.g., sub-meter individual human detection on 10m Sentinel-2).
2. **Stage 2 — Agentic Graph Planning**:
   - The Gemini Agentic Planner analyzes the user's natural-language query alongside spatial metadata.
   - Deconstructs complex requests into a Directed Acyclic Graph (DAG) of discrete steps.
   - Assigns each step to either a specialized neural network or a deterministic tool.
3. **Stage 3 — Parallel Execution & Model Inference**:
   - Locally executes specialist PyTorch models (INT4 quantized for 8GB/12GB consumer GPU memory budgets).
   - Evaluates deterministic tools directly in NumPy/Shapely.
4. **Stage 4 — Evidence Assembly & Confidence Calibration**:
   - Assembles raw outputs, masks, bounding boxes, and statistics into a structured evidence package.
   - Applies post-hoc Temperature Scaling ($T = 3.1515$) to convert raw network logits into well-calibrated posterior probabilities, reducing negative log-likelihood by 43.8%.
5. **Stage 5 — Synthesis & Report Generation**:
   - The LLM synthesizer drafts an executive analysis rooted strictly in the assembled evidence.
   - Generates downloadable Markdown, HTML, and JSON audit artifacts.

---

## 4. Zero-Hallucination Policy

A fundamental design rule of Astra is that **no language model is ever permitted to estimate spatial quantities**:
- All areas (hectares, square kilometers, $m^2$) are calculated via pixel count multiplied by pixel resolution ($GSD^2$).
- All distances are calculated using WGS84 geodesic ellipsoid formulas via `pyproj`.
- All spectral indices (e.g., NDVI) are calculated using exact band arithmetic.
- Outputs are tagged with `DETERMINISTIC_EXACT` to maintain clear demarcation between statistical inferences and exact mathematical calculations.
