# 🕑 Bi-Temporal — After Images (Date 2)

Place the **NEWER / LATER date** GeoTIFF images here.  
These are uploaded as **"Date 2"** in Mode 2 (Bi-Temporal Change Detection).

---

## Pairing Rule

Every image here must have a **matching pair** in `../before/` with the same area.

```
before/
  levir_train_001_2018.tif      ← Date 1 (older)

after/
  levir_train_001_2021.tif      ← Date 2 (newer) ← PUT HERE
```

---

## Where to Get After Images

1. **LEVIR-CD dataset** — `datasets/05_LEVIR_CD/train/B/` = after images  
2. **Google Earth Engine** — export same area at a later date  
3. **Copernicus Sentinel Hub** — pick any date after the "before" image  

---

## Technical Requirements

| Property | Requirement |
|:---|:---|
| Format | GeoTIFF (`.tif`) |
| CRS | Must match the `before/` image CRS exactly |
| Spatial extent | Must overlap with the `before/` image |
| Resolution | Should match (or be close to) the `before/` image |
| Recommended size | 256×256 to 512×512 pixels |

> ⚠️ Pre-flight validator checks **CRS compatibility** + **spatial overlap %**.  
> A mismatch will show a red ❌ badge on the website — fix before running investigation.
