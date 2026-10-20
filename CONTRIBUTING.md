# Contributing to Astra AI 2026

Thank you for your interest in contributing to **Astra AI (SatQuery AI)**, developed for Smart India Hackathon 2026 (Problem Statement: SIH26167) in partnership with the Indian Space Research Organisation (ISRO) Space Applications Centre (SAC).

---

## 1. Code of Conduct & Core Philosophy

Our engineering culture prioritizes:
1. **Physical Integrity & Zero Hallucination**: Never allow language models to guess, estimate, or hallucinate quantitative geospatial measurements. All physical metrics (surface area, distance, coordinates, NDVI) must be derived by deterministic tools (`rasterio`, `pyproj`, `shapely`).
2. **Confidentiality & Secret Safety**: Never commit credentials, `.env` files, API keys, or proprietary data.
3. **Reproducibility & Auditability**: Every specialist model output and agent decision step must leave an auditable execution trace with confidence metrics.
4. **Clean Code & Non-Destructive Changes**: Smallest working diff, clear type hints, comprehensive test coverage.

---

## 2. Getting Started

### Prerequisites
- **Python**: 3.11+
- **Node.js**: 18.x or 20.x LTS
- **Git**: 2.30+
- **CUDA Toolkit** (optional, recommended for GPU acceleration): CUDA 12.1+ or 12.8+

### Development Workflow
1. Fork or branch from `main`:
   ```bash
   git checkout -b feature/your-feature-name
   ```
2. Set up environment variables:
   ```bash
   cp .env.example .env
   # Edit .env and supply your development GEMINI_API_KEY
   ```
3. Follow the detailed setup instructions in [docs/SETUP.md](docs/SETUP.md).

---

## 3. Subsystem Guidelines

### Backend (`backend/`)
- Built with **FastAPI**, **Pydantic v2**, and **PyTorch**.
- Model inference code lives in `backend/models/`.
- Deterministic tools live in `backend/engine/tools/`.
- Orchestrator logic lives in `backend/orchestrator/`.
- Ensure any new endpoint is documented in [docs/api.md](docs/api.md) and has unit tests in `backend/tests/`.

### Frontend (`frontend/`)
- Built with **Next.js 14 App Router**, **TypeScript**, **Tailwind CSS**, and **MapLibre GL**.
- Components live in `frontend/src/components/`.
- Routes live in `frontend/src/app/`.
- Maintain accessibility, responsive UI, and dark-mode compatibility.

### Training & Pipelines (`training/`)
- Fine-tuning scripts live in `training/scripts/`.
- Dataset loaders live in `training/datasets/`.
- Never commit model weights (`*.pth`, `*.bin`, `*.safetensors`) or large raster datasets to Git. Checkpoint exports must be logged in `backend/models/model_registry.json`.

---

## 4. Running Tests & Quality Verification

Before submitting a Pull Request, verify that all checks pass:

```powershell
# Run backend tests
cd backend
.venv\Scripts\activate
pytest -v

# Run frontend linting
cd ../frontend
npm run build
```

---

## 5. Commit Standards & Pull Requests

- Use conventional commits:
  - `feat: add new SAR backscatter calibration tool`
  - `fix: resolve affine transform calculation in area tool`
  - `docs: update model registry metrics`
  - `test: add integration test for optical-sar fusion`
- Ensure all tests pass.
- Open a PR against `main` with a clear explanation of changes, test results, and any relevant screenshots.
