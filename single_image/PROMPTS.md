# 🎯 Single Image Mode — Test Photos & Matching Prompts
**Upload Mode**: Mode 1 — Single Image (VQA / LULC / Captioning)  
**Website Workspace**: https://sih-orbilens-2026-tm.web.app/analyze

---

## Image 1: `01_urban_fabric_sentinel2.tif`
- **Source**: Sentinel-2 MSI (Austria Patch `T33UUP_27_61`)
- **Key Features**: Dense urban settlement, road infrastructure, adjacent green space, inland water channel.
- **Recommended Prompts (Copy & Paste)**:

```text
What land cover classes are present in this satellite scene?
```
```text
Is this area rural or urban? Describe the density of the built-up structures.
```
```text
Classify the land use of this region and estimate the percentage of urban fabric versus natural vegetation.
```
```text
Describe this satellite scene in detail, focusing on human infrastructure and surrounding terrain.
```

---

## Image 2: `02_inland_water_sentinel2.tif`
- **Source**: Sentinel-2 MSI (Austria Patch `T33UUP_27_55`)
- **Key Features**: Distinct inland lake/river, riparian vegetation, arable agricultural fields.
- **Recommended Prompts (Copy & Paste)**:

```text
Is there a water body in this image, and where is it located?
```
```text
What is the dominant land use type surrounding the water body?
```
```text
Estimate the proportion of water versus agricultural land in this patch.
```
```text
Are there any signs of industrial runoff or artificial structures near the shoreline?
```

---

## Image 3: `03_forest_canopy_sentinel2.tif`
- **Source**: Sentinel-2 MSI (Austria Patch `T33UUP_26_57`)
- **Key Features**: Dense broad-leaved and mixed forest canopy, natural woodland, pasture clearings.
- **Recommended Prompts (Copy & Paste)**:

```text
What type of forest cover is visible in this satellite image?
```
```text
Is the vegetation healthy and continuous, or are there clear-cuts and fragmented patches?
```
```text
Classify this scene according to BigEarthNet 19-class taxonomy.
```
```text
Provide a technical scene description highlighting canopy density and elevation features.
```

---

## Image 4: `04_industrial_commercial_sentinel2.tif`
- **Source**: Sentinel-2 MSI (Austria Patch `T33UUP_30_53`)
- **Key Features**: Large commercial warehouses, industrial roofs, transportation links, perimeter farmland.
- **Recommended Prompts (Copy & Paste)**:

```text
Identify any industrial or commercial units visible in this scene.
```
```text
What infrastructure and transportation features connect this site to surrounding areas?
```
```text
Is there any residential settlement adjacent to these industrial facilities?
```
```text
List all detected land cover classes with their confidence scores.
```

---

## Image 5: `05_cartosat2s_highres_pan_optical.tif`
- **Source**: ISRO Cartosat-2S Panchromatic (0.65m GSD High Resolution)
- **Key Features**: High-resolution building footprints, runway/road alignment, sharp edge gradients.
- **Recommended Prompts (Copy & Paste)**:

```text
Analyze this high-resolution panchromatic Cartosat-2S scene. What structures are visible?
```
```text
Locate the main linear features, roads, and runway corridors.
```
```text
Count approximately how many distinct building compounds or structures can be resolved.
```
```text
What sensor characteristics and spatial resolution are evident in this image?
```

---

## Image 6: `06_rural_agriculture_sentinel2.tif`
- **Source**: Sentinel-2 MSI (Austria Patch `T33UUP_28_55`)
- **Key Features**: Geometric field parcels, crop boundaries, hedgerows, rural pasture.
- **Recommended Prompts (Copy & Paste)**:

```text
Are these agricultural fields actively cultivated or fallow?
```
```text
What is the dominant pattern of the agricultural parcels in this scene?
```
```text
Are there irrigation channels or farm access roads visible between the fields?
```

---

## Image 7: `07_regional_large_landscape.tif`
- **Source**: Multi-kilometer Regional Composite
- **Key Features**: Diverse landscape with mountain terrain, river basin, urban periphery, and agricultural valleys.
- **Recommended Prompts (Copy & Paste)**:

```text
Provide a macro-level environmental and geographic overview of this regional landscape.
```
```text
Identify the primary ecological zones and terrain transitions across the image.
```
```text
What are the primary natural hazards or environmental vulnerabilities visible in this terrain?
```
