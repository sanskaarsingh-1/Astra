# Domain Assumptions

## 1. Modality Assumptions
- **Optical RGB**: 3 bands, wavelengths typically 400-700nm. Processed heavily by VLM models (GeoChat).
- **SAR (Synthetic Aperture Radar)**: Typically 1-2 bands (VV, VH, HH, HV). Values are backscatter intensities. NEVER passed to VLMs; they rely exclusively on mathematical statistics (dB analysis).
- **Multispectral**: >= 4 bands. Specifically, Band 3 is assumed to be Red and Band 4 is assumed to be NIR unless band wavelengths/descriptions dictate otherwise.

## 2. Alignment & Preprocessing
- Multi-image tasks (e.g. Change Detection) assume images are roughly co-registered. If CRS mismatch or bounds mismatch, `alignment.py` will attempt to reproject.
- `BITModel` expects normalized 3-channel optical input tensors resized to 256x256. 16-bit raster files will be automatically cast to 8-bit using 2nd and 98th percentile stretching.

## 3. Evidence Strength
- Deterministic tools (like metadata extraction and statistical aggregations) are assigned a confidence of 1.0.
- Machine Learning predictions (GeoChat, BigEarthNet, BITModel) report their calibrated or qualitative confidence (typically 0.4 to 0.95) depending on logit outputs.
- Overall confidence score is an unweighted average minus a penalty for any failed steps in the execution trace.

## 4. Cross-Modal Fusion
- Low backscatter (< -15 dB VV/HH) in SAR strongly correlates with water.
- High backscatter (> -5 dB) strongly correlates with urban / metallic structures.
- Fusion flags a conflict if optical-based vegetation indices (NDVI) indicate water while SAR indicates rough surface, or vice versa.
