# Astra AI 2026 — Comprehensive Setup & Installation Guide

This document provides step-by-step instructions to set up, configure, test, and run the complete Astra AI (SatQuery AI) stack locally or in the cloud.

---

## 1. System Requirements

### Hardware
- **Processor**: Modern x86_64 CPU (Intel i5/i7/i9 or AMD Ryzen 5/7/9).
- **RAM**: Minimum 16 GB RAM (32 GB recommended for raster tiling).
- **GPU (Optional but Recommended)**: NVIDIA RTX 30/40/50 Series GPU with 8GB+ VRAM (e.g., RTX 5060, RTX 4070). 
  - *Note*: If no GPU is available, the system automatically falls back to CPU execution or can be run via Google Colab.
- **Disk Space**: 10 GB free disk space (excluding raw datasets).

### Software
- **Operating System**: Windows 11 / Windows 10 (PowerShell 7+ recommended) or Linux (Ubuntu 22.04+).
- **Python**: Version 3.11+ (Python 3.11.x verified).
- **Node.js**: Version 18.x or 20.x LTS.
- **Git**: 2.30+.

---

## 2. Quick Start: One-Click Windows Launch

If running on Windows with an NVIDIA GPU:

```powershell
# From the repository root
.\launch.ps1
```

The launcher automatically:
1. Validates GPU availability via `nvidia-smi`.
2. Creates and activates the backend Python virtual environment (`backend/.venv`).
3. Installs backend dependencies from `backend/requirements.txt`.
4. Validates `.env` presence.
5. Starts the FastAPI server on `http://localhost:8000`.

---

## 3. Manual Step-by-Step Installation

### Step 3.1: Environment Configuration
1. In the repository root, copy `.env.example` to `.env`:
   ```powershell
   Copy-Item .env.example .env
   ```
2. Copy `.env.example` to `backend/.env` as well:
   ```powershell
   Copy-Item backend/.env.example backend/.env
   ```
3. Open `backend/.env` and insert your Gemini API Key:
   ```env
   GEMINI_API_KEY=AIzaSy...your_actual_key_here
   ```

---

### Step 3.2: Backend Setup (FastAPI & AI Models)

```powershell
# Navigate to backend directory
cd backend

# Create Python virtual environment
python -m venv .venv

# Activate virtual environment
# On Windows PowerShell:
.\.venv\Scripts\Activate.ps1
# On Linux/macOS:
# source .venv/bin/activate

# Install PyTorch with CUDA support (CUDA 12.1 / 12.8)
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121

# Install core dependencies
pip install -r requirements.txt

# Start the FastAPI server
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

Verify backend health:
```powershell
curl.exe http://localhost:8000/health
```
Expected response:
```json
{
  "status": "online",
  "version": "2.0.0",
  "gpu": {
    "available": true,
    "name": "NVIDIA GeForce RTX 5060 Laptop GPU"
  }
}
```

Interactive OpenAPI documentation is available at: `http://localhost:8000/docs`.

---

### Step 3.3: Frontend Setup (Next.js 14 App Router)

```powershell
# Navigate to frontend directory from repository root
cd ../frontend

# Install Node.js packages
npm install

# Start development server
npm run dev
```

The application will be live at: `http://localhost:3000`.

---

## 4. Alternative: Google Colab + Cloudflare Tunnel (Free GPU)

For environments without an NVIDIA GPU, Astra includes a fully automated Colab notebook:

1. Open [Astra_Colab_Backend.ipynb](../Astra_Colab_Backend.ipynb) in Google Colab.
2. Select **Runtime → Change runtime type → T4 GPU → Save**.
3. Run all cells (`Ctrl + F9`).
4. The notebook starts FastAPI, provisions an instant Cloudflare Tunnel (`https://xxxx.trycloudflare.com`), and generates a 1-click pairing URL for the frontend.

---

## 5. Running the Test Suite

```powershell
cd backend
.\.venv\Scripts\Activate.ps1

# Run unit tests
pytest tests/test_validator.py tests/test_metadata.py -v

# Run model provenance and checkpoint tests
pytest tests/test_model_provenance_audit.py -v

# Run report synthesis and regression tests
pytest tests/test_report_human_readable_regression.py -v
```

---

## 6. Troubleshooting Common Issues

### Issue 1: `GEMINI_API_KEY` missing
- **Symptom**: `RuntimeError: GEMINI_API_KEY not configured` when running investigation workflows.
- **Fix**: Add a valid Gemini API Key from [Google AI Studio](https://aistudio.google.com/) into `backend/.env`.

### Issue 2: Rasterio / GDAL DLL errors on Windows
- **Symptom**: `ImportError: DLL load failed while importing _base`.
- **Fix**: Install precompiled binary wheels:
  ```powershell
  pip install --force-reinstall rasterio
  ```

### Issue 3: CORS errors in Frontend
- **Symptom**: Browser console logs `Access-Control-Allow-Origin` blocked.
- **Fix**: Ensure your frontend URL (e.g., `http://localhost:3000`) is listed in `ALLOWED_ORIGINS` inside `backend/.env`.
