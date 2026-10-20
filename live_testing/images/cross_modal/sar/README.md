# 📡 Cross-Modal — SAR Images

Place **SAR (Synthetic Aperture Radar) GeoTIFF** images here.  
These are uploaded as the **"SAR"** input in Mode 3 (Cross-Modal Optical + SAR).

---

## Pairing Rule

Every SAR image here must have a **matching optical pair** in `../optical/`  
covering the **exact same geographic area**.

```
optical/
  s2_patch_001_optical.tif       ← Sentinel-2 optical

sar/
  s1_patch_001_sar.tif           ← Sentinel-1 SAR ← PUT HERE
```

---

## Supported SAR Sensors

| Sensor | Band | Resolution | Notes |
|:---|:---|:---|:---|
| **Sentinel-1 IW** | C-band (5.6 GHz) | 10 m | Best paired with BigEarthNet Sentinel-2 |
| **RISAT-1A** | C-band | 3–50 m | ISRO sensor — key for SIH demo |
| **EOS-04 (RISAT-2BR2)** | C-band | 1–14 m | ISRO's latest SAR satellite |
| **ALOS-2 PALSAR** | L-band (1.2 GHz) | 3–100 m | Penetrates vegetation canopy |

---

## What SAR Signatures to Expect

Understanding SAR backscatter helps you write better test questions:

| Surface Type | Expected Backscatter | SAR Appearance |
|:---|:---|:---|
| Calm water / reservoir | Very low (−20 to −15 dB) | Dark / black in image |
| Urban buildings | Very high (double bounce, −5 to +5 dB) | Bright white clusters |
| Forest / dense veg | Medium-high (−12 to −6 dB) | Textured grey-green |
| Bare soil / desert | Medium-low (−15 to −10 dB) | Uniform grey |
| Rough sea / ocean | Medium (−10 to −5 dB) | Speckled texture |
| Airport runway (flat metal) | Very low (specular) | Dark strip |

---

## Where to Get SAR Images

1. **BigEarthNet v2.0** (already on disk — includes Sentinel-1):
   - Path: `datasets/01_BigEarthNet_v2/`
   - Subfolder: `BigEarthNet-S1-v1.0/` patches
   - Pre-paired with Sentinel-2 by patch ID — use directly

2. **Copernicus Open Access Hub** (free Sentinel-1): https://scihub.copernicus.eu  
3. **ISRO NRSC Bhuvan** (RISAT data): https://bhuvan.nrsc.gov.in  
4. **Alaska Satellite Facility** (Sentinel-1 / ALOS-2): https://asf.alaska.edu  

---

## Technical Requirements

| Property | Requirement |
|:---|:---|
| Format | GeoTIFF (`.tif`) |
| CRS | Must overlap spatially with the optical image |
| Data type | Float32 or Int16 (calibrated backscatter) |
| Polarisation | VV, VH, or HH (single or dual pol) |
| Recommended size | 256×256 to 512×512 pixels |

> ⚠️ SAR images look very different from optical — they appear grainy/speckled.  
> The system will read them as microwave backscatter (dB), not visual colour.  
> Do **not** upload regular photos as SAR — the physics-based analysis will be wrong.
