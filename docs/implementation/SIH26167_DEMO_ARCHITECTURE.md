# Astra AI / SatQuery AI — System Architecture & Capabilities Guide

**SIH Problem Statement:** SIH26167 — *SatQuery AI: An Interactive Vision-Language Assistant for Multimodal Remote Sensing Image Analysis through Text Queries*  
**Organization:** Indian Space Research Organisation (ISRO) / Space Applications Centre (SAC)  
**System Version:** 2.0 (SIH Demonstration Ready)  

---

## 1. Architectural Philosophy

Astra AI is an **agentic remote-sensing intelligence layer** designed to transform unstructured natural-language queries into specialized remote-sensing analyses and auditable geospatial reports.

### What Astra IS:
- A multi-specialist vision-language platform for multimodal satellite observations (Optical multispectral + Synthetic Aperture Radar).
- An agentic orchestrator that decomposes user queries into executable dependency plans without hardcoded pipelines.
- A deterministic measurement system where physical quantities (area, bounds, distance) are calculated mathematically by geometric tools, not hallucinated by large language models.
- An evidence-first intelligence system where every answer is backed by verifiable masks, bounding boxes, or calibrated model probabilities.

### What Astra IS NOT:
- The 3D Earth globe is **not** the product — it is an intuitive geographic discovery and disaster context interface.
- Gemini is **not** the specialist computer vision model — it acts solely as the high-level task planner and senior report synthesizer.
- The disaster feed is **not** a predictive or emergency dispatch simulator — it ingests verified real-time events from USGS, NASA EONET, and NOAA.

---

## 2. End-to-End System Dataflow

