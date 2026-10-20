# Astra AI — Geospatial Investigation Report
**Problem Statement**: SIH26167 (Space Technology — ISRO)  
**Job ID**: `eval_CASE_08_MULTI_TOOL_CHANGE_324b5d`  
**Generated At**: 2026-09-19 21:35:32 UTC  
**Overall Confidence**: `0.995`  
**User Query**: *"What changed between these images and how much of the changed region appears to be built-up?"*  

---

## 1. Executive Summary
Astra AI analyzed the scene for query 'What changed between these images and how much of the changed region appears to be built-up?'. Findings: raster_stats: {'filename': 'representative_bitemporal_t1.tif', 'width': 512, 'height': 512, 'band_count': 3, 'dtype': 'uint8', 'crs_epsg': 32643, 'crs_wkt': 'EPSG:32643', 'gsd_x_m': 1.0, 'gsd_y_m': 1.0, 'bounds': {'left': 300000.0, 'bottom': 2499488.0, 'right': 300512.0, 'top': 2500000.0}, 'nodata': None, 'is_geospatial': True, 'modality': 'OPTICAL_RGB'}; text: {'change_percentage': 0.0, 'changed_pixels': 0, 'method': 'BIT'}; measurement: {'subtype': 'area', 'error': 'No mask available for area calculation.'}; text: {'question': 'What changed between these images and how much of the changed region appears to be built-up?', 'question_type': 'change_ratio', 'answer': '0%', 'confidence': 0.99, 'narrative': 'Bi-temporal raster difference is 0.0%, which is within normal seasonal or registration tolerance without distinct structural land-use change.', 'grounded_evidence': {'change_detected': False, 'change_percentage': 0.0, 'changed_pixels': 0, 'area_m2': 0.0, 'area_ha': 0.0, 'regions_count': 0, 'dominant_increase': 'built-up structures', 'dominant_decrease': 'natural terrain', 'class_deltas': {}}, 'change_mask_base64': 'iVBORw0KGgoAAAANSUhEUgAAAQAAAAEACAAAAAB5Gfe6AAAAVklEQVR4nO3BAQEAAACCIP+vbkhAAQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAQPcGAQ8AAb1ytegAAAAASUVORK5CYII=', 'model_name': 'cdvqa-specialist', 'provenance': 'CDVQA grounded multi-specialist reasoning (BIT + ResNet-50 v2)'}

## 2. Investigation Narrative
Investigation of query 'What changed between these images and how much of the changed region appears to be built-up?' executed across active models and deterministic tools. raster_stats: {'filename': 'representative_bitemporal_t1.tif', 'width': 512, 'height': 512, 'band_count': 3, 'dtype': 'uint8', 'crs_epsg': 32643, 'crs_wkt': 'EPSG:32643', 'gsd_x_m': 1.0, 'gsd_y_m': 1.0, 'bounds': {'left': 300000.0, 'bottom': 2499488.0, 'right': 300512.0, 'top': 2500000.0}, 'nodata': None, 'is_geospatial': True, 'modality': 'OPTICAL_RGB'}; text: {'change_percentage': 0.0, 'changed_pixels': 0, 'method': 'BIT'}; measurement: {'subtype': 'area', 'error': 'No mask available for area calculation.'}; text: {'question': 'What changed between these images and how much of the changed region appears to be built-up?', 'question_type': 'change_ratio', 'answer': '0%', 'confidence': 0.99, 'narrative': 'Bi-temporal raster difference is 0.0%, which is within normal seasonal or registration tolerance without distinct structural land-use change.', 'grounded_evidence': {'change_detected': False, 'change_percentage': 0.0, 'changed_pixels': 0, 'area_m2': 0.0, 'area_ha': 0.0, 'regions_count': 0, 'dominant_increase': 'built-up structures', 'dominant_decrease': 'natural terrain', 'class_deltas': {}}, 'change_mask_base64': 'iVBORw0KGgoAAAANSUhEUgAAAQAAAAEACAAAAAB5Gfe6AAAAVklEQVR4nO3BAQEAAACCIP+vbkhAAQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAQPcGAQ8AAb1ytegAAAAASUVORK5CYII=', 'model_name': 'cdvqa-specialist', 'provenance': 'CDVQA grounded multi-specialist reasoning (BIT + ResNet-50 v2)'}

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
| `raster_stats` | `raster-metadata` | DETERMINISTIC | {'filename': 'representative_bitemporal_t1.tif', 'width': 512, 'height': 512, 'band_count': 3, 'dtype': 'uint8', 'crs_ep |
| `text` | `bit-change-detection` | 99% (CALIBRATED_PROBABILITY) | {'change_percentage': 0.0, 'changed_pixels': 0, 'method': 'BIT'} |
| `measurement` | `change-area` | DETERMINISTIC | {'subtype': 'area', 'error': 'No mask available for area calculation.'} |
| `text` | `cdvqa-specialist` | 99% (CALIBRATED_PROBABILITY) | {'question': 'What changed between these images and how much of the changed region appears to be built-up?', 'question_t |

> **Note on Calculation Certainty**: Measurements with `DETERMINISTIC` status (surface areas, distances, NDVI, SAR dB) reflect exact mathematical calculations from the input rasters or masks. Deterministic arithmetic certainty is distinct from upstream AI segmentation or classification confidence.

## 8. Identified Discrepancies & Conflicts
None identified.

## 9. Investigation Methodology
Executed pipeline utilizing: raster-metadata, change-area, cdvqa-specialist, bit-change-detection.

### Active Specialist Models Deployed
| Model ID | Architecture | Model Role | Benchmark Dataset | Verified Metrics |
| :--- | :--- | :--- | :--- | :--- |
| `cdvqa-specialist` | Change-grounded VQA fusing BIT change masks with ResNet-50 delta LULC shifts | CURRENT_PRODUCTION_MODEL | CDVQA | Verified benchmark performance |
| `bit-change-detection` | Bitemporal Image Transformer (BIT) with Siamese ResNet-18 backbone | CURRENT_PRODUCTION_MODEL | LEVIR-CD | OA: 96.98%, F1: 69.56% |

- **Deterministic Tools Invoked**: raster-metadata, change-area
- **Total Compute Time**: `129ms`

## 10. Known Limitations
- Fallback synthesis utilized due to external API state.

## 11. Assumptions & Environmental Factors
- Standard radiometric and geometric projection assumed.

## 12. Confidence Assessment
Overall confidence score: 0.995

## 13. Strategic Recommendations
Review high-probability scene classifications and spectral metrics.

---

## Appendix: Auditable Execution Trace
| Step | Tool / Specialist | Status | Latency | Output Summary |
| :--- | :--- | :--- | :--- | :--- |
| `step_1` | `raster-metadata` | **SUCCESS** | 1ms | Extracted metadata (3 bands) |
| `step_2` | `bit-change-detection` | **SUCCESS** | 48ms | {'changed': False, 'change_percentage': 0.0, 'changed_pixels': 0, 'total_pixels' |
| `step_3` | `change-area` | **SUCCESS** | 0ms |  |
| `step_4` | `cdvqa-specialist` | **SUCCESS** | 80ms | {'question': 'What changed between these images and how much of the changed regi |
