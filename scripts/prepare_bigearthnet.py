#!/usr/bin/env python3
"""
Astra AI — BigEarthNet Dataset Preparation Pipeline
=====================================================
Audits raw BigEarthNet v2 archives, validates samples, builds a clean
processed dataset (train/val/test), computes class statistics, generates
manifests, and performs pre-training sanity checks.

CRITICAL RULE:
  This script prepares the dataset ONLY. It does NOT initiate training.
"""

import os
import sys
import json
import csv
import random
import shutil
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
from collections import Counter
import numpy as np
import rasterio
from PIL import Image

# ─── Authoritative 19-Class Definition ──────────────────────────────────────────
# Exactly matches backend/services/model_service.py and backend/training/train_ben_classifier.py
BEN_CLASSES = [
    "Urban fabric",
    "Industrial or commercial units",
    "Arable land",
    "Permanent crops",
    "Pastures",
    "Complex cultivation patterns",
    "Land occupied by agriculture with natural vegetation",
    "Agro-forestry areas",
    "Broad-leaved forest",
    "Coniferous forest",
    "Mixed forest",
    "Natural grassland",
    "Moors and heathland",
    "Sclerophyllous vegetation",
    "Transitional woodland shrub",
    "Beaches, dunes, and sands",
    "Inland wetlands",
    "Coastal wetlands",
    "Water bodies",
]

IDX_TO_LABEL = {i: label for i, label in enumerate(BEN_CLASSES)}
LABEL_TO_IDX = {label: i for i, label in enumerate(BEN_CLASSES)}

# Parquet nomenclature synonym mapping to canonical 19 labels
PARQUET_SYNONYMS = {
    "Land principally occupied by agriculture, with significant areas of natural vegetation": "Land occupied by agriculture with natural vegetation",
    "Natural grassland and sparsely vegetated areas": "Natural grassland",
    "Moors, heathland and sclerophyllous vegetation": "Moors and heathland",
    "Transitional woodland, shrub": "Transitional woodland shrub",
    "Beaches, dunes, sands": "Beaches, dunes, and sands",
    "Inland waters": "Water bodies",
    "Marine waters": "Water bodies",
}

def normalize_label(label: str) -> str:
    """Map Parquet label string to canonical BEN_CLASSES label."""
    if label in LABEL_TO_IDX:
        return label
    if label in PARQUET_SYNONYMS:
        return PARQUET_SYNONYMS[label]
    return label


def audit_raw_dataset(raw_dir: Path, metadata_path: Path):
    """Audit the raw BigEarthNet files on disk."""
    print("=" * 80)
    print("1. AUDITING RAW BIGEARTHNET DATASET")
    print("=" * 80)
    print(f"Raw directory:       {raw_dir}")
    print(f"Metadata parquet:    {metadata_path}")

    assert metadata_path.exists(), f"Metadata not found: {metadata_path}"
    import pyarrow.parquet as pq
    meta_table = pq.read_table(str(metadata_path))
    num_entries = meta_table.num_rows
    print(f"Total entries in metadata.parquet: {num_entries:,}")

    # Archives
    s1_tar = raw_dir / "BigEarthNet-S1.tar.zst"
    s2_tar = raw_dir / "BigEarthNet-S2.tar.zst"
    print(f"BigEarthNet-S1 archive exists: {s1_tar.exists()} ({s1_tar.stat().st_size / (1024**3):.2f} GB)" if s1_tar.exists() else "S1 missing")
    print(f"BigEarthNet-S2 archive exists: {s2_tar.exists()} ({s2_tar.stat().st_size / (1024**3):.2f} GB)" if s2_tar.exists() else "S2 missing")

    return meta_table


