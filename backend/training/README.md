# BigEarthNet Classifier Training

## Purpose
Train a ResNet-50 multi-label classifier on BigEarthNet v2 to satisfy the SIH26167 mandatory requirement:
> "at least one remote-sensing visual/VLM component adapted using BigEarthNet.txt or permitted open-source training data"

## Dataset Download

BigEarthNet v2 is available at: **https://bigearth.net/**

License: **CDLA-Permissive-1.0** (permits training use)

```
Total size: ~66 GB
Patches: 549,488 pairs (Sentinel-1 + Sentinel-2)
Labels: 19 LULC classes (CORINE Land Cover 2018)
```

## Expected Data Structure

```
/path/to/bigearth-net-v2/
  images/
    S2B_MSIL2A_20170613T101031_0_33/
      B01.tif  B02.tif  B03.tif  B04.tif  B05.tif
      B06.tif  B07.tif  B08.tif  B8A.tif  B09.tif
      B11.tif  B12.tif
    ...
  labels/
    S2B_MSIL2A_20170613T101031_0_33.json
    ...
```

## Training Command

```bash
# From the backend/ directory
python training/train_ben_classifier.py \
  --data_dir /path/to/bigearth-net-v2 \
  --output_dir ./checkpoints \
  --epochs 20 \
  --batch_size 64 \
  --lr 1e-4
```

## After Training

Copy the best checkpoint to the models directory:
```bash
cp checkpoints/ben_classifier.pth models/ben_classifier.pth
```

## Expected Performance (Reference)

On BigEarthNet v2 test split with ResNet-50:
- Macro F1: ~0.75-0.82 (depends on epochs and augmentation)
- These are literature reference values; actual results will vary.

## Notes

- We train only on Sentinel-2 RGB bands (B04/B03/B02) for simplicity.
- Including NIR (B08) as a 4th channel would improve performance but adds complexity.
- The domain gap to Cartosat-2S is HIGH for object detection but acceptable for scene-level classification.
- Report training metrics and the BigEarthNet citation in the SIH presentation.
