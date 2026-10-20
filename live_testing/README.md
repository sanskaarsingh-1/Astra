# 🛰️ OrbilLens AI — Live Testing Suite
**Project**: SIH26167 — SatQuery AI (ISRO Space Applications Centre)  
**Live URL**: https://sih-orbilens-2026-tm.web.app  
**Last Updated**: September 2026  

---

## What This Folder Is

This is the **Live Website Testing Suite** for OrbilLens AI. It contains:

| Folder / File | Purpose |
|:---|:---|
| `PROMPTS_AND_TEST_CASES.md` | ⭐ **Master Quick-Reference** with copy-paste prompts mapped to every image |
| `images/single_image/` | 7 Sample GeoTIFF satellite images + `PROMPTS.md` for Mode 1 (VQA, LULC, Caption) |
| `images/bi_temporal/before/` | 4 "Date 1" images for Bi-Temporal Change Detection |
| `images/bi_temporal/after/` | 4 matching "Date 2" images for Bi-Temporal Change Detection + `PROMPTS.md` |
| `images/cross_modal/optical/` | 3 Optical (Sentinel-2 / Cartosat) images for Cross-Modal testing |
| `images/cross_modal/sar/` | 3 matching SAR (RISAT-1A / EOS-04 C-band) images + `PROMPTS.md` |
| `checklists/` | Question banks and test checklists per mode |
| `reports/` | Save your exported investigation reports here |

---

## 3 Upload Modes on the Website

```
┌─────────────────────────────────────────────────────────────────┐
│  OrbilLens AI — https://sih-orbilens-2026-tm.web.app/analyze   │
├─────────────────────────────────────────────────────────────────┤
│  MODE 1: Single Image                                           │
│    → 1 satellite image  → VQA / LULC / Captioning              │
│                                                                 │
│  MODE 2: Bi-Temporal                                            │
│    → Image Date 1 + Image Date 2  → Change Detection           │
│                                                                 │
│  MODE 3: Cross-Modal                                            │
│    → Optical + SAR pair  → Physics-based conflict analysis      │
└─────────────────────────────────────────────────────────────────┘
```

---

## How to Run a Live Test

1. Open the website: **https://sih-orbilens-2026-tm.web.app/analyze**
2. Pick the right upload mode (see above)
3. Upload the image(s) from the matching `images/` subfolder
4. Wait for the **Pre-flight GeoTIFF Validation badge** (green ✅ = valid)
5. Type a question from the relevant checklist in `checklists/`
6. Click **Investigate** and watch the live SSE stream
7. Check: progress steps → evidence findings → observable trace → report
8. Download the report (`.md` / `.html` / `.json`) and save to `reports/`
9. Record results in `checklists/TEST_LOG.md`

---

## Quick Links

| Page | URL |
|:---|:---|
| Mission / Landing | https://sih-orbilens-2026-tm.web.app |
| Analysis Workspace | https://sih-orbilens-2026-tm.web.app/analyze |
| ISRO Architecture | https://sih-orbilens-2026-tm.web.app/mission |
| Local Backend Docs | http://localhost:8000/docs |
| Local Frontend | http://localhost:3000 |
