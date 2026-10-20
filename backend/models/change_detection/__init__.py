"""
Change Detection Specialist Package — Bi-Temporal Image Analysis (LEVIR-CD).
Provides dataset loading, Siamese Bitemporal Image Transformer (BIT) architecture,
spatial alignment checks, deterministic area measurement, and evaluation pipelines.
"""

from .alignment import verify_spatial_alignment, align_image_pair
from .dataset import LEVIRCDDataset, create_levir_dataloader
from .model import BITChangeDetector, ChangeDetectionSpecialist, get_change_specialist

__all__ = [
    "verify_spatial_alignment",
    "align_image_pair",
    "LEVIRCDDataset",
    "create_levir_dataloader",
    "BITChangeDetector",
    "ChangeDetectionSpecialist",
    "get_change_specialist",
]
