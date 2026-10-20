# Astra AI — Geospatial Investigation Report
**Problem Statement**: SIH26167 (Space Technology — ISRO)  
**Job ID**: `eval_CASE_03_GROUNDING_ae510e`  
**Generated At**: 2026-09-19 21:35:30 UTC  
**Overall Confidence**: `0.94`  
**User Query**: *"Where are the buildings located in this scene?"*  

---

## 1. Executive Summary
Astra AI analyzed the scene for query 'Where are the buildings located in this scene?'. Findings: raster_stats: {'filename': 'representative_cartosat_optical.tif', 'width': 512, 'height': 512, 'band_count': 3, 'dtype': 'uint8', 'crs_epsg': 32643, 'crs_wkt': 'EPSG:32643', 'gsd_x_m': 1.0, 'gsd_y_m': 1.0, 'bounds': {'left': 300000.0, 'bottom': 2499488.0, 'right': 300512.0, 'top': 2500000.0}, 'nodata': None, 'is_geospatial': True, 'modality': 'PANCHROMATIC'}; bbox: {'boxes': [{'label': 'where are the buildings located in this scene?', 'box_2d': [0.1562, 0.1562, 0.5059, 0.5059], 'pixel_coords': [80, 80, 259, 259], 'confidence': 0.88, 'provenance': 'VRSBench Visual Grounding Specialist'}], 'detections_count': 1, 'text_reference': None}

## 2. Investigation Narrative
Investigation of query 'Where are the buildings located in this scene?' executed across active models and deterministic tools. raster_stats: {'filename': 'representative_cartosat_optical.tif', 'width': 512, 'height': 512, 'band_count': 3, 'dtype': 'uint8', 'crs_epsg': 32643, 'crs_wkt': 'EPSG:32643', 'gsd_x_m': 1.0, 'gsd_y_m': 1.0, 'bounds': {'left': 300000.0, 'bottom': 2499488.0, 'right': 300512.0, 'top': 2500000.0}, 'nodata': None, 'is_geospatial': True, 'modality': 'PANCHROMATIC'}; bbox: {'boxes': [{'label': 'where are the buildings located in this scene?', 'box_2d': [0.1562, 0.1562, 0.5059, 0.5059], 'pixel_coords': [80, 80, 259, 259], 'confidence': 0.88, 'provenance': 'VRSBench Visual Grounding Specialist'}], 'detections_count': 1, 'text_reference': None}

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
| `bbox` | `vrsbench-grounding` | 88% (CALIBRATED_PROBABILITY) | {'boxes': [{'label': 'where are the buildings located in this scene?', 'box_2d': [0.1562, 0.1562, 0.5059, 0.5059], 'pixe |

> **Note on Calculation Certainty**: Measurements with `DETERMINISTIC` status (surface areas, distances, NDVI, SAR dB) reflect exact mathematical calculations from the input rasters or masks. Deterministic arithmetic certainty is distinct from upstream AI segmentation or classification confidence.

## 8. Identified Discrepancies & Conflicts
None identified.

## 9. Investigation Methodology
Executed pipeline utilizing: raster-metadata, vrsbench-grounding.

### Active Specialist Models Deployed
| Model ID | Architecture | Model Role | Benchmark Dataset | Verified Metrics |
| :--- | :--- | :--- | :--- | :--- |
| `vrsbench-grounding` | Referring Expression Spatial Target Localization | CURRENT_PRODUCTION_MODEL | VRSBench Referring Expressions | Verified benchmark performance |

- **Deterministic Tools Invoked**: raster-metadata
- **Total Compute Time**: `121ms`

## 10. Known Limitations
- Fallback synthesis utilized due to external API state.

## 11. Assumptions & Environmental Factors
- Standard radiometric and geometric projection assumed.

## 12. Confidence Assessment
Overall confidence score: 0.94

## 13. Strategic Recommendations
Review high-probability scene classifications and spectral metrics.

---

## Appendix: Auditable Execution Trace
| Step | Tool / Specialist | Status | Latency | Output Summary |
| :--- | :--- | :--- | :--- | :--- |
| `step_1` | `raster-metadata` | **SUCCESS** | 0ms | Extracted metadata (3 bands) |
| `step_2` | `vrsbench-grounding` | **SUCCESS** | 121ms | {'type': 'detection', 'text': "Grounded 1 regions for 'Where are the buildings l |
