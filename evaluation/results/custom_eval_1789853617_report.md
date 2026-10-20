# Astra AI — Geospatial Investigation Report
**Problem Statement**: SIH26167 (Space Technology — ISRO)  
**Job ID**: `eval_custom_eval_1789853617_ea7814`  
**Generated At**: 2026-09-19 21:33:43 UTC  
**Overall Confidence**: `0.934`  
**User Query**: *"What changed between these two dates?"*  

---

## 1. Executive Summary
Astra AI analyzed the scene for query 'What changed between these two dates?'. Findings: raster_stats: {'filename': 'representative_bitemporal_t1.tif', 'width': 512, 'height': 512, 'band_count': 3, 'dtype': 'uint8', 'crs_epsg': 32643, 'crs_wkt': 'EPSG:32643', 'gsd_x_m': 1.0, 'gsd_y_m': 1.0, 'bounds': {'left': 300000.0, 'bottom': 2499488.0, 'right': 300512.0, 'top': 2500000.0}, 'nodata': None, 'is_geospatial': True, 'modality': 'OPTICAL_RGB'}; text: {'change_percentage': 0.0, 'changed_pixels': 0, 'method': 'BIT'}; measurement: {'subtype': 'area', 'error': 'No mask available for area calculation.'}

## 2. Investigation Narrative
Investigation of query 'What changed between these two dates?' executed across active models and deterministic tools. raster_stats: {'filename': 'representative_bitemporal_t1.tif', 'width': 512, 'height': 512, 'band_count': 3, 'dtype': 'uint8', 'crs_epsg': 32643, 'crs_wkt': 'EPSG:32643', 'gsd_x_m': 1.0, 'gsd_y_m': 1.0, 'bounds': {'left': 300000.0, 'bottom': 2499488.0, 'right': 300512.0, 'top': 2500000.0}, 'nodata': None, 'is_geospatial': True, 'modality': 'OPTICAL_RGB'}; text: {'change_percentage': 0.0, 'changed_pixels': 0, 'method': 'BIT'}; measurement: {'subtype': 'area', 'error': 'No mask available for area calculation.'}

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

> **Note on Calculation Certainty**: Measurements with `DETERMINISTIC` status (surface areas, distances, NDVI, SAR dB) reflect exact mathematical calculations from the input rasters or masks. Deterministic arithmetic certainty is distinct from upstream AI segmentation or classification confidence.

## 8. Identified Discrepancies & Conflicts
None identified.

## 9. Investigation Methodology
Executed pipeline utilizing: raster-metadata, change-area, bit-change-detection.

### Active Specialist Models Deployed
| Model ID | Architecture | Model Role | Benchmark Dataset | Verified Metrics |
| :--- | :--- | :--- | :--- | :--- |
| `bit-change-detection` | Bitemporal Image Transformer (BIT) with Siamese ResNet-18 backbone | CURRENT_PRODUCTION_MODEL | LEVIR-CD | OA: 96.98%, F1: 69.56% |

- **Deterministic Tools Invoked**: raster-metadata, change-area
- **Total Compute Time**: `6347ms`

## 10. Known Limitations
- Fallback synthesis utilized due to external API state.

## 11. Assumptions & Environmental Factors
- Standard radiometric and geometric projection assumed.

## 12. Confidence Assessment
Overall confidence score: 0.934

## 13. Strategic Recommendations
Review high-probability scene classifications and spectral metrics.

---

## Appendix: Auditable Execution Trace
| Step | Tool / Specialist | Status | Latency | Output Summary |
| :--- | :--- | :--- | :--- | :--- |
| `step_1` | `raster-metadata` | **SUCCESS** | 2ms | Extracted metadata (3 bands) |
| `step_2` | `bit-change-detection` | **SUCCESS** | 4321ms | {'changed': False, 'change_percentage': 0.0, 'changed_pixels': 0, 'total_pixels' |
| `step_3` | `change-area` | **SUCCESS** | 1ms |  |
| `step_4` | `cdvqa-specialist` | **FAILED** | 2023ms |  |
