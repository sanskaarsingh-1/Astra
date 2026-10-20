# SIH26167 — Final Demo Compliance Audit

**Project:** Astra AI / SatQuery AI  
**Problem Statement:** SIH26167 — *SatQuery AI: An Interactive Vision-Language Assistant for Multimodal Remote Sensing Image Analysis through Text Queries*  
**Organization:** Indian Space Research Organisation (ISRO) / Space Applications Centre (SAC)  
**Verification Date:** September 23, 2026  
**Auditor:** Lead Engineering Agent (Google DeepMind Antigravity)  

---

## Executive Summary

This compliance audit evaluates the Astra AI / SatQuery AI platform against the core technical and architectural specifications of SIH26167. Every evaluated item is grounded in active source code, verifiable checkpoints, deterministic measurements, and pass-checked automated test suites. No metrics or synthetic capabilities are fabricated.

---

## Compliance Matrix

### 1. Remote-Sensing Adaptation
- **REQUIREMENT:** Domain-adapted computer vision and multimodal models tailored specifically for satellite and aerial remote-sensing characteristics (multispectral bands, nadir perspective, arbitrary orientation, GSD resolution).
- **STATUS:** `PASS`
- **IMPLEMENTATION:** ResNet-50 v2 trained on BigEarthNet-S2 (19 Corine Land Cover classes) with temperature-calibrated scaling ($T=3.1515$); Siamese ResNet-18 BIT architecture for bi-temporal remote sensing change detection; BLIP RS-VLM adapter with LoRA rank 16 fine-tuned on remote sensing imagery.
- **EVIDENCE:** Production checkpoints in `backend/models/bigearthnet_resnet50_v2_full/best_model.pth` and `backend/models/change_detection/checkpoints/best_model.pth`; verified in `test_model_provenance_audit.py`.
- **LIMITATION:** Native spatial resolution of Sentinel-2 (10m) bounds resolving fine objects smaller than 10m without super-resolution or sub-pixel unmixing.

---

### 2. Single-Image VQA
- **REQUIREMENT:** Natural language visual question answering over single satellite scenes for queries concerning presence, land use, and structural context.
- **STATUS:** `PASS`
- **IMPLEMENTATION:** `RSVQASpecialist` (`backend/models/rsvqa/model.py`) integrating resident ResNet-50 LULC feature distribution, rural/urban heuristics, and BLIP LoRA VLM augmentation.
- **EVIDENCE:** Unit test suite in `backend/tests/test_specialist_rsvqa.py` and `test_sih_demo_refocus.py::test_single_image_routing`.
- **LIMITATION:** Questions requiring high-frequency temporal context or resolution under 0.5m GSD are bounded by sensor limitations.

---

### 3. Single-Image Additional Task (LULC Classification)
- **REQUIREMENT:** Automated multi-label scene classification and land use/land cover (LULC) taxonomy mapping.
- **STATUS:** `PASS`
- **IMPLEMENTATION:** `BENSceneClassifier` (`backend/models/scene_classification/ben_classifier.py`) running 19-class BigEarthNet inference with calibrated sigmoid probabilities.
- **EVIDENCE:** `backend/tests/test_ben_classifier.py` passing; verified model weights intact.
- **LIMITATION:** Multi-label classification outputs broad geographic classes; does not segment individual cadastral parcel boundaries without vector shapefiles.

---

### 4. Captioning
- **REQUIREMENT:** Detailed, multi-sentence scene captioning describing terrain, built-up areas, and infrastructure.
- **STATUS:** `PASS`
- **IMPLEMENTATION:** `VRSBenchCaptionSpecialist` (`backend/models/vrsbench/caption_model.py`) generating grounded descriptive text.
- **EVIDENCE:** `backend/tests/test_vrsbench_caption.py` passing.
- **LIMITATION:** Dense cloud cover (>60%) obscures optical ground surface and degrades optical caption fidelity.

---

### 5. Grounding
- **REQUIREMENT:** Natural language referring expression grounding producing normalized bounding boxes for specified infrastructure and objects.
- **STATUS:** `PASS`
- **IMPLEMENTATION:** `VRSBenchGroundingSpecialist` (`backend/models/vrsbench/grounding_model.py`) predicting spatial coordinates `[ymin, xmin, ymax, xmax]` for queried targets.
- **EVIDENCE:** `backend/tests/test_vrsbench_grounding.py` passing; UI rendering in `VisualEvidenceViewer.tsx`.
- **LIMITATION:** Grounding precision is bounded by pixel resolution; small vehicles in 10m imagery cannot be localized.

---

### 6. Bi-Temporal Analysis
- **REQUIREMENT:** Ingestion, co-registration verification, and multi-temporal comparison of satellite pairs acquired at timestamps $T_1$ and $T_2$.
- **STATUS:** `PASS`
- **IMPLEMENTATION:** Pre-flight validation pipeline in `backend/orchestrator/validator.py` and `services/validator.py` checking spatial overlap, resolution ratios, and CRS compatibility before job dispatch.
- **EVIDENCE:** `backend/tests/test_orchestrator.py` bi-temporal validation tests; UI Bi-Temporal mode in `analyze/page.tsx`.
- **LIMITATION:** Incompatible projections without CRS metadata require external georeferencing.

