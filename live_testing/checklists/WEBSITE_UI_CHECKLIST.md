# 📋 Website UI & Feature Testing Checklist
**Scope**: Full website UI, navigation, streaming, evidence viewer, report downloads  
**URL**: https://sih-orbilens-2026-tm.web.app  

---

## 🌐 Page Navigation Tests

| # | Test | How to Test | Pass Criteria | Result |
|:--|:---|:---|:---|:---|
| 1 | Landing page loads | Open https://sih-orbilens-2026-tm.web.app | Space-themed landing appears in < 3s | ⬜ |
| 2 | Analyze page loads | Click "Analyze" or open /analyze | Upload workspace appears | ⬜ |
| 3 | Mission page loads | Open /mission | ISRO SAC architecture page shows | ⬜ |
| 4 | Back navigation | Use browser back button | Returns to correct prior page | ⬜ |
| 5 | Mobile responsive | Open on phone or resize browser to < 768px | Layout adjusts, no overflow | ⬜ |

---

## 📤 Upload Interface Tests

| # | Test | How to Test | Pass Criteria | Result |
|:--|:---|:---|:---|:---|
| 6 | Mode 1 selector | Click "Single Image" mode tab | Upload zone shows 1 slot | ⬜ |
| 7 | Mode 2 selector | Click "Bi-Temporal" mode tab | Upload zone shows 2 slots (Date 1, Date 2) | ⬜ |
| 8 | Mode 3 selector | Click "Cross-Modal" mode tab | Upload zone shows 2 slots (Optical, SAR) | ⬜ |
| 9 | Drag & drop upload | Drag a .tif file onto upload zone | File accepted, filename shown | ⬜ |
| 10 | Click-to-upload | Click upload zone, select file | File accepted, filename shown | ⬜ |
| 11 | Wrong file type | Try to upload a .jpg/.png | Error message shown | ⬜ |
| 12 | Empty submit | Click Investigate with no image | Error: "Please upload an image" | ⬜ |

---

## ✅ Pre-Flight GeoTIFF Validation Badge

| # | Test | How to Test | Pass Criteria | Result |
|:--|:---|:---|:---|:---|
| 13 | Valid GeoTIFF | Upload a valid .tif file | Green ✅ badge with CRS, GSD, WxH | ⬜ |
| 14 | CRS shown | After upload | EPSG code displayed (e.g. EPSG:32632) | ⬜ |
| 15 | GSD shown | After upload | Resolution shown (e.g. 10.0m) | ⬜ |
| 16 | Bi-temporal compatibility | Upload 2 images in Mode 2 | Overlap % and resolution ratio shown | ⬜ |
| 17 | Invalid file rejected | Upload a corrupt file | Red ❌ badge with error message | ⬜ |

---

## 🔴 Live SSE Streaming (Investigation)

| # | Test | How to Test | Pass Criteria | Result |
|:--|:---|:---|:---|:---|
| 18 | Stream starts | Click Investigate | Loading spinner / progress bar appears | ⬜ |
| 19 | Progress steps shown | During stream | Step names appear live (validating, routing, etc.) | ⬜ |
| 20 | Progress % updates | During stream | Percentage increases from 0 → 100 | ⬜ |
| 21 | Stream completes | After stream finishes | Results panel appears, no spinner | ⬜ |
| 22 | Error recovery | Submit with bad image | Error message shown, no crash | ⬜ |
| 23 | Ping keepalive | Long running query | Page stays alive, no timeout | ⬜ |

---

## 🔬 Evidence Findings Viewer

| # | Test | How to Test | Pass Criteria | Result |
|:--|:---|:---|:---|:---|
| 24 | Evidence panel shown | After investigation completes | Evidence findings section visible | ⬜ |
| 25 | DETERMINISTIC label | Check area/distance values | Shows "DETERMINISTIC" status badge | ⬜ |
| 26 | LULC distribution chart | Run Mode 1 with VQA query | Bar chart of CORINE classes shown | ⬜ |
| 27 | Change mask overlay | Run Mode 2 query | Binary mask rendered over image | ⬜ |
| 28 | Change mask slider | Mode 2 — evidence viewer | Side-by-side slider between before/after | ⬜ |
| 29 | Bounding boxes | Run grounding query | Bounding box drawn over image | ⬜ |
| 30 | Conflict alerts | Run cross-modal with conflict | Physical conflict alert shown in red/orange | ⬜ |
| 31 | SAR backscatter dB | Run Mode 3 query | dB value displayed in evidence | ⬜ |

