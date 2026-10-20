# Astra AI — Geospatial Investigation Report
**Problem Statement**: SIH26167 (Space Technology — ISRO)  
**Job ID**: `eval_custom_eval_1789853606_021380`  
**Generated At**: 2026-09-19 21:33:30 UTC  
**Overall Confidence**: `0.794`  
**User Query**: *"What type of land cover dominates this scene?"*  

---

## 1. Executive Summary
Astra AI analyzed the scene for query 'What type of land cover dominates this scene?'. Findings: raster_stats: {'filename': 'representative_cartosat_optical.tif', 'width': 512, 'height': 512, 'band_count': 3, 'dtype': 'uint8', 'crs_epsg': 32643, 'crs_wkt': 'EPSG:32643', 'gsd_x_m': 1.0, 'gsd_y_m': 1.0, 'bounds': {'left': 300000.0, 'bottom': 2499488.0, 'right': 300512.0, 'top': 2500000.0}, 'nodata': None, 'is_geospatial': True, 'modality': 'PANCHROMATIC'}; classification: {'labels': ['Coniferous forest'], 'top_predictions': [{'label': 'Coniferous forest', 'probability': 0.5877}, {'label': 'Arable land', 'probability': 0.3818}, {'label': 'Broad-leaved forest', 'probability': 0.0597}, {'label': 'Mixed forest', 'probability': 0.0015}, {'label': 'Coastal wetlands', 'probability': 0.0001}]}

## 2. Investigation Narrative
Investigation of query 'What type of land cover dominates this scene?' executed across active models and deterministic tools. raster_stats: {'filename': 'representative_cartosat_optical.tif', 'width': 512, 'height': 512, 'band_count': 3, 'dtype': 'uint8', 'crs_epsg': 32643, 'crs_wkt': 'EPSG:32643', 'gsd_x_m': 1.0, 'gsd_y_m': 1.0, 'bounds': {'left': 300000.0, 'bottom': 2499488.0, 'right': 300512.0, 'top': 2500000.0}, 'nodata': None, 'is_geospatial': True, 'modality': 'PANCHROMATIC'}; classification: {'labels': ['Coniferous forest'], 'top_predictions': [{'label': 'Coniferous forest', 'probability': 0.5877}, {'label': 'Arable land', 'probability': 0.3818}, {'label': 'Broad-leaved forest', 'probability': 0.0597}, {'label': 'Mixed forest', 'probability': 0.0015}, {'label': 'Coastal wetlands', 'probability': 0.0001}]}

## 3. Spatial Findings & Geography
Spatial metadata and coordinates successfully resolved from image headers.

## 4. Temporal Analysis & Change Findings
Single image analyzed; temporal baseline established.

## 5. SAR Microwave Evidence
N/A - Optical analysis pipeline.

## 6. Optical & SAR Cross-Modal Synthesis
N/A

## 7. Verified Findings Provenance
| Finding Type | Source Engine | Confidence | Extracted Evidence |
| :--- | :--- | :--- | :--- |
| `raster_stats` | `raster-metadata` | DETERMINISTIC | {'filename': 'representative_cartosat_optical.tif', 'width': 512, 'height': 512, 'band_count': 3, 'dtype': 'uint8', 'crs |
| `classification` | `ben-scene-classifier` | 58% (CALIBRATED_PROBABILITY) | {'labels': ['Coniferous forest'], 'top_predictions': [{'label': 'Coniferous forest', 'probability': 0.5877}, {'label': ' |

> **Note on Calculation Certainty**: Measurements with `DETERMINISTIC` status (surface areas, distances, NDVI, SAR dB) reflect exact mathematical calculations from the input rasters or masks. Deterministic arithmetic certainty is distinct from upstream AI segmentation or classification confidence.

## 8. Identified Discrepancies & Conflicts
None identified.

## 9. Investigation Methodology
Executed pipeline utilizing: raster-metadata, ben-scene-classifier.

### Active Specialist Models Deployed
| Model ID | Architecture | Model Role | Benchmark Dataset | Verified Metrics |
| :--- | :--- | :--- | :--- | :--- |
| `ben-scene-classifier` | ResNet-50 | CURRENT_PRODUCTION_MODEL | BigEarthNet v2.0 (reBEN) | Val Acc: 91.79%, Macro F1: 0.7038 (Calibrated T=3.1515, NLL 0.3263) |

- **Deterministic Tools Invoked**: raster-metadata
- **Total Compute Time**: `3955ms`

## 10. Known Limitations
- Fallback synthesis utilized due to external API state.

## 11. Assumptions & Environmental Factors
- Standard radiometric and geometric projection assumed.

## 12. Confidence Assessment
Overall confidence score: 0.794

## 13. Strategic Recommendations
Review high-probability scene classifications and spectral metrics.

---

## Appendix: Auditable Execution Trace
| Step | Tool / Specialist | Status | Latency | Output Summary |
| :--- | :--- | :--- | :--- | :--- |
| `step_1` | `raster-metadata` | **SUCCESS** | 1ms | Extracted metadata (3 bands) |
| `step_2` | `ben-scene-classifier` | **SUCCESS** | 3954ms | Classified as: Coniferous forest |
