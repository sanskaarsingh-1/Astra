# Astra AI Backend

SIH26167 — SatQuery AI: Interactive Vision-Language Assistant for Multimodal Remote Sensing Image Analysis.

## Architecture

```
Layer 1: Input Gateway       → File validation, metadata extraction, modality detection
Layer 2: Gemini Orchestrator → Query understanding, investigation planning
Layer 3: Execution Engine    → Plan execution, model/tool dispatch
Layer 4: Evidence Assembly   → Result validation, confidence scoring, trace building
Layer 5: Report Synthesis    → Gemini narrative synthesis
```

## Quick Start (Windows)

```powershell
cd backend
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY
notepad .env

# Create virtual environment
python -m venv .venv
.venv\Scripts\activate

# Install dependencies (install PyTorch with CUDA first)
# See: https://pytorch.org/get-started/locally/
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121
pip install -r requirements.txt

# Run
.\start.ps1
```

## Manual Start

```powershell
.venv\Scripts\activate
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

## API

| Endpoint | Method | Description |
|---|---|---|
| `/health` | GET | GPU and backend status |
| `/api/investigate` | POST | Submit investigation (multipart form) |
| `/api/investigate/{job_id}/stream` | GET | SSE progress stream |
| `/api/investigate/{job_id}/result` | GET | Poll for result |
| `/docs` | GET | FastAPI auto-generated docs |

## Project Structure

```
backend/
├── main.py                    # FastAPI app entry point
├── config.py                  # Settings (from .env)
├── requirements.txt
├── start.ps1                  # Windows startup script
│
├── gateway/                   # Layer 1: Input validation
│   ├── validator.py           # File format/size/magic byte validation
│   ├── metadata.py            # CRS, resolution, band extraction
│   └── modality.py            # Optical/SAR/multispectral detection
│
├── orchestrator/              # Layer 2: Gemini planning
│   ├── planner.py             # Gemini → InvestigationPlan
│   ├── registry.py            # Model & tool registry (source of truth)
│   └── schemas.py             # All Pydantic data models
│
├── engine/                    # Layer 3: Execution
│   ├── executor.py            # Plan execution loop with timeout/retry
│   ├── models/
│   │   ├── loader.py          # Lazy GPU model loader
│   │   ├── geochat.py         # GeoChat VQA/caption/grounding
│   │   ├── change_detect.py   # BIT change detection
│   │   └── classifier.py      # BigEarthNet scene classifier
│   └── tools/
│       ├── raster_stats.py    # Band statistics, SAR statistics
│       ├── indices.py         # NDVI computation
│       ├── geometry.py        # Area, distance calculations
│       └── visualizer.py      # Mask overlay, thumbnails
│
├── evidence/                  # Layer 4: Evidence assembly
│   └── assembler.py           # Validates results, builds EvidencePackage
│
├── report/                    # Layer 5: Report synthesis
│   └── synthesizer.py         # Gemini narrative synthesis
│
├── training/                  # BigEarthNet classifier training
│   ├── train_ben_classifier.py
│   └── README.md
│
├── models/                    # Downloaded model weights (gitignored)
│   ├── ben_classifier.pth     # Trained BigEarthNet classifier
│   └── BIT_CD.pth             # BIT change detection weights
│
├── uploads/                   # Temporary uploaded files (gitignored)
└── tests/
    └── test_gateway_and_tools.py
```

## Models Required

| Model | Source | Download |
|---|---|---|
| GeoChat-7B | HuggingFace | `huggingface-cli download MBZUAI/geochat-7B` |
| BIT Change Detection | GitHub | https://github.com/justchenhao/BIT_CD |
| BigEarthNet Classifier | Train it | `python training/train_ben_classifier.py` |

## Running Tests

```powershell
.venv\Scripts\activate
pytest tests/ -v
```

## Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `GEMINI_API_KEY` | ✅ Yes | — | Google AI API key |
| `USE_INT4_QUANTIZATION` | No | `true` | 4-bit quantization for GeoChat |
| `MAX_FILE_SIZE_MB` | No | `200` | Max upload size per file |
| `ALLOWED_ORIGINS` | No | Firebase URL | CORS allowed origins |

## ⚠ GPU Memory Notes

- GeoChat-7B: 7GB VRAM (INT4) or 16GB (FP16)
- BIT: ~2GB VRAM
- BigEarthNet classifier: <1GB VRAM
- Models are lazy-loaded — only one large model in VRAM at a time
- On 8-12GB GPUs: always use `USE_INT4_QUANTIZATION=true`