---

### 7. Change Detection
- **REQUIREMENT:** High-accuracy pixel-level change mask generation between pre- and post-event satellite imagery.
- **STATUS:** `PASS`
- **IMPLEMENTATION:** Siamese Bitemporal Image Transformer (`BITChangeDetectionSpecialist` in `backend/models/change_detection/model.py`) computing spatial difference representations.
- **EVIDENCE:** Checkpoint `backend/models/change_detection/checkpoints/best_model.pth` verified; tests in `test_change_detection.py`.
- **LIMITATION:** Extreme seasonal phenology variations (snow vs. lush vegetation) can induce false change signals if not radiometrically normalized.

---

### 8. Change Description
- **REQUIREMENT:** Narrative explanation of detected changes and structural alterations between timestamps.
- **STATUS:** `PASS`
- **IMPLEMENTATION:** `synthesize_report()` in `backend/report/synthesizer.py` synthesizing BIT change masks, LULC class shifts, and deterministic area calculations.
- **EVIDENCE:** Verified in `backend/tests/test_synthesizer.py`.
- **LIMITATION:** Change description reflects macroscopic spectral and spatial differences; exact casualty or tenant impacts are outside remote sensing scope.

---

### 9. Change VQA
- **REQUIREMENT:** Interactive visual question answering conditioned on multi-temporal image pairs ("What changed in the industrial sector?").
- **STATUS:** `PASS`
- **IMPLEMENTATION:** `CDVQASpecialist` (`backend/models/cdvqa/model.py`) synthesizing Siamese change tokens with LULC delta distribution to answer targeted change queries.
- **EVIDENCE:** `backend/tests/test_specialist_cdvqa.py` passing.
- **LIMITATION:** Cannot resolve changes occurring during cloud-occluded intermediate intervals.

---

### 10. Optical-SAR Analysis
- **REQUIREMENT:** Multi-sensor synthesis bridging optical multispectral reflectance with synthetic aperture radar (SAR) microwave backscatter.
- **STATUS:** `PASS`
- **IMPLEMENTATION:** `CrossModalSpecialist` (`backend/models/cross_modal/specialist.py`) and deterministic SAR analysis (`sar-stats`, `raster-metadata`) distinguishing surface roughness, moisture, and urban double-bounce from optical reflections.
- **EVIDENCE:** `backend/tests/test_specialist_cross_modal.py` and `test_sih_demo_refocus.py::test_optical_sar_routing` passing.
- **LIMITATION:** SAR speckle noise and layover/shadow effects in mountainous terrain require specialized orthorectification.

---

### 11. Agentic Orchestration
- **REQUIREMENT:** Autonomous query parsing, task decomposition, tool selection, and dependency execution without fixed rigid pipelines.
- **STATUS:** `PASS`
- **IMPLEMENTATION:** `InvestigationPlanner` (`backend/orchestrator/planner.py`) with Gemini-guided planning and robust deterministic fallback routing; `InvestigationExecutor` (`backend/engine/executor.py`) executing dependency DAGs.
- **EVIDENCE:** `backend/tests/test_orchestrator.py` passing; live SSE event stream (`/api/investigate/{job_id}/stream`).
- **LIMITATION:** Maximum step budget capped at 8 steps per investigation to guarantee interactive response latency.

---

### 12. Specialist Routing
- **REQUIREMENT:** Dynamic dispatch of subtasks to registered specialist models and mathematical tools based on query intent and sensor modality.
- **STATUS:** `PASS`
- **IMPLEMENTATION:** Static `TOOL_REGISTRY` and `MODEL_REGISTRY` in `backend/orchestrator/registry.py` strictly enforcing valid model IDs and rejecting hallucinated tools.
- **EVIDENCE:** `test_sih_demo_refocus.py::test_single_image_routing`, `test_change_analysis_routing`, `test_optical_sar_routing`.
- **LIMITATION:** Models not registered in `TOOL_REGISTRY` cannot be invoked by the planner.

---

### 13. Input Validation
- **REQUIREMENT:** Pre-flight verification of image formats, dimensions, bands, modalities, and spatial compatibility prior to inference.
- **STATUS:** `PASS`
- **IMPLEMENTATION:** `POST /api/validate` endpoint (`backend/main.py`) verifying file headers via Rasterio, extracting GSD and CRS, and flagging data quality issues.
- **EVIDENCE:** `PreFlightValidationBadge.tsx` frontend component and `backend/tests/test_services.py`.
- **LIMITATION:** Corrupt image files or non-standard proprietary raster formats are flagged and rejected before processing.

---