---

## 🕵️ Observable Execution Trace

| # | Test | How to Test | Pass Criteria | Result |
|:--|:---|:---|:---|:---|
| 32 | Trace panel visible | After investigation | "Execution Trace" section shown | ⬜ |
| 33 | Step IDs shown | Expand trace | Each step has `step_id` label | ⬜ |
| 34 | Tool IDs shown | Expand trace | Each tool call has `tool_id` label | ⬜ |
| 35 | Duration (ms) shown | Expand trace | Millisecond latency shown per step | ⬜ |
| 36 | No raw CoT leaked | Read trace carefully | No internal chain-of-thought text visible | ⬜ |

---

## 📊 Model & Tool Registry Modal

| # | Test | How to Test | Pass Criteria | Result |
|:--|:---|:---|:---|:---|
| 37 | Open registry modal | Click "Model Registry" button | Modal opens with 7 specialists listed | ⬜ |
| 38 | Specialist models listed | Inside modal | All 7 models shown with metrics | ⬜ |
| 39 | Tool registry shown | Inside modal | 10 deterministic tools listed | ⬜ |
| 40 | BIT metrics shown | Inside modal | OA: 96.98%, F1: 69.56% shown | ⬜ |
| 41 | ResNet-50 metrics shown | Inside modal | Val Acc: 91.79%, Macro F1: 70.38% shown | ⬜ |
| 42 | Close modal | Click X or outside | Modal closes cleanly | ⬜ |

---

## 📥 Report Download Tests

| # | Test | How to Test | Pass Criteria | Result |
|:--|:---|:---|:---|:---|
| 43 | Download Markdown | Click "Download .md" | `.md` file downloads | ⬜ |
| 44 | Markdown content | Open downloaded .md | Contains report text, findings, models used | ⬜ |
| 45 | Download HTML | Click "Download .html" | `.html` file downloads | ⬜ |
| 46 | HTML renders | Open .html in browser | Styled report, readable in browser | ⬜ |
| 47 | Download JSON | Click "Download .json" | `.json` file downloads | ⬜ |
| 48 | JSON structure | Open .json | Has `report`, `evidence`, `trace` keys | ⬜ |
| 49 | JSON DETERMINISTIC | Check JSON evidence | Area values carry `calculation_status: "DETERMINISTIC"` | ⬜ |

---

## 🎯 End-to-End Scenario Tests

| # | Scenario | Mode | Question | Expected | Result |
|:--|:---|:---|:---|:---|:---|
| 50 | Urban scene | Mode 1 | "Is this area urban or rural?" | Urban classification + LULC | ⬜ |
| 51 | Water detection | Mode 1 | "Is there a water body?" | Yes/No with evidence | ⬜ |
| 52 | Change detection | Mode 2 | "What has changed?" | Change mask + area m² | ⬜ |
| 53 | Area in ha | Mode 2 | "How many hectares changed?" | Numeric ha value | ⬜ |
| 54 | Optical/SAR agree | Mode 3 | "Do these images agree?" | Agreement or conflict | ⬜ |
| 55 | SAR backscatter | Mode 3 | "What is the backscatter in dB?" | dB value in evidence | ⬜ |

---

## 📊 Summary Score

```
Total Tests: 55
Passed:  ___
Failed:  ___
Skipped: ___

Pass Rate: ____%
```

**Tester Name**: ___________________________  
**Date of Test**: ___________________________  
**Browser Used**: ___________________________  
**Device / OS**: ___________________________  
**Backend Running**: ☐ Live (Firebase) / ☐ Local (localhost:8000)
