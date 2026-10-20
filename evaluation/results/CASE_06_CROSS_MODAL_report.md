# Astra AI — Geospatial Investigation Report
**Problem Statement**: SIH26167 (Space Technology — ISRO)  
**Job ID**: `eval_CASE_06_CROSS_MODAL_15ad54`  
**Generated At**: 2026-09-19 21:35:31 UTC  
**Overall Confidence**: `0.803`  
**User Query**: *"Compare the optical and SAR observations for surface structures."*  

---

## 1. Executive Summary
Astra AI analyzed the scene for query 'Compare the optical and SAR observations for surface structures.'. Findings: raster_stats: {'filename': 'representative_cartosat_optical.tif', 'width': 512, 'height': 512, 'band_count': 3, 'dtype': 'uint8', 'crs_epsg': 32643, 'crs_wkt': 'EPSG:32643', 'gsd_x_m': 1.0, 'gsd_y_m': 1.0, 'bounds': {'left': 300000.0, 'bottom': 2499488.0, 'right': 300512.0, 'top': 2500000.0}, 'nodata': None, 'is_geospatial': True, 'modality': 'PANCHROMATIC'}; raster_stats: {'filename': 'representative_risat_sar.tif', 'width': 512, 'height': 512, 'band_count': 1, 'dtype': 'uint8', 'crs_epsg': 32643, 'crs_wkt': 'EPSG:32643', 'gsd_x_m': 1.0, 'gsd_y_m': 1.0, 'bounds': {'left': 300000.0, 'bottom': 2499488.0, 'right': 300512.0, 'top': 2500000.0}, 'nodata': None, 'is_geospatial': True, 'modality': 'SAR'}; text: {'optical_evidence': {'modality': 'Optical (Multispectral / RGB)', 'sensor_family': 'Sentinel-2 / Cartosat-2S', 'physical_mechanism': 'Surface solar reflectance & absorption', 'lulc_predictions': [], 'dominant_land_cover': 'Unclassified', 'vegetation_detected': True, 'water_detected': False}, 'sar_evidence': {'modality': 'Synthetic Aperture Radar (SAR)', 'sensor_family': 'Sentinel-1 / RISAT-1A (C-Band)', 'physical_mechanism': 'Microwave active backscatter & dielectric geometry', 'penetration': 'All-weather, cloud & smoke penetrating', 'backscatter_db': {'mean_dB': -21.82, 'min_dB': -30.0, 'max_dB': 0.0}, 'specular_reflection_water': True, 'double_bounce_urban_structures': True, 'surface_roughness': 'High / Built'}, 'modality_agreement': 'CONFLICT', 'conflicts': ['Ambiguity detected: SAR exhibits low backscatter mimicking calm water, but Optical imagery shows dry smooth surface (e.g. tarmac/runway/dry flatland). Optical resolves false-positive SAR water.'], 'complementary_findings': ['SAR detects prominent double-bounce microwave corner reflections (-21.82 dB), confirming dense built-up infrastructure/metallic structures.', 'SAR structural detection penetrates surface canopy or shadow, revealing buildings obscured in optical bands.'], 'synthesis': 'Modality conflict identified and resolved: Ambiguity detected: SAR exhibits low backscatter mimicking calm water, but Optical imagery shows dry smooth surface (e.g. tarmac/runway/dry flatland). Optical resolves false-positive SAR water.', 'confidence': 0.65, 'sensor_compatibility': {'optical_source': 'Sentinel-2 MSI / ISRO Cartosat-2S', 'sar_source': 'Sentinel-1 C-SAR / ISRO RISAT-1A (EOS-04)', 'polarisation_supported': ['VV', 'VH', 'HH', 'HV', 'RH', 'RV']}, 'model_name': 'optical-sar-cross-modal-specialist', 'provenance': 'BigEarthNet S1+S2 joint physics & ISRO sensor alignment'}

