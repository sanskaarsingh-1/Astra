# 🧪 Astra AI — Master Test Photos & Prompts Guide
**Project**: SIH26167 — SatQuery AI (ISRO Space Applications Centre)  
**Live Application**: https://sih-orbilens-2026-tm.web.app/analyze  
**Last Updated**: September 2026

---

## 📁 Test Assets Inventory on Disk

All test photos and raster pairs are populated and ready in `live_testing/images/`:

```
live_testing/
├── images/
│   ├── single_image/                         ← Mode 1: Single Image
│   │   ├── 01_urban_fabric_sentinel2.tif
│   │   ├── 02_inland_water_sentinel2.tif
│   │   ├── 03_forest_canopy_sentinel2.tif
│   │   ├── 04_industrial_commercial_sentinel2.tif
│   │   ├── 05_cartosat2s_highres_pan_optical.tif
│   │   ├── 06_rural_agriculture_sentinel2.tif
│   │   ├── 07_regional_large_landscape.tif
│   │   └── PROMPTS.md
│   │
│   ├── bi_temporal/                          ← Mode 2: Bi-Temporal Change Detection
│   │   ├── before/
│   │   │   ├── pair1_urban_construction_t1_2018.png
│   │   │   ├── pair2_residential_expansion_t1.png
│   │   │   ├── pair3_building_change_cdvqa_t1.png
│   │   │   └── pair4_geotiff_satellite_t1.tif
│   │   ├── after/
│   │   │   ├── pair1_urban_construction_t2_2021.png
│   │   │   ├── pair2_residential_expansion_t2.png
│   │   │   ├── pair3_building_change_cdvqa_t2.png
│   │   │   └── pair4_geotiff_satellite_t2.tif
│   │   └── PROMPTS.md
│   │
│   └── cross_modal/                          ← Mode 3: Optical + SAR Cross-Modal
│       ├── optical/
│       │   ├── pair1_cartosat2s_optical.tif
│       │   ├── pair2_airfield_optical.png
│       │   └── pair3_water_coast_optical.png
│       ├── sar/
│       │   ├── pair1_risat1a_eos04_sar.tif
│       │   ├── pair2_airfield_sar.png
│       │   └── pair3_water_coast_sar.png
│       └── PROMPTS.md
```

---

## 🚀 Quick Reference: Photo to Prompt Mapping

### 🟦 MODE 1: Single Image (VQA / LULC / Captioning)
**Step 1:** Select **"Single Image"** on the website (`/analyze`).  
**Step 2:** Drag & drop the chosen `.tif` file from `live_testing/images/single_image/`.  
**Step 3:** Copy & paste one of the matching prompts below:

| File | Scene Type | Copy-Paste Prompt | Expected AI Output |
|:---|:---|:---|:---|
| `01_urban_fabric_sentinel2.tif` | Urban Settlement | `What land cover classes are present in this satellite scene?` | Detects `Urban fabric`, `Inland waters`, `Pastures` with confidence scores. |
| `02_inland_water_sentinel2.tif` | Lake / River | `Is there a water body in this image, and where is it located?` | Identifies `Inland waters` and surrounding riparian vegetation. |
| `03_forest_canopy_sentinel2.tif` | Dense Forest | `What type of forest cover is visible in this satellite image?` | Classifies `Broad-leaved forest` and `Mixed forest`. |
| `04_industrial_commercial_sentinel2.tif` | Industrial Zone | `Identify any industrial or commercial units visible in this scene.` | Highlights `Industrial or commercial units` with warehouse footprints. |
| `05_cartosat2s_highres_pan_optical.tif` | High-Res Cartosat | `Analyze this high-resolution panchromatic Cartosat-2S scene. What structures are visible?` | Resolves sub-meter linear corridors, roads, and building clusters. |
| `06_rural_agriculture_sentinel2.tif` | Agriculture | `What is the dominant pattern of the agricultural parcels in this scene?` | Identifies arable field parcels and pasture boundaries. |
| `07_regional_large_landscape.tif` | Macro Landscape | `Provide a macro-level environmental and geographic overview of this regional landscape.` | Comprehensive landscape scene narrative and terrain transition. |

