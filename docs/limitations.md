# Astra AI — Known Technical Limitations & Constraints

In alignment with our engineering commitment to honesty, transparency, and scientific rigor, this document details current system boundaries, unverified metrics, and areas under active development.

---

## 1. Domain & Sensor Limitations

- **Resolution Physics Boundary**: The platform processes macro-satellite imagery (Sentinel-2 at 10m GSD, Landsat at 30m, Cartosat-2S at 0.65m panchromatic). It cannot detect or identify individual humans, moving vehicles under sub-pixel scales, or internal room contents. Such queries are rejected at the input gateway.
- **SAR Speckle Noise & Geometric Distortions**: SAR backscatter analysis (`sar-stats`) operates on radiometrically calibrated $\sigma^0$ data. Steep mountain topography causes layover and radar shadow which requires external high-resolution DEM orthorectification.
- **Cloud Obscuration in Optical Imagery**: Dense cloud cover severely attenuates optical reflectance. While the Cross-Modal Specialist uses SAR to verify structural persistence through clouds, optical LULC classification under heavy cloud cover defaults to cloudy confidence degradation.

---

## 2. Model & Metric Provenance Limitations

- **Hidden ISRO / SAC Evaluation Set**: The official private evaluation set from ISRO SAC was not released publicly during hackathon development. Consequently, all reported metrics are strictly benchmarked on public validation splits (BigEarthNet v2.0 reBEN, LEVIR-CD, CDVQA).
- **VLM Full Training Budget**: The `rs-vlm-adapter` (Salesforce/blip-image-captioning-base + PEFT LoRA) completed 1 epoch (1,000 steps) on BigEarthNet.txt. While binary question accuracy reached 70.8%, multi-choice and bounding box tasks scored 25.0% and require 3–5 additional training epochs.
- **End-to-End Optical-SAR Fusion Metric**: Cross-modal physical conflict detection is implemented using verified physical rules (optical reflectance vs. radar microwave backscatter), but a dedicated unified multimodal benchmark score is pending standardized community benchmarks.