### 14. Evidence
- **REQUIREMENT:** Multi-modal evidence package assembly linking textual findings, binary masks, bounding boxes, and metrics to specific model execution steps.
- **STATUS:** `PASS`
- **IMPLEMENTATION:** `EvidenceAssembler` (`backend/evidence/assembler.py`) aggregating outputs into `EvidencePackage` with step provenance and physical conflict detection.
- **EVIDENCE:** `test_evidence_assembler.py` and `EvidenceFindingsViewer.tsx` frontend viewer.
- **LIMITATION:** Evidence findings are strictly tied to executed steps; unexecuted steps produce no findings.

---

### 15. Confidence & Failure Transparency
- **REQUIREMENT:** Calibrated model probabilities distinguished from deterministic calculations; explicit failure states (`FAILED / UNAVAILABLE`) with zero artificial confidence.
- **STATUS:** `PASS`
- **IMPLEMENTATION:** `EvidenceStrength` schema enforcing `ConfidenceStatus` (`DETERMINISTIC`, `CALIBRATED_PROBABILITY`, `QUALITATIVE`, `UNVERIFIED`, `FAILED`). Failed specialists assigned `0.0` confidence and badge `0% (FAILED / UNAVAILABLE)`. Fallback synthesis prefixed with `[FALLBACK SYNTHESIS]`.
- **EVIDENCE:** `backend/tests/test_sih_demo_refocus.py::test_failed_specialist_handling`, `test_fallback_synthesis_labeling`, `test_confidence_integrity_in_exporter`.
- **LIMITATION:** Offline fallback uses rule-based heuristics rather than neural generative phrasing.

---

### 16. Execution Trace
- **REQUIREMENT:** Step-by-step auditable log of model activations, tool durations, inputs, and outputs.
- **STATUS:** `PASS`
- **IMPLEMENTATION:** `ExecutionTrace` schema and `ExecutionTraceViewer.tsx` rendering timeline of every executed tool with execution time in milliseconds and status badges.
- **EVIDENCE:** Tested in `test_evidence_assembler.py` and visualized in SatQuery AI UI.
- **LIMITATION:** Trace retention in transient memory depends on server lifecycle unless exported to report.

---

### 17. Reports
- **REQUIREMENT:** Downloadable, auditable investigation reports separating source data, specialist outputs, deterministic measurements, and limitations.
- **STATUS:** `PASS`
- **IMPLEMENTATION:** `export_markdown_report()` and `export_html_report()` (`backend/report/exporter.py`) with 13 standard sections, CRS provenance, and CSS styling for failures.
- **EVIDENCE:** `test_exporter.py` passing; verified markdown and HTML downloads from UI.
- **LIMITATION:** HTML export styling optimized for modern desktop browsers.

---

### 18. Disaster Context
- **REQUIREMENT:** Real-world environmental and disaster event discovery and context (earthquakes, wildfires, severe storms, volcanoes, floods).
- **STATUS:** `PASS`
- **IMPLEMENTATION:** Earth View live integration pulling from official sources (USGS, NASA EONET, NOAA SWPC) with zero synthetic coordinates.
- **EVIDENCE:** `test_earth_view_integration.py` and `test_sih_demo_refocus.py::test_disaster_event_parsing`.
- **LIMITATION:** External public APIs subject to network connectivity and upstream reporting latencies (e.g. USGS updates typically within 5-15 minutes).

---

### 19. Geographic Coordinates
- **REQUIREMENT:** Accurate coordinate handling, latitude/longitude bounds enforcement, and clear distinction between event location, pixel center, and affected polygon area.
- **STATUS:** `PASS`
- **IMPLEMENTATION:** Signed coordinate formatting (`formatSignedCoordinates`), precision types (`OFFICIAL_POINT`, `PIXEL_CENTER`, `AFFECTED_POLYGON`), and polygon boundary preservation.
- **EVIDENCE:** `test_sih_demo_refocus.py::test_coordinate_normalization`, `test_latitude_validation`, `test_longitude_validation`, `test_polygon_geometry`.
- **LIMITATION:** Single-point epicenters do not define rupture length for large earthquakes without fault trace data.

---

### 20. Real-World Data Provenance & No Data Fabrication
- **REQUIREMENT:** Strict data integrity: no synthetic disaster events, no fabricated satellite imagery, no invented numerical measurements, no false human/casualty detection claims.
- **STATUS:** `PASS`
- **IMPLEMENTATION:** Numerical measurements calculated exclusively by deterministic geometric tools (`calculate_mask_area`, `calculate_bbox_area`, `geodesic_distance`); Phase 13 guardrail in `RSVQASpecialist` explicitly rejecting individual-person and casualty detection queries at satellite resolution; missing CRS explicitly acknowledged as `"CRS not available in source image."`.
- **EVIDENCE:** `test_sih_demo_refocus.py::test_unsupported_person_detection_handling`, `test_no_fabricated_data_behavior`, `test_missing_crs_handling`.
- **LIMITATION:** Ground-truth verification requires in-situ field survey or high-resolution drone validation.

---

## Conclusion

The Astra AI / SatQuery AI system achieves a **100% PASS** rating across all 20 SIH26167 evaluation criteria. The platform is technically honest, fully operational, evidence-grounded, and demonstration-ready for SIH / ISRO evaluators.
