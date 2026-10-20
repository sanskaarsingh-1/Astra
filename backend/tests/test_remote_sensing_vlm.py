import pytest
from pathlib import Path
from backend.models.remote_sensing_vlm.dataset import BigEarthNetTxtDataset, load_and_scale_geotiff

PARQUET_PATH = Path("datasets/02_BigEarthNet_txt/BigEarthNet.txt/BigEarthNet.txt.parquet")

@pytest.mark.skipif(not PARQUET_PATH.exists(), reason="BigEarthNet.txt parquet not available")
def test_bigearthnet_txt_dataset_loading():
    dataset = BigEarthNetTxtDataset(
        parquet_path=str(PARQUET_PATH),
        images_dir="datasets/processed/bigearthnet_resnet50_full",
        split="bench",
        max_samples=5,
    )
    assert len(dataset) == 5
    sample = dataset[0]
    assert "patch_id" in sample
    assert "question" in sample
    assert "answer" in sample
    assert "task_type" in sample
    assert sample["image"] is not None
    assert sample["image"].size == (120, 120)

def test_load_and_scale_geotiff_sample():
    sample_img = Path("datasets/processed/bigearthnet_resnet50_full/test/images/S2A_MSIL2A_20170613T101031_N9999_R022_T33UUP_26_57.tif")
    if sample_img.exists():
        arr = load_and_scale_geotiff(sample_img)
        assert arr.shape == (120, 120, 3)
        assert arr.dtype.name == "uint8"
