# ❓ Quick Question Bank — All Modes
**Copy-paste these directly into the OrbilLens AI website query box**

---

## 🟦 MODE 1 — Single Image Questions

### VQA — Presence / Existence
```
Is there a water body in this image?
Are there any roads visible in this satellite image?
Is there a forested area in this image?
Can you see any agricultural fields?
Is there urban development in this region?
Are there any buildings or structures visible?
Is this area near the coast?
Is there any industrial infrastructure present?
Is there a river or stream flowing through this area?
Are there any airports or runways visible?
```

### VQA — Rural vs Urban
```
Is this area rural or urban?
Does this look like a city centre or a rural outskirt?
Is the land use primarily agricultural or industrial?
Is this a residential or commercial area?
```

### VQA — Count
```
How many large buildings can you see?
How many distinct land cover types are present?
How many roads or pathways are visible in this image?
Approximately how many separate forest patches are there?
```

### VQA — Comparison
```
Is the vegetation area larger or smaller than the built-up area?
Which part of the image has higher density — the north or the south?
Is the water body on the left or right side of the image?
Is the forest cover greater than 50% of this image?
```

### LULC — Land Cover Classification
```
What land cover classes are present in this image?
What is the dominant land use type in this satellite image?
Classify the land cover of this region according to CORINE classes.
What percentage of this image is covered by vegetation?
Is there any industrial or commercial land use visible?
List all land cover types detected in this image with their probabilities.
What CORINE land cover class has the highest probability in this image?
```

### Captioning — Scene Description
```
Describe this satellite image in detail.
What is happening in this region based on the satellite view?
Give me a detailed description of the land use and geographic features visible.
Write a technical scene description for this remote sensing image.
Summarize the key objects and spatial patterns visible in this image.
What are the most notable features in this satellite scene?
```

### Visual Grounding — Object Localization
```
Locate the largest water body in this image.
Find the main road or highway in this satellite image.
Where is the densest urban cluster in this image?
Point to the agricultural field in this image.
Locate the forest patch in this image.
Find the airport or runway in this image.
Where are the buildings located in this scene?
```

---

## 🟩 MODE 2 — Bi-Temporal Change Detection Questions

### Change Detection
```
What has changed between these two satellite images?
Detect all changes between image 1 and image 2.
Show me the change mask between these two time periods.
How much area has changed between the two dates?
What is the total changed area in hectares?
What is the total area of change detected in square metres?
What percentage of the image has changed between the two dates?
How many separate change regions were detected?
Are the changes concentrated in one region or spread across the whole image?
What is the size of the largest changed region in hectares?
```

### Change Type Classification
```
Has there been urban expansion between these two images?
Has deforestation occurred in this region between the two dates?
Have there been any flood events visible in the change map?
What type of land cover change has occurred?
Has construction activity taken place in this area?
```

### CDVQA — Change VQA
```
Has the water area increased or decreased between the two dates?
Is the change in vegetation larger than the change in built-up area?
What land cover class has seen the most growth?
Was the change predominantly in urban or agricultural zones?
Has the forest cover been reduced?
Which part of the image changed the most — north, south, east, or west?
Is the detected change consistent with urban development or natural events?
Did the green vegetation increase or decrease between the two images?
```

---

## 🟥 MODE 3 — Cross-Modal (Optical + SAR) Questions

### General Cross-Modal Analysis
```
Analyse this optical and SAR image pair and describe the land surface.
Do the optical and SAR observations agree about this area?
What does the SAR backscatter tell us that the optical image cannot?
Describe the surface roughness and reflectance characteristics of this region.
What surface type would explain both the optical reflectance and the radar backscatter?
```

### Conflict Detection
```
Are there any physical contradictions between the optical and radar signatures?
Does the optical reflectance conflict with the SAR microwave backscatter?
Is the SAR backscatter consistent with what we see in the optical image?
Is there evidence of double-bounce radar scattering consistent with urban structures?
Is the microwave return consistent with bare soil or vegetated surface?
```

### Physics / Quantitative
```
What is the estimated SAR backscatter in decibels (dB) for this region?
Is this area likely to be water, urban, or vegetation based on both optical and radar?
What is the NDVI of the optical image and how does it compare to the SAR return?
Describe the radar roughness signature of this scene.
What is the C-band backscatter intensity of this SAR image?
```

### ISRO Sensor-Specific
```
Is this a Cartosat-2S panchromatic image or a Sentinel-2 multispectral image?
What C-band radar features are visible in this RISAT-1A image?
Describe the backscatter characteristics of this EOS-04 SAR image.
Is the optical image captured in solar reflectance band or thermal infrared?
Analyse this ISRO satellite image pair for land surface characterization.
```

---

## 🔧 API / Technical Questions (for advanced testing)

These can be asked to test the system's awareness of its own capabilities:

```
What specialist models are available in this system?
What deterministic geospatial tools does OrbilLens use?
What is the overall accuracy of the change detection model?
What datasets were used to train the LULC classifier?
How is the area measurement calculated — is it deterministic?
What is the validation accuracy of the BigEarthNet ResNet-50 model?
```
