# 📋 Mode 3 — Cross-Modal (Optical + SAR) Testing Checklist
**Upload Mode**: Cross-Modal (Optical GeoTIFF + SAR GeoTIFF)  
**Specialists Triggered**: Cross-Modal Reasoning Specialist, SAR Stats, Optical-SAR Conflict Detector  
**Images to use**: `images/cross_modal/optical/` + `images/cross_modal/sar/`  

---

## ✅ Pre-Test Setup

- [ ] Website is open at https://sih-orbilens-2026-tm.web.app/analyze
- [ ] Upload mode is set to **Cross-Modal**
- [ ] Optical image (Sentinel-2 / Cartosat-2S) ready in `optical/`
- [ ] SAR image (RISAT-1A / EOS-04 C-band) of SAME AREA ready in `sar/`
- [ ] Pre-flight validation shows both files compatible

---

## 🖼️ What Kind of Image Pairs to Use

Place matching optical + SAR GeoTIFF pairs covering the SAME geographic area:

- `images/cross_modal/optical/` → Sentinel-2 (10m MSI), Cartosat-2S (0.65m Panchromatic)
- `images/cross_modal/sar/`     → RISAT-1A C-band, EOS-04 SAR

| Conflict Scenario | What Optical Shows | What SAR Shows | Expected Conflict |
|:---|:---|:---|:---|
| Water body | High reflectance (blue/white) | Very low backscatter (dark) | ✅ Agree — both show water |
| Urban / Buildings | Moderate reflectance | High double-bounce backscatter | ⚠️ Compare surface vs structure |
| Airport runway | Grey, flat, low reflectance | Very low SAR return (flat metal) | Potential conflict |
| Forest | Strong NIR reflectance | Medium-high volume scatter | ⚠️ Optical vs SAR canopy depth |
| Flooded farmland | Low NIR (water stress) | Specular low return | ✅ Agree — waterlogged |
| Ocean / Sea | High solar reflectance | Low-to-medium roughness return | Compare wind roughness vs calm |

> 💡 **Tip**: BigEarthNet v2.0 has paired Sentinel-1 (SAR) + Sentinel-2 (optical) tiles.  
> Same patch ID = same geographic area. Use these pairs for perfectly aligned testing.  
> File naming: `S2B_optical_patch_001.tif` + `S1B_sar_patch_001.tif`

---

## ❓ Questions to Ask — Optical + SAR Cross-Modal Reasoning

### Core Cross-Modal Analysis Questions

```
Analyse this optical and SAR image pair and describe the land surface.
Do the optical and SAR observations agree about this area?
What does the SAR backscatter tell us that the optical image cannot?
Describe the surface roughness and reflectance characteristics of this region.
```

### Conflict Detection Questions (Physics-Based)

```
Are there any physical contradictions between the optical and radar signatures?
Does the optical reflectance conflict with the SAR microwave backscatter?
Is the SAR backscatter consistent with what we see in the optical image?
What surface type would explain both the optical reflectance and the radar backscatter?
Is there evidence of double-bounce radar scattering consistent with urban structures?
```

### Surface Physics Questions

```
What is the estimated SAR backscatter in decibels (dB) for this region?
Is this area likely to be water, urban, or vegetation based on both optical and radar?
What is the NDVI of the optical image and how does it compare to the SAR return?
Describe the radar roughness signature of this scene.
Is the microwave return consistent with bare soil or vegetated surface?
```

### ISRO Sensor-Specific Questions

```
Is this a Cartosat-2S panchromatic image or a Sentinel-2 multispectral image?
What C-band radar features are visible in this RISAT-1A / EOS-04 image?
Describe the backscatter characteristics of this SAR image.
Is the optical image captured in solar reflectance band or thermal?
```

---

## ✅ What to Verify After Each Test

| Check | Pass Criteria |
|:---|:---|
| Pre-flight validation — Optical | Green ✅ CRS, GSD, width/height |
| Pre-flight validation — SAR | Green ✅ compatible CRS + overlap % |
| SAR stats in evidence | Backscatter dB value shown with `DETERMINISTIC` label |
| Optical stats | NIR, Red reflectance values shown |
| Conflict detection | Agreement or conflict record shown in evidence panel |
| Physical separation | Optical and SAR evidence kept in separate evidence blocks |
| NDVI (if optical has NIR) | NDVI value computed deterministically |
| Cross-modal reasoning answer | References BOTH optical AND radar physical properties |
| Observable trace | Cross-modal specialist step shown with duration |
| Report export | Conflict record included in `.json` report |

---

## 🔬 Specific Physics Conflict Checks

These combinations should trigger a conflict warning:

| Scenario | Optical Shows | SAR Shows | Expected |
|:---|:---|:---|:---|
| High optical reflectance (water glint) + high SAR return | Bright water | High backscatter | ⚠️ Conflict — water = low SAR |
| Very low optical reflectance + very high SAR double bounce | Dark surface | Bright urban return | ⚠️ Shadow vs structure conflict |

---

## 📝 Test Log

| # | Optical Image | SAR Image | Question Asked | Conflict Detected? | Result | Notes |
|:--|:---|:---|:---|:---|:---|:---|
| 1 | | | "Do optical/SAR agree?" | Yes / No | ⬜ Pass / ⬜ Fail | |
| 2 | | | "SAR backscatter dB?" | Numeric value | ⬜ Pass / ⬜ Fail | |
| 3 | | | "Physical contradictions?" | Conflict record | ⬜ Pass / ⬜ Fail | |
| 4 | | | "Describe surface type" | Combined reasoning | ⬜ Pass / ⬜ Fail | |
| 5 | | | | | ⬜ Pass / ⬜ Fail | |
