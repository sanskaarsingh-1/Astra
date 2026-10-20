# 🌅 Cross-Modal — Optical Images

Place **Optical satellite GeoTIFF** images here.  
These are uploaded as the **"Optical"** input in Mode 3 (Cross-Modal Optical + SAR).

---

## Pairing Rule

Every optical image here must have a **matching SAR pair** in `../sar/`  
covering the **exact same geographic area**.

```
optical/
  s2_patch_001_optical.tif       ← Sentinel-2 optical ← PUT HERE

sar/
  s1_patch_001_sar.tif           ← Sentinel-1 SAR — matches above
```

---

## Supported Optical Sensors

| Sensor | Resolution | Bands | Notes |
|:---|:---|:---|:---|
| **Sentinel-2 MSI** | 10–60 m | 12 bands (B01–B12) | Best for NDVI, LULC, cross-modal |
| **Cartosat-2S PAN** | 0.65 m | Panchromatic | ISRO sensor — high-res B&W |
| **Landsat 8/9 OLI** | 30 m | 11 bands | Good for large-area analysis |

---

## Where to Get Optical Images

1. **BigEarthNet v2.0** (already on disk — includes Sentinel-2):
   - Path: `datasets/01_BigEarthNet_v2/`
   - Subfolder pattern: `BigEarthNet-S2-v1.0/` patches
   - These are already paired with Sentinel-1 SAR — perfect for cross-modal

2. **Copernicus Open Access Hub**: https://scihub.copernicus.eu  
3. **USGS Earth Explorer**: https://earthexplorer.usgs.gov  
4. **ISRO Bhuvan Portal** (Cartosat data): https://bhuvan.nrsc.gov.in  

---

## Technical Requirements

| Property | Requirement |
|:---|:---|
| Format | GeoTIFF (`.tif`) |
| CRS | Must overlap spatially with the SAR image |
| Bands | RGB minimum; full multispectral preferred |
| Recommended size | 256×256 to 512×512 pixels |

> 💡 **Tip**: BigEarthNet patches are pre-paired — `S2B_MSIL2A_*` (optical) maps 1:1 to `S1B_IW_*` (SAR) by patch ID.  
> This is the easiest way to get guaranteed-compatible optical+SAR pairs.
