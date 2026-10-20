# 📋 Mode 2 — Bi-Temporal Change Detection Checklist
**Upload Mode**: Bi-Temporal (2 GeoTIFFs — Date 1 + Date 2)  
**Specialists Triggered**: BIT Siamese Change Detection, CDVQA (Change-VQA), Area Calculator  
**Images to use**: `images/bi_temporal/before/` + `images/bi_temporal/after/`  

---

## ✅ Pre-Test Setup

- [ ] Website is open at https://sih-orbilens-2026-tm.web.app/analyze
- [ ] Upload mode is set to **Bi-Temporal**
- [ ] Two images of the SAME location at DIFFERENT dates are ready
- [ ] Both images have compatible CRS and spatial overlap
- [ ] Pre-flight validation badge shows green ✅ for both files

---

## 🖼️ What Kind of Image Pairs to Use

Place matching before/after GeoTIFF pairs in:
- `images/bi_temporal/before/` → older date (e.g. 2020)
- `images/bi_temporal/after/`  → newer date (e.g. 2023)

| Scenario | Before Image | After Image | Change Expected |
|:---|:---|:---|:---|
| Urban expansion | Rural outskirts | New housing / roads added | New built-up pixels |
| Deforestation | Dense forest cover | Forest cleared, bare soil | Vegetation → barren |
| Flood event | Dry river floodplain | Flooded fields / roads | Water body expansion |
| Construction | Bare land / fields | New building / stadium built | Built-up area appears |
| Wildfire aftermath | Green forest | Burnt, charred landscape | Vegetation loss |
| Crop cycle | Harvested fields (brown) | Growing crops (green) | Vegetation increase |
| Reservoir fill | Empty reservoir bed | Full reservoir | Water body appears |

> 💡 **Tip**: LEVIR-CD dataset pairs (512×512 px, 0.5m GSD) are ideal for testing.  
> File naming: `before_2020_levir_train_001.png`, `after_2023_levir_train_001.png`

---

## ❓ Questions to Ask — Change Detection (BIT Specialist)

### Core Change Detection Questions

```
What has changed between these two satellite images?
Detect all changes between image 1 and image 2.
Show me the change mask between these two time periods.
How much area has changed between the two dates?
What is the total changed area in hectares?
```

### Change Characterisation Questions

```
Has there been urban expansion between these two images?
Has deforestation occurred in this region between the two dates?
Have there been any flood events visible in the change map?
What type of land cover change has occurred?
Has construction activity taken place in this area?
Are the changes concentrated in one region or spread across the whole image?
```

### Quantitative / Area Questions

```
What is the total area of change detected in square metres?
What percentage of the image has changed between the two dates?
How many separate change regions were detected?
What is the size of the largest changed region in hectares?
```

---

## ❓ Questions to Ask — CDVQA (Change-VQA)

These questions require the model to reason over the *change mask* AND the land cover shift:

```
Has the water area increased or decreased between the two dates?
Is the change in vegetation larger than the change in built-up area?
What land cover class has seen the most growth?
Was the change predominantly in urban or agricultural zones?
Has the forest cover been reduced?
Which part of the image changed the most — north, south, east, or west?
Is the detected change consistent with urban development or natural events?
Did the green vegetation increase or decrease between the two images?
```

---

## ✅ What to Verify After Each Test

| Check | Pass Criteria |
|:---|:---|
| Pre-flight validation — File 1 | Green ✅ CRS + dimensions shown |
| Pre-flight validation — File 2 | Green ✅ compatible CRS + overlap % shown |
| Change mask overlay | Visual binary mask rendered over the image |
| Changed area (m²) | Numeric value with `DETERMINISTIC` status label |
| Changed area (ha) | Converted hectares shown alongside m² |
| Changed pixel count | Integer count displayed in evidence |
| Connected components | Number of distinct change regions shown |
| CDVQA answer | Grounded natural language answer references the mask |
| Observable trace | BIT model step shows duration_ms |
| Report includes | Change area, mask, model metrics (OA: 96.98%, F1: 69.56%) |

---

## 📝 Test Log

| # | Before Image | After Image | Question Asked | Expected Output | Result | Notes |
|:--|:---|:---|:---|:---|:---|:---|
| 1 | | | "What has changed?" | Change mask + area | ⬜ Pass / ⬜ Fail | |
| 2 | | | "Area in hectares?" | m² + ha values | ⬜ Pass / ⬜ Fail | |
| 3 | | | CDVQA question | Grounded answer | ⬜ Pass / ⬜ Fail | |
| 4 | | | "Urban expansion?" | Yes/No + mask | ⬜ Pass / ⬜ Fail | |
| 5 | | | | | ⬜ Pass / ⬜ Fail | |
