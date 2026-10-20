"""
Gateway - Metadata Extraction
Extracts deterministic geospatial metadata (CRS, bounds, resolution) from files using rasterio.
"""
import uuid
from pathlib import Path
from typing import Dict, Any
import rasterio
from loguru import logger
try:
    from orchestrator.schemas import ImageManifest, ModalityResult, ModalityEnum
except ImportError:
    from backend.orchestrator.schemas import ImageManifest, ModalityResult, ModalityEnum

try:
    from engine.format_normalizer import ensure_rasterio_compatible
except ImportError:
    from backend.engine.format_normalizer import ensure_rasterio_compatible

def extract_metadata(file_path: Path, file_id: str = None) -> ImageManifest:
    """
    Deterministically extracts spatial metadata from a remote sensing file.
    """
    if file_id is None:
        file_id = str(uuid.uuid4())
        
    try:
        rasterio_path = ensure_rasterio_compatible(file_path)
        was_converted = (Path(rasterio_path) != Path(file_path))
        with rasterio.open(rasterio_path) as dataset:
            width = dataset.width
            height = dataset.height
            count = dataset.count
            driver = file_path.suffix.lstrip('.').upper() if was_converted else dataset.driver
            dtype = dataset.dtypes[0] if count > 0 else "unknown"
            nodata = dataset.nodata
            
            crs_wkt = dataset.crs.to_string() if dataset.crs else None
            crs_epsg = dataset.crs.to_epsg() if dataset.crs else None
            
            is_geospatial = (crs_wkt is not None or crs_epsg is not None) and not was_converted

            
            affine_transform = None
            if dataset.transform and dataset.transform != rasterio.Affine.identity():
                affine_transform = list(dataset.transform)
                
            bounds = None
            if dataset.bounds:
                bounds = {
                    "left": dataset.bounds.left,
                    "bottom": dataset.bounds.bottom,
                    "right": dataset.bounds.right,
                    "top": dataset.bounds.top
                }
                
            gsd_x, gsd_y = None, None
            if dataset.res:
                gsd_x, gsd_y = dataset.res[0], dataset.res[1]
                
            # Extract tags for band descriptions and wavelengths
            band_descriptions = []
            band_wavelengths = []
            for i in range(1, count + 1):
                tags = dataset.tags(i)
                band_descriptions.append(tags.get('DESCRIPTION', f'Band {i}'))
                # Attempt to extract wavelength if present
                wavelength = tags.get('WAVELENGTH')
                if wavelength:
                    try:
                        band_wavelengths.append(float(wavelength))
                    except ValueError:
                        pass
                        
            tags = dataset.tags()
            sensor = tags.get('SENSOR_ID') or tags.get('SENSOR')
            acquisition_date = None  # Could parse tags.get('ACQUISITION_DATETIME') if needed
            
            # Basic validation
            quality_flags = []
            if width == 0 or height == 0:
                quality_flags.append("ZERO_DIMENSION")
            
            # Temporary modality until modality.py takes over
            modality = ModalityResult(
                modality=ModalityEnum.UNKNOWN,
                confidence=0.0,
                evidence=["Pending modality detection"]
            )
            
            try:
                from gateway.modality import detect_modality
            except ImportError:
                from backend.gateway.modality import detect_modality
            
            manifest = ImageManifest(
                file_id=file_id,
                filename=file_path.name,
                file_path=str(file_path),
                format=driver,
                width_px=width,
                height_px=height,
                band_count=count,
                dtype=dtype,
                crs_wkt=crs_wkt,
                crs_epsg=crs_epsg,
                affine_transform=affine_transform,
                bounds=bounds,
                gsd_x=gsd_x,
                gsd_y=gsd_y,
                nodata_value=nodata,
                band_descriptions=band_descriptions,
                band_wavelengths=band_wavelengths,
                modality=ModalityResult(modality=ModalityEnum.UNKNOWN, confidence=0, evidence=[]),
                sensor=sensor,
                acquisition_date=acquisition_date,
                is_geospatial=is_geospatial,
                quality_flags=quality_flags,
                validation_status="VALIDATED"
            )
            manifest.modality = detect_modality(manifest)
            return manifest
                
    except rasterio.errors.RasterioIOError:
        logger.warning(f"Could not read {file_path.name} as a standard geospatial raster. Treating as simple image.")
        # Attempt fallback for non-geospatial image formats like standard PNG/JPEG
        from PIL import Image
        try:
            with Image.open(file_path) as img:
                from gateway.modality import detect_modality
                manifest = ImageManifest(
                    file_id=file_id,
                    filename=file_path.name,
                    file_path=str(file_path),
                    format=img.format,
                    width_px=img.width,
                    height_px=img.height,
                    band_count=len(img.getbands()),
                    dtype="uint8",  # Usually true for PIL images
                    is_geospatial=False,
                    modality=ModalityResult(
                        modality=ModalityEnum.UNKNOWN,
                        confidence=0.0,
                        evidence=["Pending modality detection"]
                    ),
                    validation_status="VALIDATED_AS_NON_SPATIAL"
                )
                manifest.modality = detect_modality(manifest)
                return manifest
        except Exception as e:
            logger.error(f"Fallback PIL parsing failed for {file_path.name}: {e}")
            raise ValueError(f"Unable to parse image data from {file_path.name}")
            
    except Exception as e:
        logger.error(f"Error extracting metadata from {file_path}: {e}")
        raise ValueError(f"Error extracting metadata: {e}")
