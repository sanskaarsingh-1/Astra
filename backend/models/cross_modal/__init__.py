"""
Optical + SAR Cross-Modal Specialist Package.
Combines complementary physical mechanisms (optical spectral reflectance + SAR backscatter geometry)
for joint all-weather remote sensing analysis (SIH26167).
"""

from .specialist import CrossModalSpecialist, get_cross_modal_specialist

__all__ = [
    "CrossModalSpecialist",
    "get_cross_modal_specialist",
]
