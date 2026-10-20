"""
Gateway - Modality Detection
Infers the sensing modality (Optical, SAR, Multispectral, DEM, etc.) based on metadata.
"""
from typing import Dict, Any
try:
    from orchestrator.schemas import ModalityResult, ModalityEnum, ImageManifest
except ImportError:
    from backend.orchestrator.schemas import ModalityResult, ModalityEnum, ImageManifest

def detect_modality(manifest: ImageManifest) -> ModalityResult:
    """
    Analyzes the extracted metadata to classify the modality with confidence and evidence.
    """
    filename = manifest.filename.lower()
    channels = manifest.band_count
    
    evidence = []
    
    # Check sensor metadata if available
    if manifest.sensor:
        sensor = manifest.sensor.lower()
        if any(kw in sensor for kw in ["risat", "risat-1", "risat-1a", "eos-04", "eos04"]):
            evidence.append(f"Sensor metadata indicates ISRO RISAT C-band SAR: {manifest.sensor}")
            return ModalityResult(modality=ModalityEnum.SAR, confidence=0.98, evidence=evidence)
        if any(kw in sensor for kw in ["cartosat", "cartosat-2", "cartosat-2s", "carto"]):
            evidence.append(f"Sensor metadata indicates ISRO Cartosat-2S High-Res Optical: {manifest.sensor}")
            return ModalityResult(modality=ModalityEnum.PANCHROMATIC, confidence=0.95, evidence=evidence)
        if any(kw in sensor for kw in ["sar", "sentinel-1", "s1"]):
            evidence.append(f"Sensor metadata indicates SAR: {manifest.sensor}")
            return ModalityResult(modality=ModalityEnum.SAR, confidence=0.95, evidence=evidence)
            
    # Check band descriptions (linear & hybrid polarisations)
    desc_str = " ".join([d.lower() for d in manifest.band_descriptions])
    if any(p in desc_str for p in ["vv", "vh", "hh", "hv", "rh", "rv"]):
        evidence.append("Band descriptions contain SAR polarisation (VV, VH, HH, HV, RH, RV)")
        return ModalityResult(modality=ModalityEnum.SAR, confidence=0.92, evidence=evidence)
        
    # Check filename naming conventions (including ISRO conventions)
    if any(keyword in filename for keyword in ["risat", "eos04", "eos-04", "sar", "sentinel-1", "s1a", "s1b"]):
        evidence.append("Filename matches known SAR naming conventions (Sentinel-1 / RISAT)")
        return ModalityResult(modality=ModalityEnum.SAR, confidence=0.85, evidence=evidence)

    if any(keyword in filename for keyword in ["cartosat", "carto", "cartosat-2s"]):
        evidence.append("Filename matches ISRO Cartosat high-resolution optical convention")
        return ModalityResult(modality=ModalityEnum.PANCHROMATIC, confidence=0.88, evidence=evidence)
        
    if any(keyword in filename for keyword in ["dem", "dsm", "dtm", "elevation"]):
        evidence.append("Filename matches known DEM naming conventions")
        return ModalityResult(modality=ModalityEnum.DEM, confidence=0.8, evidence=evidence)
        
    # Check channel counts and spectral metadata
    if channels == 1:
        if "pan" in filename or "panchromatic" in filename:
            evidence.append("Single band with 'pan' in filename")
            return ModalityResult(modality=ModalityEnum.PANCHROMATIC, confidence=0.8, evidence=evidence)
        elif manifest.dtype in ["complex64", "complex128"]:
            evidence.append("Single band with complex datatype is typical for SLC SAR")
            return ModalityResult(modality=ModalityEnum.SAR, confidence=0.85, evidence=evidence)
        else:
            evidence.append("Single band image (could be grayscale optical, SAR intensity, or DEM)")
            return ModalityResult(modality=ModalityEnum.AMBIGUOUS, confidence=0.4, evidence=evidence)
            
    elif channels == 3:
        evidence.append("3 bands strongly suggests RGB Optical")
        return ModalityResult(modality=ModalityEnum.OPTICAL_RGB, confidence=0.85, evidence=evidence)
        
    elif channels >= 4:
        evidence.append(f"{channels} bands strongly suggests Multispectral Optical")
        return ModalityResult(modality=ModalityEnum.OPTICAL_MULTISPECTRAL, confidence=0.85, evidence=evidence)
            
    # Default fallback
    evidence.append("No strong indicators found")
    return ModalityResult(modality=ModalityEnum.UNKNOWN, confidence=0.1, evidence=evidence)
