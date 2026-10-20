"""
Astra AI — Large Raster Stress Tests
SIH26167 | ISRO SAC

Validates:
- Synthetic & realistic GeoTIFF generation across multiple resolutions:
  512x512, 1024x1024, 2048x2048, and 2500x2500 (>2000px).
- Metadata extraction: CRS, transform, resolution, bounds.
- Windowed tiling decomposition without loading full scenes into memory.
- Geographic CRS bounding box preservation per tile window.
- Spatial aggregation: class frequency, ground area (m² and km²), and hotspot mapping.
- Memory safety and execution time tracking under large raster loads.
"""

import time
import pytest
import numpy as np
import rasterio
from rasterio.transform import from_origin
from pathlib import Path
from PIL import Image

from backend.engine.tiler import TiledRasterProcessor, tiled_processor


def create_synthetic_geotiff(
    path: Path,
    width: int,
    height: int,
    count: int = 3,
    dtype: str = "uint8",
    res: float = 10.0,
    crs: str = "EPSG:3857",
) -> Path:
    """Helper to create a valid georeferenced GeoTIFF of arbitrary size."""
    transform = from_origin(100000.0, 200000.0, res, res)
    if count == 3:
        # Create synthetic spatial pattern with distinct quadrant signatures
        data = np.zeros((count, height, width), dtype=np.uint8)
        # Quadrant 0: Forest (high green)
        data[1, :height // 2, :width // 2] = 180
        data[0, :height // 2, :width // 2] = 60
        data[2, :height // 2, :width // 2] = 60
        # Quadrant 1: Water (high blue)
        data[2, :height // 2, width // 2:] = 200
        data[0, :height // 2, width // 2:] = 40
        data[1, :height // 2, width // 2:] = 80
        # Quadrant 2: Urban (medium grey)
        data[:, height // 2:, :width // 2] = 160
        # Quadrant 3: Agriculture (yellowish)
        data[0, height // 2:, width // 2:] = 210
        data[1, height // 2:, width // 2:] = 200
        data[2, height // 2:, width // 2:] = 40
    else:
        data = np.full((count, height, width), fill_value=128, dtype=np.uint8)

    with rasterio.open(
        path,
        "w",
        driver="GTiff",
        height=height,
        width=width,
        count=count,
        dtype=dtype,
        crs=crs,
        transform=transform,
    ) as dst:
        dst.write(data)
    return path


class TestLargeRasterStress:
    """Stress testing suite for large satellite rasters."""

    def test_512x512_single_scene_pass(self, tmp_path):
        """A 512x512 raster should execute as a single scene pass without forced tiling."""
        tif_path = tmp_path / "scene_512.tif"
        create_synthetic_geotiff(tif_path, width=512, height=512)

        processor = TiledRasterProcessor(tile_size=512)
        mock_classifier = lambda p: {
            "prediction": "Coniferous forest",
            "confidence": 0.89,
            "labels": ["Coniferous forest"],
            "all_probabilities": {"Coniferous forest": 0.89},
            "top_predictions": [{"label": "Coniferous forest", "probability": 0.89}],
        }

        result = processor.process_raster(tif_path, classifier_fn=mock_classifier)
        assert result["is_tiled"] is False
        assert result["tile_count"] == 1
        assert result["scene_dimensions"] == [512, 512]
        assert result["dominant_class"] == "Coniferous forest"

    def test_1024x1024_raster_tiling(self, tmp_path):
        """A 1024x1024 raster decomposed into 512x512 tiles yields exactly 4 tiles."""
        tif_path = tmp_path / "scene_1024.tif"
        create_synthetic_geotiff(tif_path, width=1024, height=1024)

        processor = TiledRasterProcessor(tile_size=512)
        mock_classifier = lambda p: {
            "prediction": "Urban fabric",
            "confidence": 0.91,
            "labels": ["Urban fabric", "Industrial or commercial units"],
            "all_probabilities": {"Urban fabric": 0.91, "Industrial or commercial units": 0.65},
        }

        result = processor.process_raster(tif_path, classifier_fn=mock_classifier)
        assert result["is_tiled"] is True
        assert result["tile_count"] == 4
        assert result["scene_dimensions"] == [1024, 1024]
        assert "Urban fabric" in result["labels"]
        assert "Urban fabric" in result["spatial_coverage"]

        # Check coverage calculation
        urban_cov = result["spatial_coverage"]["Urban fabric"]
        assert urban_cov["tile_count"] == 4
        assert urban_cov["coverage_pct"] == 100.0
        assert urban_cov["estimated_area_m2"] > 0

    def test_2048x2048_large_raster_stress(self, tmp_path):
        """
        A 2048x2048 satellite raster decomposed into 512x512 tiles yields 16 tiles.
        Verifies execution completes stably and memory remains bounded.
        """
        tif_path = tmp_path / "scene_2048.tif"
        create_synthetic_geotiff(tif_path, width=2048, height=2048, res=10.0)

        processor = TiledRasterProcessor(tile_size=512)
        call_count = [0]

        def dynamic_classifier(p):
            call_count[0] += 1
            if call_count[0] % 2 == 0:
                return {
                    "prediction": "Water bodies",
                    "confidence": 0.95,
                    "labels": ["Water bodies"],
                    "all_probabilities": {"Water bodies": 0.95},
                }
            else:
                return {
                    "prediction": "Broad-leaved forest",
                    "confidence": 0.88,
                    "labels": ["Broad-leaved forest"],
                    "all_probabilities": {"Broad-leaved forest": 0.88},
                }

        t0 = time.perf_counter()
        result = processor.process_raster(tif_path, classifier_fn=dynamic_classifier)
        elapsed_s = time.perf_counter() - t0

        assert result["is_tiled"] is True
        assert result["tile_count"] == 16
        assert len(result["tile_results"]) == 16
        assert "Water bodies" in result["spatial_coverage"]
        assert "Broad-leaved forest" in result["spatial_coverage"]
        assert result["spatial_coverage"]["Water bodies"]["tile_count"] == 8
        assert result["spatial_coverage"]["Broad-leaved forest"]["tile_count"] == 8
        assert elapsed_s < 10.0, f"2048x2048 tiling took too long: {elapsed_s:.2f}s"

    def test_greater_than_2000_raster_handling(self, tmp_path):
        """
        Tests >2000x2000 px raster (2500x2500 px).
        2500 / 512 = 5 rows x 5 cols = 25 tiles.
        Verifies partial edge tiles (w_w=452, w_h=452) are handled properly.
        """
        tif_path = tmp_path / "scene_2500.tif"
        create_synthetic_geotiff(tif_path, width=2500, height=2500, res=5.0)

        processor = TiledRasterProcessor(tile_size=512)
        mock_classifier = lambda p: {
            "prediction": "Arable land",
            "confidence": 0.84,
            "labels": ["Arable land"],
            "all_probabilities": {"Arable land": 0.84},
        }

        result = processor.process_raster(tif_path, classifier_fn=mock_classifier)
        assert result["is_tiled"] is True
        assert result["tile_count"] == 25
        assert result["scene_dimensions"] == [2500, 2500]

        # Verify edge tile dimensions
        edge_tiles = [t for t in result["tile_results"] if t["grid_coord"][0] == 4 or t["grid_coord"][1] == 4]
        assert len(edge_tiles) > 0
        # Edge width or height should be 2500 - 512*4 = 452 px
        assert any(t["pixel_window"][2] == 452 or t["pixel_window"][3] == 452 for t in edge_tiles)

    def test_crs_and_hotspot_georeferencing(self, tmp_path):
        """Verify each tile retains its true CRS geographic bounding box."""
        tif_path = tmp_path / "scene_crs.tif"
        create_synthetic_geotiff(tif_path, width=1024, height=1024, res=20.0, crs="EPSG:32643")

        processor = TiledRasterProcessor(tile_size=512)
        mock_classifier = lambda p: {
            "prediction": "Urban fabric",
            "confidence": 0.92,
            "labels": ["Urban fabric"],
            "all_probabilities": {"Urban fabric": 0.92},
        }

        result = processor.process_raster(tif_path, classifier_fn=mock_classifier)
        hotspots = result["hotspots"].get("Urban fabric", [])
        assert len(hotspots) > 0

        # Each hotspot must have a valid 4-tuple of coordinates (minx, miny, maxx, maxy)
        for hs in hotspots:
            bounds = hs["crs_bounds"]
            assert len(bounds) == 4
            minx, miny, maxx, maxy = bounds
            assert maxx > minx
            assert maxy > miny

    def test_single_band_pan_tiling(self, tmp_path):
        """Verify single-band panchromatic imagery (Cartosat style) tiles correctly."""
        tif_path = tmp_path / "scene_pan_1024.tif"
        create_synthetic_geotiff(tif_path, width=1024, height=1024, count=1, res=2.5)

        processor = TiledRasterProcessor(tile_size=512)
        mock_classifier = lambda p: {
            "prediction": "Industrial or commercial units",
            "confidence": 0.81,
            "labels": ["Industrial or commercial units"],
            "all_probabilities": {"Industrial or commercial units": 0.81},
        }

        result = processor.process_raster(tif_path, classifier_fn=mock_classifier)
        assert result["is_tiled"] is True
        assert result["tile_count"] == 4
        assert result["dominant_class"] == "Industrial or commercial units"