def prepare_processed_dataset(
    scratch_extracted_dir: Path,
    metadata_path: Path,
    output_processed_dir: Path,
    manifests_dir: Path,
    target_train_count: int = 1500,
    target_val_count: int = 400,
    target_test_count: int = 400,
    random_seed: int = 42,
):
    """
    Build clean, validated processed dataset with train/val/test splits.
    """
    random.seed(random_seed)
    np.random.seed(random_seed)

    print("\n" + "=" * 80)
    print("2. DISCOVERING & VALIDATING EXTRACTED SAMPLES")
    print("=" * 80)

    import pyarrow.parquet as pq
    table = pq.read_table(str(metadata_path))
    patch_to_split = dict(zip(table["patch_id"].to_pylist(), table["split"].to_pylist()))
    patch_to_labels = dict(zip(table["patch_id"].to_pylist(), table["labels"].to_pylist()))
    patch_to_country = dict(zip(table["patch_id"].to_pylist(), table["country"].to_pylist()))

    # Find all extracted patch directories
    all_patch_dirs = []
    for tile_dir in scratch_extracted_dir.iterdir():
        if tile_dir.is_dir():
            for pdir in tile_dir.iterdir():
                if pdir.is_dir():
                    all_patch_dirs.append(pdir)

    print(f"Discovered {len(all_patch_dirs)} extracted patch directories across tiles.")

    # Validate each candidate patch
    valid_by_split = {"train": [], "val": [], "test": []}
    corrupted_count = 0
    missing_band_count = 0

    for pdir in all_patch_dirs:
        pid = pdir.name
        b4 = pdir / f"{pid}_B04.tif"
        b3 = pdir / f"{pid}_B03.tif"
        b2 = pdir / f"{pid}_B02.tif"

        if not (b4.exists() and b3.exists() and b2.exists()):
            missing_band_count += 1
            continue

        # Check raster validity
        try:
            with rasterio.open(b4) as s4, rasterio.open(b3) as s3, rasterio.open(b2) as s2:
                if s4.shape != (120, 120) or s3.shape != (120, 120) or s2.shape != (120, 120):
                    corrupted_count += 1
                    continue
        except Exception:
            corrupted_count += 1
            continue

        raw_split = patch_to_split.get(pid)
        if not raw_split:
            continue
        
        split = "val" if raw_split == "validation" else raw_split
        if split not in valid_by_split:
            continue

        # Canonical labels
        raw_labels = patch_to_labels.get(pid, [])
        canon_labels = sorted(list(set([normalize_label(l) for l in raw_labels if normalize_label(l) in LABEL_TO_IDX])))
        if not canon_labels:
            continue

        valid_by_split[split].append({
            "patch_id": pid,
            "split": split,
            "labels": canon_labels,
            "country": patch_to_country.get(pid, "Unknown"),
            "b4": b4,
            "b3": b3,
            "b2": b2,
        })

    print(f"Validated patches available:")
    print(f"  Train: {len(valid_by_split['train'])}")
    print(f"  Val:   {len(valid_by_split['val'])}")
    print(f"  Test:  {len(valid_by_split['test'])}")
    print(f"  Corrupted / invalid: {corrupted_count}")
    print(f"  Missing bands:       {missing_band_count}")

    # Deterministic selection
    selected_samples = {}
    for split, target in [("train", target_train_count), ("val", target_val_count), ("test", target_test_count)]:
        pool = valid_by_split[split]
        # Shuffle deterministically
        random.shuffle(pool)
        selected = pool[:min(target, len(pool))]
        selected_samples[split] = selected
        print(f"Selected {len(selected)} samples for {split} split.")

    # Prevent Data Leakage: Verify zero intersection across patch IDs
    train_ids = set(s["patch_id"] for s in selected_samples["train"])
    val_ids = set(s["patch_id"] for s in selected_samples["val"])
    test_ids = set(s["patch_id"] for s in selected_samples["test"])

    assert len(train_ids.intersection(val_ids)) == 0, "DATA LEAKAGE DETECTED: Train and Val overlap!"
    assert len(train_ids.intersection(test_ids)) == 0, "DATA LEAKAGE DETECTED: Train and Test overlap!"
    assert len(val_ids.intersection(test_ids)) == 0, "DATA LEAKAGE DETECTED: Val and Test overlap!"
    print("\n[VERIFIED] Zero data leakage between Train, Validation, and Test splits.")

    # ─── Write Processed Files ──────────────────────────────────────────────────
    print("\n" + "=" * 80)
    print("3. WRITING PROCESSED DATASET (IMAGES & LABELS)")
    print("=" * 80)

    manifest_rows = {split: [] for split in ["train", "val", "test"]}
    class_stats = {split: Counter() for split in ["train", "val", "test"]}

    for split in ["train", "val", "test"]:
        split_dir = output_processed_dir / split
        img_dir = split_dir / "images"
        lbl_dir = split_dir / "labels"
        img_dir.mkdir(parents=True, exist_ok=True)
        lbl_dir.mkdir(parents=True, exist_ok=True)

        for item in selected_samples[split]:
            pid = item["patch_id"]
            labels = item["labels"]
            for l in labels:
                class_stats[split][l] += 1

            # Read B04 (Red), B03 (Green), B02 (Blue)
            with rasterio.open(item["b4"]) as s4, rasterio.open(item["b3"]) as s3, rasterio.open(item["b2"]) as s2:
                r = s4.read(1)
                g = s3.read(1)
                b = s2.read(1)
                meta = s4.meta.copy()

            meta.update({
                "count": 3,
                "dtype": "uint16"
            })

            # Save 3-band GeoTIFF
            out_tif = img_dir / f"{pid}.tif"
            with rasterio.open(out_tif, "w", **meta) as dst:
                dst.write(r, 1)
                dst.write(g, 2)
                dst.write(b, 3)

            # Save 8-bit normalized PNG for visual preview and fast web inspection
            # 2% - 98% percentile stretch per channel
            def stretch(arr):
                p2, p98 = np.percentile(arr[arr > 0], [2, 98]) if (arr > 0).any() else (0, 1)
                scaled = np.clip((arr - p2) / max(p98 - p2, 1e-5), 0, 1) * 255.0
                return scaled.astype(np.uint8)

            rgb_8bit = np.stack([stretch(r), stretch(g), stretch(b)], axis=-1)
            out_png = img_dir / f"{pid}.png"
            Image.fromarray(rgb_8bit).save(out_png)

            # Save Label JSON
            out_json = lbl_dir / f"{pid}.json"
            label_record = {
                "patch_id": pid,
                "split": split,
                "labels": labels,
                "label_indices": [LABEL_TO_IDX[l] for l in labels],
                "country": item["country"],
                "dimensions": [120, 120, 3],
            }
            with open(out_json, "w") as f:
                json.dump(label_record, f, indent=2)

            # Relative path for manifest
            rel_tif = f"datasets/processed/bigearthnet/{split}/images/{pid}.tif"
            rel_png = f"datasets/processed/bigearthnet/{split}/images/{pid}.png"
            rel_lbl = f"datasets/processed/bigearthnet/{split}/labels/{pid}.json"

            manifest_rows[split].append({
                "sample_id": pid,
                "image_path": rel_tif,
                "preview_path": rel_png,
                "label_path": rel_lbl,
                "labels": ";".join(labels),
                "label_indices": ";".join(str(LABEL_TO_IDX[l]) for l in labels),
                "num_labels": len(labels),
                "country": item["country"],
                "split": split,
            })

    # ─── Write Manifests ────────────────────────────────────────────────────────
    print("\n" + "=" * 80)
    print("4. GENERATING MANIFESTS AND STATISTICS")
    print("=" * 80)
    manifests_dir.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "sample_id", "image_path", "preview_path", "label_path",
        "labels", "label_indices", "num_labels", "country", "split"
    ]

    for split in ["train", "val", "test"]:
        csv_path = manifests_dir / f"bigearthnet_{split}.csv"
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(manifest_rows[split])
        print(f"Manifest written: {csv_path} ({len(manifest_rows[split])} samples)")

    # Compute Class Distribution & Imbalance
    stats = {
        "dataset": "BigEarthNet v2.0",
        "task": "Multi-label Scene Classification",
        "num_classes": len(BEN_CLASSES),
        "random_seed": random_seed,
        "splits": {
            "train_samples": len(manifest_rows["train"]),
            "validation_samples": len(manifest_rows["val"]),
            "test_samples": len(manifest_rows["test"]),
            "total_samples": sum(len(manifest_rows[s]) for s in ["train", "val", "test"]),
        },
        "classes": BEN_CLASSES,
        "class_mapping": {i: l for i, l in enumerate(BEN_CLASSES)},
        "class_frequencies": {
            split: {c: class_stats[split][c] for c in BEN_CLASSES}
            for split in ["train", "val", "test"]
        },
        "class_positive_rates": {
            split: {c: round(class_stats[split][c] / max(len(manifest_rows[split]), 1), 4) for c in BEN_CLASSES}
            for split in ["train", "val", "test"]
        },
        "image_specifications": {
            "height": 120,
            "width": 120,
            "channels": 3,
            "band_names": ["B04 (Red)", "B03 (Green)", "B02 (Blue)"],
            "resolution_meters": 10.0,
            "dtype": "uint16",
        },
        "normalization": {
            "training_mean": [0.485, 0.456, 0.406],
            "training_std": [0.229, 0.224, 0.225],
            "target_resolution": [224, 224],
        }
    }

    stats_path = manifests_dir / "bigearthnet_dataset_statistics.json"
    with open(stats_path, "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2)
    print(f"Dataset statistics written: {stats_path}")

    # ─── Sanity Check ───────────────────────────────────────────────────────────
    print("\n" + "=" * 80)
    print("5. LIGHTWEIGHT PRE-TRAINING SANITY CHECK")
    print("=" * 80)
    for split in ["train", "val", "test"]:
        sample = random.choice(manifest_rows[split])
        tif_path = PROJECT_ROOT / sample["image_path"]
        assert tif_path.exists(), f"Image not found: {tif_path}"
        with rasterio.open(tif_path) as src:
            arr = src.read()
            assert arr.shape == (3, 120, 120), f"Unexpected shape: {arr.shape}"
            assert arr.dtype == np.uint16, f"Unexpected dtype: {arr.dtype}"

        # Verify label indices are valid
        lbl_indices = [int(x) for x in sample["label_indices"].split(";")]
        assert all(0 <= idx < len(BEN_CLASSES) for idx in lbl_indices), "Invalid label index"
        print(f"  [PASS] {split.upper():5s} sanity sample: {sample['sample_id']} | labels: {sample['labels'][:40]}... (count: {sample['num_labels']})")

    print("\n[SUCCESS] BigEarthNet dataset preparation completed cleanly!")
    return stats


if __name__ == "__main__":
    raw_directory = PROJECT_ROOT / "datasets" / "01_BigEarthNet_v2"
    parquet_file = raw_directory / "metadata.parquet"
    scratch_dir = PROJECT_ROOT / "datasets" / "scratch" / "BigEarthNet-S2"
    processed_out = PROJECT_ROOT / "datasets" / "processed" / "bigearthnet"
    manifests_out = PROJECT_ROOT / "datasets" / "manifests"

    audit_raw_dataset(raw_directory, parquet_file)
    prepare_processed_dataset(
        scratch_extracted_dir=scratch_dir,
        metadata_path=parquet_file,
        output_processed_dir=processed_out,
        manifests_dir=manifests_out,
        target_train_count=1500,
        target_val_count=400,
        target_test_count=400,
        random_seed=42,
    )