```
┌─────────────────────────────────────────────────────────────┐
│                         EARTH VIEW                          │
│   (Real-time USGS / NASA EONET / NOAA Disaster Discovery)   │
└──────────────────────────────┬──────────────────────────────┘
                               │ User selects real event & clicks
                               │ "ANALYZE WITH SATQUERY AI"
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                    TARGET EVENT / AOI                       │
│  (Latitude, Longitude, Place, Magnitude, Source Provenance)  │
└──────────────────────────────┬──────────────────────────────┘
                               │ Context passed via bridge
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                        SATQUERY AI                          │
│        (Interactive Analysis Workspace: Single /            │
│         Bi-Temporal / Cross-Modal Imagery Ingest)           │
└──────────────────────────────┬──────────────────────────────┘
                               │ User query (e.g. "What changed between
                               │ these two images and how much area?")
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                    GEMINI PLANNER                           │
│  (Intent Understanding, Modality Verification, Dynamic      │
│   Dependency Planning, Deterministic Fallback Engine)       │
└──────────────────────────────┬──────────────────────────────┘
                               │ Routes tasks strictly through
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                   SPECIALIST REGISTRY                       │
│  (Static Model & Deterministic Geospatial Tool Catalog)     │
└──────────────┬──────────────────────────────┬───────────────┘
               │ Dispatches to                │ Dispatches to
               ▼                              ▼
┌──────────────────────────────┐ ┌────────────────────────────┐
│      SPECIALIST MODELS       │ │    DETERMINISTIC TOOLS     │
│ - ben-scene-classifier       │ │ - area-calculator          │
│   (ResNet-50 v2, 19 LULC)    │ │ - bbox-area-calculator     │
│ - bit-change-detection       │ │ - polygon-area-calculator  │
│   (Siamese BIT Transformer)  │ │ - geodesic-distance-calc   │
│ - cdvqa-specialist (CD-VQA)  │ │ - raster-metadata          │
│ - cross-modal-specialist     │ │ - raster-stats             │
│ - vrsbench-caption           │ │ - sar-stats                │
│ - vrsbench-grounding         │ │ - ndvi-calculator          │
│ - rsvqa-specialist           │ │ - mask-overlay             │
└──────────────┬───────────────┘ └────────────┬───────────────┘
               │                              │
               └──────────────┬───────────────┘
                              │ Standardized outputs
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      EVIDENCE LAYER                         │
│  (Calibrated Confidence, Conflict Detection, Visual Masks,  │
│   Bounding Boxes, Execution Trace, 0% FAILED badges)        │
└──────────────────────────────┬──────────────────────────────┘
                               │ Structured Evidence Package
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                  SENIOR REPORT SYNTHESIZER                  │
│  (Factual Gemini 13-Section Synthesis / Deterministic       │
│   [FALLBACK SYNTHESIS] Engine with Strict CRS Provenance)   │
└──────────────────────────────┬──────────────────────────────┘
                               │ Downloadable Audit Artifacts
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                     AUDITABLE REPORT                        │
│         (Interactive UI / Markdown Export / HTML)           │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. What the System CAN Do (Verified Capabilities)

| Capability Area | Details & Mechanism | Grounding / Accuracy |
| :--- | :--- | :--- |
| **Land Cover Classification (LULC)** | 19 Corine Land Cover classes mapped via fine-tuned ResNet-50 v2 on BigEarthNet-S2. | Temperature calibrated ($T=3.1515$); 0.99 AUC-ROC on validation set. |
| **Bi-Temporal Change Detection** | Siamese ResNet-18 BIT architecture generates precise binary change masks across co-registered $T_1$ and $T_2$ optical scenes. | Grounded pixel change map output; visual overlay generated. |
| **Bi-Temporal Change VQA** | Answers specific questions regarding temporal shifts (e.g., changes in industrial units or water boundaries). | Conditioned on Siamese difference tokens and LULC class shift distributions. |
| **Deterministic Area Calculation** | Exact real-world area calculation of change masks or bounding boxes in square meters ($m^2$), square kilometers ($km^2$), and hectares ($ha$). | Strictly deterministic ($1.0$ confidence status) computed from image GSD and CRS geometry. Zero LLM guessing. |
| **Referring Expression Grounding** | Predicts spatial bounding boxes for structures, storage tanks, and runways specified in natural language. | Output normalized coordinates `[ymin, xmin, ymax, xmax]`. |
| **Scene Captioning** | Multi-sentence natural language narrative describing landscape, infrastructure, and environmental patterns. | Grounded in remote-sensing VLM features. |
| **Optical + SAR Cross-Modal Fusion** | Multi-sensor reasoning comparing optical reflectance with synthetic aperture radar (SAR) microwave backscatter. | Distinguishes surface roughness, dielectric permittivity, and urban double-bounce reflections. |
| **Vegetation Indexing** | Deterministic NDVI calculation across multispectral Red and NIR bands. | Mathematical matrix calculation; NDVI raster and distribution statistics. |
| **Real-Time Disaster Discovery** | Live ingest of global earthquakes (USGS), wildfires/storms (NASA EONET), and space weather (NOAA). | 100% verified provenance; exact signed coordinates and official event links. |
| **Audit-Grade Reporting** | Generates exportable 13-section Markdown and HTML reports with execution traces and provenance. | Separates source metadata, model outputs, calculations, and limitations. |
| **Failure Transparency** | Explicitly marks failed specialists as `SPECIALIST STATUS: FAILED / UNAVAILABLE` with `0.0` confidence and labels unassisted responses as `[FALLBACK SYNTHESIS]`. | Prevents artificial high-confidence illusion on degraded execution. |

---

## 4. What the System CANNOT Reliably Do (Honest Technical Limitations)

To uphold the highest standards of scientific and operational integrity, Astra AI explicitly documents what it cannot do:

1. **Individual Person / Human Detection (Phase 13 Guardrail):**
   - **Limitation:** Satellite imagery (even high-resolution commercial imagery at 30cm to 50cm GSD, and especially open Sentinel-2 at 10m GSD) cannot reliably resolve individual human beings.
   - **System Behavior:** When queried about people, casualties, victims, or individual survivors, the system enforces a strict guardrail:
     > *"Individual-person detection is not currently supported reliably for this imagery and resolution."*
   - It will never fabricate casualty counts, victim locations, or rescue priorities.

2. **Automated Casualty / Triage Estimation:**
   - The system detects physical structural change and land cover transitions. It does not infer medical casualties or mortality figures from visual devastation.

3. **Emergency Dispatch / Rescue Routing:**
   - Astra is an Earth observation analytics platform, not an emergency vehicle routing engine or dispatch coordinator.

4. **Guaranteed Damage Classification Without In-Situ Validation:**
   - A change mask identifies physical differences between two dates (spectral and textural shift). It cannot definitively prove internal structural integrity without ground engineering surveys or very high-resolution oblique aerial reconnaissance.

5. **Cloud Penetration with Optical Imagery:**
   - Optical multispectral sensors cannot penetrate cloud cover. For cloud-occluded scenes, the system prompts for SAR imagery or marks optical features as occluded.

6. **Sub-Pixel Georeferencing of Non-Geospatial Formats:**
   - If an image lacks an embedded CRS or world file (e.g. plain PNG/JPEG without spatial tags), the system explicitly warns:
     > *"CRS not available in source image."*
   - Coordinates provided by external disaster feeds are credited to the source and never falsely attributed to the image pixels.

---

## 5. Flagship SIH Evaluator Demonstration Workflows

### Flagship 1: Disaster Change Analysis (Pre/Post Event Pair)
1. **Find Event:** Open **Earth View**, navigate to an active disaster (e.g., Chile Earthquake or California Wildfire). Click event pointer to view magnitude, depth, and USGS provenance.
2. **Transfer Context:** Click **"Analyze with SatQuery AI"**. Coordinates, event type, and place name transfer seamlessly into the analysis workspace.
3. **Query System:** Upload pre-event ($T_1$) and post-event ($T_2$) satellite scenes and prompt:
   > *"What changed between these two images, where did the change occur, and approximately how much area was affected?"*
4. **Observe Execution:**
   - Planner detects bi-temporal query $\rightarrow$ selects `bit-change-detection` + `change-area` + `cdvqa-specialist`.
   - BIT generates change mask.
   - Deterministic tool calculates exact changed area in hectares and $km^2$ (labeled `DETERMINISTIC`).
   - Senior analyst synthesizes grounded narrative.
   - User downloads auditable investigation report.

### Flagship 2: Optical + SAR Cross-Modal Ingest
1. **Ingest Modalities:** Upload co-registered optical RGB/multispectral image and Sentinel-1 SAR image.
2. **Query System:**
   > *"Compare the optical and SAR observations and explain what additional information the SAR image provides."*
3. **Observe Execution:**
   - Planner selects `cross-modal-specialist` + `sar-stats`.
   - Distinguishes optical reflectance from microwave radar backscatter (dB).
   - Identifies double-bounce urban structures and surface water roughness invariant to cloud cover.

### Flagship 3: Single-Image Land Cover Scene Classification
1. **Ingest Scene:** Upload a single Sentinel-2 optical scene.
2. **Query System:**
   > *"What is the dominant land cover in this image?"*
3. **Observe Execution:**
   - Planner routes to `ben-scene-classifier` (ResNet-50 v2).
   - Generates calibrated multi-label probabilities across Corine Land Cover taxonomy.
