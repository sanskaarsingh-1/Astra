# 🛰️ Cross-Modal Mode — Optical + SAR Photo Pairs & Prompts
**Upload Mode**: Mode 3 — Cross-Modal (Optical + SAR Physics-Based Analysis)  
**Website Workspace**: https://sih-orbilens-2026-tm.web.app/analyze

---

## Pair 1: ISRO Cartosat-2S (Optical) + RISAT-1A / EOS-04 (SAR)
- **Optical Image**: `optical/pair1_cartosat2s_optical.tif` (Cartosat-2S High-Resolution Panchromatic)
- **SAR Image**: `sar/pair1_risat1a_eos04_sar.tif` (RISAT-1A C-band Synthetic Aperture Radar, RH/RV polarizations)
- **Physics**: Optical captures surface reflectance and albedo; C-band SAR penetrates clouds/haze and responds to surface roughness, dielectric constant, and corner-reflector geometry.
- **Recommended Prompts (Copy & Paste)**:

```text
Compare the optical Cartosat-2S and SAR RISAT-1A observations for this scene.
```
```text
Are there any structural features detected by the SAR sensor that are obscured or ambiguous in the optical image?
```
```text
Analyze the dielectric and roughness properties of the terrain using the C-band SAR backscatter.
```
```text
Resolve any conflicting signatures between the optical reflectance and radar backscatter.
```

---

## Pair 2: Airfield Runway & Transportation Corridor
- **Optical Image**: `optical/pair2_airfield_optical.png`
- **SAR Image**: `sar/pair2_airfield_sar.png`
- **Physics**: Smooth tarmac/concrete acts as a specular reflector in SAR (scattering radar pulses away $\to$ dark signature), while exhibiting high visual contrast in optical imagery. Surrounding hangars produce strong double-bounce reflections.
- **Recommended Prompts (Copy & Paste)**:

```text
Identify the airfield runway corridor across both optical and SAR modalities.
```
```text
Explain why the runway surface appears dark in the SAR image compared to the optical view.
```
```text
Are there metallic aircraft or hangar structures exhibiting strong double-bounce backscatter in the SAR channel?
```
```text
How does the cross-modal fusion improve boundary delineation of the transportation facilities?
```

---

## Pair 3: Water Body & Coastal Boundary
- **Optical Image**: `optical/pair3_water_coast_optical.png`
- **SAR Image**: `sar/pair3_water_coast_sar.png`
- **Physics**: Calm water produces minimal radar backscatter (specular return away from satellite), appearing dark in SAR regardless of solar illumination, turbidity, or algal blooms. Vegetation and land exhibit high volume backscatter.
- **Recommended Prompts (Copy & Paste)**:

```text
Delineate the water-land boundary using complementary optical spectral reflectance and SAR backscatter.
```
```text
Does the SAR observation confirm the presence of standing water where optical illumination varies?
```
```text
Analyze surface roughness differences between the water surface and coastal terrain.
```
```text
Generate a cross-modal verification report validating the shoreline position.
```
