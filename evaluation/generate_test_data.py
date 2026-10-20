"""
Evaluation Test Data Generator — SatQuery AI / Astra AI
SIH26167 | Space Technology (ISRO SAC)

Generates representative test rasters for offline evaluation and live demonstrations.
NOTE: These are strictly synthetic REPRESENTATIVE TEST DATA approximating Cartosat-2S and RISAT-1A
sensor characteristics, and are NOT hidden ISRO/SAC evaluation data.
"""

import os
import numpy as np
import rasterio
from rasterio.transform import from_origin


def generate_all_test_data(output_dir: str = "evaluation/test_data"):
    os.makedirs(output_dir, exist_ok=True)
    crs = "EPSG:32643"  # UTM Zone 43N (common for Gujarat / Western India)
    transform_512 = from_origin(300000.0, 2500000.0, 1.0, 1.0)  # 1.0m GSD

    # 1. Representative Cartosat Optical Scene (512x512, 3 bands)
    opt_data = np.zeros((3, 512, 512), dtype=np.uint8)
    opt_data[0] = 110
    opt_data[1] = 145
    opt_data[2] = 85
    opt_data[:, 80:260, 80:260] = 195  # Built-up cluster
    opt_data[0, 360:480, 50:220] = 25   # Water body
    opt_data[1, 360:480, 50:220] = 65
    opt_data[2, 360:480, 50:220] = 175

    opt_path = os.path.join(output_dir, "representative_cartosat_optical.tif")
    with rasterio.open(
        opt_path, "w", driver="GTiff", height=512, width=512, count=3,
        dtype="uint8", crs=crs, transform=transform_512
    ) as dst:
        dst.write(opt_data)
        dst.update_tags(
            DATASET_ROLE="REPRESENTATIVE TEST DATA",
            MISSION="SIMULATED_CARTOSAT_2S",
            SENSOR="PAN_MULTISPECTRAL",
            SPATIAL_RESOLUTION="1.0m",
            TARGET_REGION="UTM_ZONE_43N"
        )

    # 2. Representative RISAT-1A SAR Scene (512x512, 1 band amplitude with speckle)
    np.random.seed(42)
    sar_data = np.random.gamma(shape=3.0, scale=20.0, size=(1, 512, 512)).astype(np.float32)
    sar_data = np.clip(sar_data, 0, 255).astype(np.uint8)
    # Double bounce bright return on urban structures
    sar_data[0, 80:260, 80:260] = np.clip(sar_data[0, 80:260, 80:260] + 120, 0, 255)
    # Low backscatter specular return on water
    sar_data[0, 360:480, 50:220] = np.random.randint(5, 20, size=(120, 170), dtype=np.uint8)

    sar_path = os.path.join(output_dir, "representative_risat_sar.tif")
    with rasterio.open(
        sar_path, "w", driver="GTiff", height=512, width=512, count=1,
        dtype="uint8", crs=crs, transform=transform_512
    ) as dst:
        dst.write(sar_data)
        dst.update_tags(
            DATASET_ROLE="REPRESENTATIVE TEST DATA",
            MISSION="SIMULATED_RISAT_1A",
            SENSOR="C_BAND_SAR_FRS1",
            POLARIZATION="HH_HV",
            SPATIAL_RESOLUTION="2.0m"
        )

    # 3. Bi-Temporal Pair (Pre-event T1 and Post-event T2 with new construction)
    t1_data = np.zeros((3, 512, 512), dtype=np.uint8)
    t1_data[0] = 95
    t1_data[1] = 160
    t1_data[2] = 80
    t1_data[:, 50:180, 50:180] = 190  # Existing urban patch

    t2_data = t1_data.copy()
    # New expansion between dates
    t2_data[:, 220:420, 220:420] = 215  # New industrial/residential expansion

    t1_path = os.path.join(output_dir, "representative_bitemporal_t1.tif")
    with rasterio.open(
        t1_path, "w", driver="GTiff", height=512, width=512, count=3,
        dtype="uint8", crs=crs, transform=transform_512
    ) as dst:
        dst.write(t1_data)
        dst.update_tags(
            DATASET_ROLE="REPRESENTATIVE TEST DATA",
            MISSION="SIMULATED_OPTICAL_T1",
            ACQUISITION_DATE="2023-01-15"
        )

    t2_path = os.path.join(output_dir, "representative_bitemporal_t2.tif")
    with rasterio.open(
        t2_path, "w", driver="GTiff", height=512, width=512, count=3,
        dtype="uint8", crs=crs, transform=transform_512
    ) as dst:
        dst.write(t2_data)
        dst.update_tags(
            DATASET_ROLE="REPRESENTATIVE TEST DATA",
            MISSION="SIMULATED_OPTICAL_T2",
            ACQUISITION_DATE="2024-03-20"
        )

    # 4. Large GeoTIFF (1200x1200px) for windowed tiling verification
    transform_1200 = from_origin(300000.0, 2500000.0, 2.0, 2.0)  # 2m GSD -> 2.4km x 2.4km extent
    large_data = np.zeros((3, 1200, 1200), dtype=np.uint8)
    large_data[0] = 100
    large_data[1] = 150
    large_data[2] = 90
    large_data[:, 300:700, 300:700] = 210  # Dense urban core
    large_data[2, 800:1100, 100:600] = 180 # Large reservoir / wetland

    large_path = os.path.join(output_dir, "representative_large_scene.tif")
    with rasterio.open(
        large_path, "w", driver="GTiff", height=1200, width=1200, count=3,
        dtype="uint8", crs=crs, transform=transform_1200
    ) as dst:
        dst.write(large_data)
        dst.update_tags(
            DATASET_ROLE="REPRESENTATIVE TEST DATA",
            MISSION="SIMULATED_LARGE_MOSAIC",
            SPATIAL_RESOLUTION="2.0m",
            GROUND_COVERAGE="5.76_SQ_KM"
        )

    # 5. Corrupted GeoTIFF for failure testing
    corrupt_path = os.path.join(output_dir, "corrupted_sample.tif")
    with open(corrupt_path, "wb") as f:
        f.write(b"II*\x00\x08\x00\x00\x00FAKE_CORRUPTED_RASTER_DATA_TRUNCATED")

    print(f"Generated 6 representative test datasets in {output_dir}")


if __name__ == "__main__":
    generate_all_test_data()