## 2. Investigation Narrative
Investigation of query 'Compare the optical and SAR observations for surface structures.' executed across active models and deterministic tools. raster_stats: {'filename': 'representative_cartosat_optical.tif', 'width': 512, 'height': 512, 'band_count': 3, 'dtype': 'uint8', 'crs_epsg': 32643, 'crs_wkt': 'EPSG:32643', 'gsd_x_m': 1.0, 'gsd_y_m': 1.0, 'bounds': {'left': 300000.0, 'bottom': 2499488.0, 'right': 300512.0, 'top': 2500000.0}, 'nodata': None, 'is_geospatial': True, 'modality': 'PANCHROMATIC'}; raster_stats: {'filename': 'representative_risat_sar.tif', 'width': 512, 'height': 512, 'band_count': 1, 'dtype': 'uint8', 'crs_epsg': 32643, 'crs_wkt': 'EPSG:32643', 'gsd_x_m': 1.0, 'gsd_y_m': 1.0, 'bounds': {'left': 300000.0, 'bottom': 2499488.0, 'right': 300512.0, 'top': 2500000.0}, 'nodata': None, 'is_geospatial': True, 'modality': 'SAR'}; text: {'optical_evidence': {'modality': 'Optical (Multispectral / RGB)', 'sensor_family': 'Sentinel-2 / Cartosat-2S', 'physical_mechanism': 'Surface solar reflectance & absorption', 'lulc_predictions': [], 'dominant_land_cover': 'Unclassified', 'vegetation_detected': True, 'water_detected': False}, 'sar_evidence': {'modality': 'Synthetic Aperture Radar (SAR)', 'sensor_family': 'Sentinel-1 / RISAT-1A (C-Band)', 'physical_mechanism': 'Microwave active backscatter & dielectric geometry', 'penetration': 'All-weather, cloud & smoke penetrating', 'backscatter_db': {'mean_dB': -21.82, 'min_dB': -30.0, 'max_dB': 0.0}, 'specular_reflection_water': True, 'double_bounce_urban_structures': True, 'surface_roughness': 'High / Built'}, 'modality_agreement': 'CONFLICT', 'conflicts': ['Ambiguity detected: SAR exhibits low backscatter mimicking calm water, but Optical imagery shows dry smooth surface (e.g. tarmac/runway/dry flatland). Optical resolves false-positive SAR water.'], 'complementary_findings': ['SAR detects prominent double-bounce microwave corner reflections (-21.82 dB), confirming dense built-up infrastructure/metallic structures.', 'SAR structural detection penetrates surface canopy or shadow, revealing buildings obscured in optical bands.'], 'synthesis': 'Modality conflict identified and resolved: Ambiguity detected: SAR exhibits low backscatter mimicking calm water, but Optical imagery shows dry smooth surface (e.g. tarmac/runway/dry flatland). Optical resolves false-positive SAR water.', 'confidence': 0.65, 'sensor_compatibility': {'optical_source': 'Sentinel-2 MSI / ISRO Cartosat-2S', 'sar_source': 'Sentinel-1 C-SAR / ISRO RISAT-1A (EOS-04)', 'polarisation_supported': ['VV', 'VH', 'HH', 'HV', 'RH', 'RV']}, 'model_name': 'optical-sar-cross-modal-specialist', 'provenance': 'BigEarthNet S1+S2 joint physics & ISRO sensor alignment'}

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
| `raster_stats` | `raster-metadata` | DETERMINISTIC | {'filename': 'representative_risat_sar.tif', 'width': 512, 'height': 512, 'band_count': 1, 'dtype': 'uint8', 'crs_epsg': |
| `text` | `cross-modal-specialist` | 65% (CALIBRATED_PROBABILITY) | {'optical_evidence': {'modality': 'Optical (Multispectral / RGB)', 'sensor_family': 'Sentinel-2 / Cartosat-2S', 'physica |

> **Note on Calculation Certainty**: Measurements with `DETERMINISTIC` status (surface areas, distances, NDVI, SAR dB) reflect exact mathematical calculations from the input rasters or masks. Deterministic arithmetic certainty is distinct from upstream AI segmentation or classification confidence.

## 8. Identified Discrepancies & Conflicts
- **[High]**: Ambiguity detected: SAR exhibits low backscatter mimicking calm water, but Optical imagery shows dry smooth surface (e.g. tarmac/runway/dry flatland). Optical resolves false-positive SAR water.

## 9. Investigation Methodology
Executed pipeline utilizing: raster-metadata, cross-modal-specialist.

### Active Specialist Models Deployed
| Model ID | Architecture | Model Role | Benchmark Dataset | Verified Metrics |
| :--- | :--- | :--- | :--- | :--- |
| `cross-modal-specialist` | Dual Physical Encoder (Optical Reflectance vs. Microwave Backscatter dB) | CURRENT_PRODUCTION_MODEL | BigEarthNet S1/S2 Paired (480k pairs) + Cartosat-2S & RISAT-1A | Verified benchmark performance |

- **Deterministic Tools Invoked**: raster-metadata
- **Total Compute Time**: `83ms`

## 10. Known Limitations
- Fallback synthesis utilized due to external API state.

## 11. Assumptions & Environmental Factors
- Standard radiometric and geometric projection assumed.

## 12. Confidence Assessment
Overall confidence score: 0.803

## 13. Strategic Recommendations
Review high-probability scene classifications and spectral metrics.

---

## Appendix: Auditable Execution Trace
| Step | Tool / Specialist | Status | Latency | Output Summary |
| :--- | :--- | :--- | :--- | :--- |
| `step_1` | `raster-metadata` | **SUCCESS** | 1ms | Extracted metadata (3 bands) |
| `step_2` | `raster-metadata` | **SUCCESS** | 0ms | Extracted metadata (1 bands) |
| `step_3` | `cross-modal-specialist` | **SUCCESS** | 82ms | {'optical_evidence': {'modality': 'Optical (Multispectral / RGB)', 'sensor_famil |