---

### 🟩 MODE 2: Bi-Temporal (Change Detection)
**Step 1:** Select **"Bi-Temporal"** on the website (`/analyze`).  
**Step 2:** Upload Date 1 file into **T1 (Pre-Event)** and Date 2 file into **T2 (Post-Event)**.  
**Step 3:** Copy & paste the prompt:

| Pair Name | Date 1 (Before) | Date 2 (After) | Copy-Paste Prompt | Expected AI Output |
|:---|:---|:---|:---|:---|
| **Pair 1: Construction** | `pair1_urban_construction_t1_2018.png` | `pair1_urban_construction_t2_2021.png` | `Detect all newly constructed buildings and structures between Date 1 and Date 2.` | Highlights emerging residential buildings and foundation expansion. |
| **Pair 2: Residential** | `pair2_residential_expansion_t1.png` | `pair2_residential_expansion_t2.png` | `Analyze the spatial distribution of changes between the two dates.` | Reports transformation of open ground into residential subdivision. |
| **Pair 3: CDVQA** | `pair3_building_change_cdvqa_t1.png` | `pair3_building_change_cdvqa_t2.png` | `Have any buildings disappeared or been demolished between image 1 and image 2?` | Answers structural alterations and localized change regions. |
| **Pair 4: Satellite GeoTIFF** | `pair4_geotiff_satellite_t1.tif` | `pair4_geotiff_satellite_t2.tif` | `Perform bi-temporal change detection using calibrated satellite bands. What changes occurred?` | Generates calibrated change mask and area metric in hectares. |

---

### 🟨 MODE 3: Cross-Modal (Optical + SAR Analysis)
**Step 1:** Select **"Cross-Modal"** on the website (`/analyze`).  
**Step 2:** Upload the optical image into the **Optical slot** and SAR image into the **SAR slot**.  
**Step 3:** Copy & paste the prompt:

| Pair Name | Optical Input | SAR Input | Copy-Paste Prompt | Expected AI Output |
|:---|:---|:---|:---|:---|
| **Pair 1: ISRO Sensors** | `pair1_cartosat2s_optical.tif` | `pair1_risat1a_eos04_sar.tif` | `Compare the optical Cartosat-2S and SAR RISAT-1A observations for this scene.` | Separates optical surface albedo from C-band dielectric roughness; reports high agreement. |
| **Pair 2: Airfield Runway** | `pair2_airfield_optical.png` | `pair2_airfield_sar.png` | `Explain why the runway surface appears dark in the SAR image compared to the optical view.` | Explains radar specular reflection away from sensor on smooth asphalt vs optical contrast. |
| **Pair 3: Coastal Water** | `pair3_water_coast_optical.png` | `pair3_water_coast_sar.png` | `Delineate the water-land boundary using complementary optical spectral reflectance and SAR backscatter.` | Verifies shoreline position using low radar backscatter for water and high volume scatter for land. |

---

## 🛠️ Step-by-Step Live Testing Walkthrough

1. **Open the Live Analysis App**:
   Navigate to **https://sih-orbilens-2026-tm.web.app/analyze**

2. **Select Upload Mode**:
   Click **Single Image**, **Bi-Temporal**, or **Cross-Modal**.

3. **Upload the Files**:
   From your local file picker, select the files from:
   `<repo-root>\live_testing\images\{mode}\`

4. **Verify Pre-Flight Validation**:
   Confirm the raster displays a green validation badge indicating valid dimensions, channels, and format.

5. **Submit Query**:
   Copy one of the prompts above into the prompt box and click **Investigate** (or press Enter).

6. **Observe Real-Time Stream**:
   Watch the live agentic execution stream:
   - Intent routing & specialist dispatch
   - Multimodal evidence extraction
   - Confidence scoring and verifiable citations

7. **Download Investigation Report**:
   Export the generated report as **Markdown**, **HTML**, or **JSON** and save it into `live_testing/reports/`.
