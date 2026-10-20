# 🛰️ ASTRA AI
### AI-Powered Satellite Image Analysis & Geospatial Intelligence

**Ask Questions. Understand Satellite Images.**

ASTRA AI is an intelligent satellite image analysis platform that combines **Artificial Intelligence, Deep Learning, Computer Vision, and Geospatial Technologies** to make Earth observation more accessible, accurate, and interactive.

Instead of relying on complex GIS software or technical expertise, users can upload satellite imagery, ask questions in natural language, detect environmental changes, identify land-cover types, and perform geospatial measurements through a unified AI-powered workspace.

---

## 🌍 Overview

Satellite imagery provides valuable information about urban development, deforestation, agriculture, water bodies, and natural disasters. However, extracting meaningful insights often requires specialized tools and technical knowledge.

**ASTRA AI bridges this gap** by integrating multiple specialized AI models with geospatial processing tools.

The platform selects suitable AI models based on the user's query, performs image analysis, and presents understandable results with supporting evidence.

## ✨ Key Features

### 🛰️ Satellite Image Understanding
- Upload and analyze satellite images.
- Identify land-cover categories such as forests, water bodies, and buildings.
- Generate AI-powered descriptions of satellite imagery.

### 🔄 Multi-Temporal Change Detection
- Compare satellite images captured on different dates.
- Detect changes in land use and geographical features.
- Analyze urban expansion and environmental changes.

### 💬 Natural Language Satellite Queries
- Ask questions about satellite images using everyday language.
- Receive AI-generated answers based on image content.
- Locate objects and geographical features through text queries.

### 📍 Visual Grounding
- Identify specific regions within satellite imagery.
- Locate areas matching natural language descriptions.
- Support region-based satellite image analysis.

### 📡 Optical & Radar Image Analysis
- Support optical satellite imagery.
- Combine optical and radar information for enhanced analysis.
- Enable analysis across different satellite imaging modalities.

### 📐 Geospatial Measurements
- Calculate geographical areas and distances using dedicated map tools.
- Perform spatial analysis using geospatial libraries.
- Provide measurement-based evidence instead of relying on AI-generated estimates.

### 📊 Analysis Reports
- Display AI-generated findings.
- Review analysis results and supporting information.
- Download reports for further study.

---

## 🧠 AI Models & Specialists

ASTRA AI uses a multi-model architecture where different AI specialists handle different satellite image analysis tasks.

| AI Model | Function |
|---|---|
| ResNet-50 v2 | Land-cover classification |
| BIT + Siamese ResNet-18 | Satellite image change detection |
| RSVQA | Remote sensing visual question answering |
| VRSBench Captioner | Satellite image description generation |
| VRSBench Grounding | Text-based region localization |
| CDVQA | Change-related visual question answering |
| Optical + Radar Specialist | Multimodal satellite image analysis |
| BLIP + LoRA | Image-text model adaptation |

**Reported land-cover classification test accuracy: 91.67%.**

Model performance varies by task and dataset.

---

## 🏗️ Technology Stack

| Component | Technologies |
|---|---|
| Frontend | Next.js, React |
| Backend | Python, FastAPI |
| AI & Deep Learning | PyTorch |
| AI Integration | Google Gemini |
| Geospatial Processing | Rasterio, PyProj, Shapely |
| Hosting | Firebase Hosting |

---

## ⚙️ System Architecture

ASTRA AI follows a structured four-stage processing pipeline.

**1. Upload**

Users upload satellite imagery and submit a question or analysis request.

↓

**2. Preprocessing**

The system validates the uploaded files and prepares imagery for analysis.

↓

**3. AI Analysis**

ASTRA selects appropriate specialized AI models and geospatial tools based on the requested task.

↓

**4. Results & Visualization**

The platform displays findings, measurements, supporting evidence, and downloadable reports.

---

## 🚀 How It Works

1. **Choose Analysis Mode:** Select single-image analysis, two-date comparison, or optical and radar analysis.
2. **Upload Satellite Imagery:** Provide the relevant satellite images.
3. **Ask a Question:** Enter a natural language query describing what you want to analyze.
4. **Run AI Analysis:** ASTRA selects and executes the appropriate AI specialists.
5. **Explore Results:** Review generated insights, geographical measurements, and reports.

---

## 🌱 Real-World Applications

**Urban Planning**
- Monitoring urban expansion
- Studying infrastructure development
- Detecting changes in built-up areas

**Environmental Monitoring**
- Tracking deforestation
- Analyzing vegetation changes
- Monitoring land-cover transformation

**Disaster Management**
- Studying flood-affected regions
- Examining wildfire-related landscape changes
- Supporting post-disaster satellite image analysis

**Agriculture & Land Management**
- Identifying agricultural regions
- Observing changes in vegetation
- Supporting land-use studies

---

## 🧪 Testing & Evaluation

ASTRA AI is evaluated using different satellite image types and analysis tasks.

**Testing Areas:**
- Land-cover classification
- Satellite image captioning
- Visual question answering
- Multi-temporal change detection
- Optical and radar imagery
- Large image processing
- Invalid or damaged file handling
- Report generation

Evaluation emphasizes task-specific accuracy, repeatability, and reliable geospatial measurements.

---

## 🎯 Sustainable Development Goals

ASTRA AI supports applications aligned with the United Nations Sustainable Development Goals.

- **SDG 9 — Industry, Innovation and Infrastructure:** Satellite-based infrastructure analysis.
- **SDG 11 — Sustainable Cities and Communities:** Monitoring urban development.
- **SDG 13 — Climate Action:** Environmental and disaster-related observations.
- **SDG 15 — Life on Land:** Forest, vegetation, and land-cover monitoring.

---

## 🔮 Future Scope

- Improve AI model accuracy and reliability.
- Expand testing across diverse satellite datasets.
- Enhance visualization of detected changes.
- Improve uncertainty estimation and explanation.
- Strengthen multimodal satellite image understanding.
- Expand geospatial analysis capabilities.

---

## 👨‍💻 Project Team

- **Sanskaar Singh**
- **Varad Walawalkar**
- **Akshat Zaveri**

**Project Guide:** Soumyojyoti

---

## 📚 References

- [BigEarthNet Satellite Dataset](https://bigearth.net/)
- [PyTorch Documentation](https://pytorch.org/docs/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Rasterio Documentation](https://rasterio.readthedocs.io/)
- [PyProj Documentation](https://pyproj4.github.io/pyproj/stable/)

---

## ⭐ Support

If you find ASTRA AI interesting, consider giving the repository a ⭐ on GitHub.

**ASTRA AI — Making Satellite Intelligence Accessible Through Artificial Intelligence.**
