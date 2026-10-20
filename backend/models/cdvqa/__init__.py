"""
Change-Based Visual Question Answering (CDVQA) Specialist Package.
Grounds natural-language queries about temporal differences in bi-temporal
change masks and differential LULC transitions (SIH26167).
"""

from .dataset import CDVQADataset, get_cdvqa_samples
from .model import CDVQASpecialist, get_cdvqa_specialist

__all__ = [
    "CDVQADataset",
    "get_cdvqa_samples",
    "CDVQASpecialist",
    "get_cdvqa_specialist",
]
