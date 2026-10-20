#!/usr/bin/env python3
"""
Astra AI - CDVQA & SECOND Imagery Reusable Validation Script
Validates 100% coverage and integrity of the 2,968 CDVQA bi-temporal image pairs.
Exit status 0: All pairs present, valid, readable, and 512x512.
Exit status 1: Any missing, corrupt, or invalid image.
"""

import os
import sys
import json
from PIL import Image

def validate():
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    cdvqa_root = os.path.join(repo_root, "datasets", "04_CDVQA")
    json_dir = os.path.join(cdvqa_root, "CDVQA-main")
    img_dir = os.path.join(cdvqa_root, "images")
    im1_dir = os.path.join(img_dir, "im1")
    im2_dir = os.path.join(img_dir, "im2")

    print("==================================================")
    print("ASTRA AI — CDVQA VALIDATION SCRIPT")
    print("==================================================")
    print(f"CDVQA Root: {cdvqa_root}")
    print(f"Images: im1={im1_dir}, im2={im2_dir}")

    if not os.path.exists(json_dir):
        print(f"ERROR: JSON directory not found: {json_dir}")
        sys.exit(1)
    if not os.path.exists(im1_dir) or not os.path.exists(im2_dir):
        print(f"ERROR: Images directory not found: {im1_dir} or {im2_dir}")
        sys.exit(1)

    splits = ['Train', 'Val', 'Test', 'Test2']
    unique_ids = set()
    split_ids = {}

    for s in splits:
        jf = os.path.join(json_dir, f"{s}_images.json")
        if not os.path.exists(jf):
            print(f"ERROR: Missing annotation file: {jf}")
            sys.exit(1)
        with open(jf, 'r') as f:
            data = json.load(f)
        ids = sorted(list(set(x['file_name'] for x in data.get('images', []))))
        split_ids[s] = ids
        unique_ids.update(ids)

    total_expected = 2968
    if len(unique_ids) != total_expected:
        print(f"ERROR: Expected {total_expected} unique IDs, found {len(unique_ids)}")
        sys.exit(1)

    print(f"Verified CDVQA Unique IDs: {len(unique_ids)}")
    for s in splits:
        print(f"  Split {s:<5}: {len(split_ids[s])} unique IDs")

    missing = []
    corrupted = []
    dimension_mismatches = []
    verified_pairs = 0

    for idx, img_id in enumerate(sorted(unique_ids), 1):
        p_a = os.path.join(im1_dir, img_id)
        p_b = os.path.join(im2_dir, img_id)

        if not os.path.exists(p_a):
            missing.append((img_id, 'im1'))
            continue
        if not os.path.exists(p_b):
            missing.append((img_id, 'im2'))
            continue

        # Validate A
        try:
            with Image.open(p_a) as img_a:
                img_a.verify()
            with Image.open(p_a) as img_a:
                dim_a = img_a.size
                if dim_a != (512, 512):
                    dimension_mismatches.append((p_a, dim_a))
        except Exception as e:
            corrupted.append((p_a, str(e)))
            continue

        # Validate B
        try:
            with Image.open(p_b) as img_b:
                img_b.verify()
            with Image.open(p_b) as img_b:
                dim_b = img_b.size
                if dim_b != (512, 512):
                    dimension_mismatches.append((p_b, dim_b))
        except Exception as e:
            corrupted.append((p_b, str(e)))
            continue

        if dim_a == dim_b == (512, 512):
            verified_pairs += 1

    print("\n--------------------------------------------------")
    print("VALIDATION SUMMARY:")
    print(f"Total pairs expected:   {total_expected}")
    print(f"Complete pairs verified: {verified_pairs} / {total_expected}")
    print(f"Missing images:         {len(missing)}")
    print(f"Corrupt images:         {len(corrupted)}")
    print(f"Dimension mismatches:   {len(dimension_mismatches)}")
    print("--------------------------------------------------")

    if verified_pairs == total_expected and len(missing) == 0 and len(corrupted) == 0:
        print("ALL 2,968 CDVQA BI-TEMPORAL PAIRS ARE 100% VALID!")
        print("STATUS: CDVQA READY (Exit 0)")
        sys.exit(0)
    else:
        print("VALIDATION FAILED (Exit 1)")
        sys.exit(1)

if __name__ == "__main__":
    validate()
