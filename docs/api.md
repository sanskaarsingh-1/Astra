# Astra AI — Verified REST API Specification

**Base URL**: `http://localhost:8000` (Local) / `https://<tunnel-id>.trycloudflare.com` (Cloud)  
**FastAPI OpenAPI Specification**: `GET /docs` and `GET /openapi.json`

---

## 1. System & Health Endpoints

### `GET /health`
Returns system status, version, and GPU acceleration metadata.
- **Authentication**: None
- **Response `200 OK`**:
  ```json
  {
    "status": "online",
    "version": "2.0.0",
    "gpu": {
      "available": true,
      "name": "NVIDIA GeForce RTX 5060 Laptop GPU",
      "memory_total_mb": 8188,
      "vram_free_gb": 6.8
    }
  }
  ```

### `GET /api/disasters/live`
Fetches real-time environmental events and disaster coordinates from USGS Earthquakes and NASA EONET feeds for the Earth View GIS interface.
- **Authentication**: None
- **Response `200 OK`**: Array of geo-referenced event objects with magnitude, title, coordinates, and sensor recommendations.

### `GET /api/system/status`
Returns real-time resource utilization (CPU, RAM, GPU VRAM) and active job queue counts.
- **Headers**: `X-API-Key: <key>` (if configured)
- **Response `200 OK`**: Detailed hardware telemetry.

---

## 2. Model Registry & Demonstration Cases

### `GET /api/registry`
Returns the machine-readable catalog of all 6 specialist AI models, BLIP LoRA adapters, and 10 deterministic tools with verified benchmark accuracies and architectural parameters.
- **Response `200 OK`**:
  ```json
  {
    "title": "Astra AI Model & Tool Registry",
    "version": "2.0.0",
    "models": {
      "ben-scene-classifier": { ... },
      "bit-change-detection": { ... },
      "rsvqa-specialist": { ... }
    },
    "deterministic_tools": { ... }
  }
  ```

### `GET /api/demo/cases`
Returns the list of 10 curated benchmark evaluation cases covering optical LULC, LEVIR-CD change detection, RISAT-1A SAR fusion, and large raster tiling.

### `GET /api/demo/file/{filename}`
Streams the raw GeoTIFF raster for a demo case.

### `GET /api/demo/preview/{filename}`
Generates and streams an RGB 2%-98% percentile-stretched display-safe PNG preview.

---

## 3. Investigation Orchestration Pipeline

### `POST /api/validate`
Validates uploaded satellite rasters for format integrity, CRS, EPSG affine coordinate matrices, spatial resolution, and bitemporal/cross-modal compatibility.
- **Form Data**:
  - `files`: UploadFile (1 or 2 GeoTIFF rasters)
  - `query`: Text string
- **Response `200 OK`**:
  ```json
  {
    "valid": true,
    "images": [
      {
        "filename": "sentinel2_optical.tif",
        "crs": "EPSG:32643",
        "width": 1024,
        "height": 1024,
        "bands": 4,
        "modality": "optical_multispectral",
        "gsd_meters": 10.0
      }
    ]
  }
  ```

### `POST /api/investigate`
Initiates an asynchronous multi-specialist investigation workflow. Returns `202 Accepted` with a unique `job_id`.
- **Form Data**:
  - `files`: UploadFile (1 or 2 rasters)
  - `query`: Investigation question (e.g., *"What changed between T1 and T2? Calculate burned surface area."*)
- **Response `202 Accepted`**:
  ```json
  {
    "job_id": "7b3a9856-f40c-4e89-b883-93665bc7f03a",
    "status": "pending",
    "message": "Investigation job created and queued."
  }
  ```

### `GET /api/investigate/{job_id}/stream`
Server-Sent Events (SSE) stream delivering real-time execution steps, specialist activations, progress percentages, and log messages.
- **SSE Event Types**:
  - `progress`: Current step status and progress integer (0–100%)
  - `step_complete`: Output from an individual specialist model or deterministic tool
  - `complete`: Final investigation payload ready
  - `error`: Detailed error explanation and failure transparent diagnostic

### `GET /api/investigate/{job_id}/result`
Retrieves the complete structured investigation output.
- **Response `200 OK`**:
  ```json
  {
    "job_id": "7b3a9856-f40c-4e89-b883-93665bc7f03a",
    "status": "completed",
    "query": "...",
    "plan": [ ... ],
    "evidence_package": { ... },
    "synthesis": {
      "summary": "...",
      "confidence_score": 0.94,
      "calibration": {
        "calibrated_confidence": 0.91,
        "temperature": 3.1515
      }
    },
    "deterministic_measurements": {
      "changed_area_ha": 42.85,
      "changed_area_m2": 428500.0,
      "confidence": "DETERMINISTIC_EXACT"
    }
  }
  ```

### `GET /api/report/{job_id}/download?format=markdown|html|json`
Exports the complete auditable investigation report in Markdown, HTML, or structured JSON.

---

## 4. Specialist Model Direct Endpoints

| Endpoint | Method | Specialist Model | Description |
| :--- | :--- | :--- | :--- |
| `/api/specialists/lulc` | POST | ResNet-50 v2 | 19-class Land-Use / Land-Cover multi-label classification |
| `/api/specialists/vqa` | POST | RSVQA Specialist | Remote sensing visual question answering |
| `/api/specialists/caption` | POST | VRSBench Caption | Fine-grained natural language scene descriptions |
| `/api/specialists/grounding` | POST | VRSBench Grounding | Referring expression normalized bounding box localization |
| `/api/specialists/change` | POST | BIT ResNet-18 | Bi-temporal change detection mask and statistics |
| `/api/specialists/change-vqa` | POST | CDVQA Specialist | Change-grounded questions over bitemporal pairs |
| `/api/specialists/optical-sar`| POST | Dual Physical Encoder | Optical reflectance + Microwave radar backscatter reasoning |

---

## 5. Deterministic Geospatial Tools Endpoint

### `POST /api/geospatial/measure`
Direct computation of exact physical metrics without LLM involvement.
- **Payload**:
  ```json
  {
    "operation": "polygon_area",
    "coordinates": [[77.2090, 28.6139], [77.2190, 28.6139], [77.2190, 28.6239], [77.2090, 28.6139]],
    "crs": "EPSG:4326"
  }
  ```
- **Response `200 OK`**:
  ```json
  {
    "operation": "polygon_area",
    "area_sq_meters": 1104820.5,
    "area_hectares": 110.48,
    "method": "PyProj WGS84 Geodesic Ellipsoid (Deterministic)",
    "status": "success"
  }
  ```
