# 📋 Mode 1 — Single Image Testing Checklist
**Upload Mode**: Single Image (1 GeoTIFF)  
**Specialists Triggered**: VQA, LULC (Land Cover), Scene Captioning, Visual Grounding  
**Images to use**: `images/single_image/` folder  

---

## ✅ Pre-Test Setup

- [ ] Website is open at https://sih-orbilens-2026-tm.web.app/analyze
- [ ] Upload mode is set to **Single Image**
- [ ] Backend is running (local) OR using live Firebase deployment
- [ ] GeoTIFF image file is ready (see image folder)

---

## 🖼️ What Kind of Images to Use

Place the following types of GeoTIFF or high-res satellite images in `images/single_image/`:

| Image Type | What to Look For | LULC Classes Expected |
|:---|:---|:---|
| Urban area (city / town) | Buildings, roads, dense blocks | Urban fabric, Industrial units |
| Agricultural land | Fields, crop rows, irrigation canals | Arable land, Pastures |
| Forest / Woodland | Dense tree cover, forest patches | Broad-leaved forest, Mixed forest |
| Water body | Lake, reservoir, coastal strip | Water bodies, Sea & ocean |
| Barren / Desert | Sand, rock, sparse vegetation | Beaches, dunes, sparsely vegetated |
| Airport / Runway | Long runways, taxiways, terminals | Industrial / commercial units |
| Port / Harbour | Ships, docks, storage tanks | Port areas |

> 💡 **Tip**: Images from BigEarthNet v2.0 dataset (510×510 px Sentinel-2 tiles) work best.  
> File naming suggestion: `urban_ahmedabad_s2.tif`, `forest_patch_ooty.tif`, etc.

---

## ❓ Questions to Ask — VQA (Visual Question Answering)

### Presence / Existence Questions
Ask these to test if the model can detect objects in the image:

```
Is there a water body in this image?
Are there any roads visible in this satellite image?
Is there a forested area in this image?
Can you see any agricultural fields?
Is there urban development in this region?
Are there any buildings or structures visible?
Is this area near the coast?
Is there any industrial infrastructure present?
```

### Count Questions
Ask these to test counting capability:

```
How many large buildings can you see?
How many distinct land cover types are present?
How many roads or pathways are visible in this image?
Approximately how many separate forest patches are there?
```

### Rural vs. Urban Classification Questions
Ask these to test rural/urban reasoning:

```
Is this area rural or urban?
Does this look like a city centre or a rural outskirt?
Is the land use primarily agricultural or industrial?
```

### Comparison Questions
Ask these to test relative spatial reasoning:

```
Is the vegetation area larger or smaller than the built-up area?
Which part of the image has higher density — the northern or southern region?
Is the water body on the left or right side of the image?
```

---

## 🗺️ Questions to Ask — LULC (Land Cover Classification)

```
What land cover classes are present in this image?
What is the dominant land use type in this satellite image?
Classify the land cover of this region according to CORINE classes.
What percentage of this image is covered by vegetation?
Is there any industrial or commercial land use visible?
```

---

## 📝 Questions to Ask — Scene Captioning

```
Describe this satellite image in detail.
What is happening in this region based on the satellite view?
Give me a detailed description of the land use and geographic features visible.
Write a technical scene description for this remote sensing image.
Summarize the key objects and spatial patterns visible in this image.
```

---

## 📍 Questions to Ask — Visual Grounding (Object Localization)

```
Locate the largest water body in this image.
Find the main road or highway in this satellite image.
Where is the densest urban cluster in this image?
Point to the agricultural field in this image.
Locate the forest patch in this image.
Find the airport or runway in this image.
```

---

## ✅ What to Verify After Each Test

| Check | Pass Criteria |
|:---|:---|
| Pre-flight GeoTIFF badge | Shows green ✅ with CRS, GSD, dimensions |
| Progress SSE stream | Shows steps: validating → routing → specialist → assembling |
| LULC Classification | Shows 19 CORINE classes with probability bars |
| Caption output | Multi-sentence, specific to the image content |
| VQA answer | Grounded answer with confidence |
| Observable Trace | Shows `step_id`, `tool_id`, `duration_ms` timeline |
| Evidence Panel | Shows physical findings with `DETERMINISTIC` tags |
| Report download | `.md`, `.html`, `.json` all download correctly |

---

## 📝 Test Log

| # | Image File | Question Asked | Expected Specialist | Result | Notes |
|:--|:---|:---|:---|:---|:---|
| 1 | | | VQA | ⬜ Pass / ⬜ Fail | |
| 2 | | | LULC | ⬜ Pass / ⬜ Fail | |
| 3 | | | Caption | ⬜ Pass / ⬜ Fail | |
| 4 | | | Grounding | ⬜ Pass / ⬜ Fail | |
| 5 | | | | ⬜ Pass / ⬜ Fail | |
| 6 | | | | ⬜ Pass / ⬜ Fail | |
