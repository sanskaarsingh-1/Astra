# ⏳ Bi-Temporal Mode — Test Photo Pairs & Prompts
**Upload Mode**: Mode 2 — Bi-Temporal Change Detection  
**Website Workspace**: https://sih-orbilens-2026-tm.web.app/analyze

---

## Pair 1: Urban Construction & Building Emergence
- **Date 1 (Before)**: `before/pair1_urban_construction_t1_2018.png`
- **Date 2 (After)**: `after/pair1_urban_construction_t2_2021.png`
- **Source**: LEVIR-CD Dataset (0.5m High-Resolution Optical)
- **Ground Truth**: New building construction and foundation expansion over previously open ground.
- **Recommended Prompts (Copy & Paste)**:

```text
What has changed between these two satellite images?
```
```text
Detect all newly constructed buildings and structures between Date 1 and Date 2.
```
```text
Show me the change mask and estimate the total built-up area increase in square metres.
```
```text
Has there been significant urban expansion or vegetation loss between these two periods?
```

---

## Pair 2: Residential Expansion & Subdivision Development
- **Date 1 (Before)**: `before/pair2_residential_expansion_t1.png`
- **Date 2 (After)**: `after/pair2_residential_expansion_t2.png`
- **Source**: LEVIR-CD Dataset
- **Ground Truth**: Conversion of agricultural/pasture parcels into residential housing blocks and access roads.
- **Recommended Prompts (Copy & Paste)**:

```text
Analyze the spatial distribution of changes between the two dates. Are they concentrated or scattered?
```
```text
Identify the primary land use transition from Date 1 to Date 2.
```
```text
How many distinct new building clusters or residential units were constructed?
```
```text
Generate a comprehensive change detection report detailing the altered parcels.
```

---

## Pair 3: Change Detection VQA (Building Footprints)
- **Date 1 (Before)**: `before/pair3_building_change_cdvqa_t1.png`
- **Date 2 (After)**: `after/pair3_building_change_cdvqa_t2.png`
- **Source**: CDVQA Dataset
- **Ground Truth**: Targeted structural alterations, building additions, and roofline changes.
- **Recommended Prompts (Copy & Paste)**:

```text
Have any buildings disappeared or been demolished between image 1 and image 2?
```
```text
Are the changes primarily building additions, road developments, or vegetation changes?
```
```text
Which quadrant of the scene contains the most significant change?
```
```text
What percentage of the total area has experienced change between the two observations?
```

---

## Pair 4: Georeferenced Satellite GeoTIFF Bi-Temporal Pair
- **Date 1 (Before)**: `before/pair4_geotiff_satellite_t1.tif`
- **Date 2 (After)**: `after/pair4_geotiff_satellite_t2.tif`
- **Source**: Calibrated Satellite GeoTIFFs (EPSG:32632 UTM)
- **Ground Truth**: Radiometric and structural change across multi-spectral satellite overpasses.
- **Recommended Prompts (Copy & Paste)**:

```text
Perform bi-temporal change detection using calibrated satellite bands. What changes occurred?
```
```text
Calculate the change metric and highlight all regions exceeding the significance threshold.
```
```text
Did vegetation increase or decrease between the two satellite acquisition dates?
```
```text
Provide a technical remote sensing change summary with hectares altered.
```
