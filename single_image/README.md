# 🖼️ Single Image — Test Images Folder

Place **single GeoTIFF satellite images** here for **Mode 1** testing (VQA, LULC, Caption, Grounding).

---

## What to Put Here

| File | Scene Type | Why Useful |
|:---|:---|:---|
| `urban_city_s2.tif` | Dense urban area (city centre) | Tests LULC urban fabric detection |
| `agricultural_fields_s2.tif` | Crop fields / farmland | Tests arable land classification |
| `forest_cover_s2.tif` | Dense forest | Tests broad-leaved / mixed forest class |
| `water_body_s2.tif` | Lake, reservoir, coast | Tests water body detection |
| `airport_runway_s2.tif` | Airport with runways | Tests industrial + road classification |
| `desert_barren_s2.tif` | Sandy / rocky barren land | Tests sparse vegetation class |
| `port_harbour_s2.tif` | Harbour with ships | Tests port area class + captioning |
| `mixed_scene_s2.tif` | Mixed land uses | Tests multi-label LULC |

---

## Where to Get Images

1. **From your BigEarthNet v2.0 dataset** (already on disk):
   - Location: `datasets/01_BigEarthNet_v2/`
   - These are 510×510 px Sentinel-2 12-band GeoTIFFs
   - Copy any `.tif` patch here and rename it descriptively

2. **From BigEarthNet.txt** (VLM training set):
   - Location: `datasets/02_BigEarthNet_txt/`

3. **Copernicus Open Access Hub** (free downloads):
   - https://scihub.copernicus.eu

4. **USGS Earth Explorer** (Landsat, Sentinel):
   - https://earthexplorer.usgs.gov

---

## File Naming Convention

```
{scene_type}_{location}_{sensor}.tif

Examples:
  urban_ahmedabad_s2.tif
  forest_nilgiris_s2.tif
  water_chilika_lake_s2.tif
  agricultural_punjab_s2.tif
```

---

## Technical Requirements

| Property | Requirement |
|:---|:---|
| Format | GeoTIFF (`.tif`) |
| CRS | Any EPSG (EPSG:32632 / EPSG:4326 etc.) |
| Minimum size | 64×64 pixels |
| Recommended size | 256×256 to 512×512 pixels |
| Bands | At minimum RGB; Sentinel-2 12-band preferred |
| File size | Keep under 50 MB for smooth upload |

> ⚠️ **Plain `.jpg` or `.png` images will fail pre-flight validation** — the website expects GeoTIFF with geospatial metadata.
> Use images from your actual datasets for best results.
