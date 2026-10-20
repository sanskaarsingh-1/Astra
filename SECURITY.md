# Security Policy — Astra AI 2026

The Astra AI project is committed to maintaining robust security, data privacy, and responsible AI practices for geospatial remote-sensing intelligence.

---

## 1. Supported Versions

| Subsystem | Version | Supported |
| :--- | :--- | :--- |
| Astra AI Core (FastAPI / Next.js) | 2.0.x / 2026 Release | :white_check_mark: |
| SatQuery AI Orchestration | 2.0.x | :white_check_mark: |
| Legacy Baselines (ResNet-50 v1) | 1.0.x | :x: (Deprecated) |

---

## 2. Reporting a Vulnerability

If you discover a security vulnerability, credential leak, or critical bug in this repository:

1. **DO NOT open a public GitHub issue.**
2. Send a confidential report to the project maintainers with:
   - A description of the vulnerability.
   - Steps to reproduce or proof-of-concept.
   - Potential impact and affected subsystems.
3. Maintainers will acknowledge receipt within 48 hours and coordinate remediation.

---

## 3. Secret Management & Credential Policy

- **Zero Secret Commits**: Real API keys, personal access tokens, database credentials, and service account JSON files must never be committed.
- **Environment Isolation**: All configuration is managed via `.env` files loaded at runtime and strictly ignored by `.gitignore`.
- **Pre-Commit Auditing**: The repository enforces pattern exclusions for `.env`, `.env.*`, `*.pem`, `*.key`, `*service*account*.json`, and `*credentials*.json`.
- **Immediate Credential Revocation**: If any secret is accidentally exposed, it must be rotated immediately at the provider (Google Cloud, GitHub, NVIDIA, etc.) and revoked.

---

## 4. Responsible Remote-Sensing AI Policy

- **No Unauthorized High-Resolution Surveillance**: Astra AI is designed for macro-level environmental, agricultural, and disaster intelligence using public earth observation data (Sentinel-1, Sentinel-2, Landsat, Cartosat-2S, RISAT-1A).
- **Zero Hallucination Guardrails**: Quantitative metrics (e.g., burned hectares, flooded surface area, distance) are strictly computed deterministically via `rasterio` and coordinate geometry. LLMs are prohibited from inventing measurements.
- **Physical Resolution Boundaries**: The system explicitly enforces boundaries; tasks requiring sub-meter human or casualty detection are rejected as physically invalid on macro-satellite sensors.
