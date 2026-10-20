# 🕐 Bi-Temporal — Before Images (Date 1)

Place the **OLDER / EARLIER date** GeoTIFF images here.  
These are uploaded as **"Date 1"** in Mode 2 (Bi-Temporal Change Detection).

---

## Pairing Rule

Every image in this `before/` folder must have a **matching pair** in `../after/`  
with the **same filename prefix** so you know which files go together.

```
before/
  levir_train_001_2018.tif      ← Date 1 (older)
  urban_expand_2020.tif         ← Date 1 (older)

after/
  levir_train_001_2021.tif      ← Date 2 (newer) — matches above
  urban_expand_2023.tif         ← Date 2 (newer) — matches above
```

---

## Recommended Image Pairs (Scene Types)

| Scenario | Before Image Description | Expected Change |
|:---|:---|:---|
| Urban expansion | Rural outskirts with sparse structures (2018–2020) | New housing colonies appear |
| Construction | Bare land, open ground | Building / stadium constructed |
| Deforestation | Dense forest cover | Trees cleared, bare soil visible |
| Flood event | Dry river floodplain / farmland | Flooded water bodies expand |
| Crop cycle change | Harvested fields (brown/dry) | New crop growth (green) |
| Wildfire aftermath | Green forest pre-fire | Charred, burnt landscape |
| Reservoir fill | Empty or low reservoir | Full reservoir after monsoon |

---

## Where to Get Before Images

1. **LEVIR-CD dataset** (already on disk — bi-temporal pairs):
   - Path: `datasets/05_LEVIR_CD/`
   - These are 512×512 px RGB GeoTIFF pairs — perfect for bi-temporal testing
   - The `train/A/` folder = "before" images
   - The `train/B/` folder = "after" images

2. **Google Earth Engine** (export any date range as GeoTIFF):
   - https://earthengine.google.com

3. **Copernicus Sentinel Hub**:
   - https://www.sentinel-hub.com

---

## Technical Requirements

| Property | Requirement |
|:---|:---|
| Format | GeoTIFF (`.tif`) |
| CRS | Must match the `after/` image CRS |
| Spatial extent | Must overlap with the `after/` image |
| Resolution | Should match (or be compatible with) the `after/` image |
| Recommended size | 256×256 to 512×512 pixels |

> ⚠️ The pre-flight validator will check **CRS compatibility** and **spatial overlap %** between the before and after images. Mismatched CRS = validation failure.
