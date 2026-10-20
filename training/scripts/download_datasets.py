import argparse
import json
import os
from pathlib import Path
from loguru import logger

MANIFESTS_DIR = Path("training/datasets/manifests")

def get_manifest(dataset_name: str):
    manifest_path = MANIFESTS_DIR / f"{dataset_name}.json"
    if not manifest_path.exists():
        logger.error(f"Manifest not found for dataset: {dataset_name}")
        return None
    with open(manifest_path, "r") as f:
        return json.load(f)

def main():
    parser = argparse.ArgumentParser(description="Astra AI Dataset Downloader")
    parser.add_argument("--dataset", type=str, required=True, help="Dataset to download (e.g. vrsbench, levir_cd)")
    args = parser.parse_args()

    manifest = get_manifest(args.dataset)
    if not manifest:
        return

    logger.info(f"Dataset: {manifest['name']}")
    logger.info(f"Description: {manifest['description']}")
    logger.info(f"Source: {manifest['source_url']}")
    logger.info(f"License: {manifest['license']}")
    logger.info(f"Approximate Size: {manifest['approx_size_gb']} GB")

    confirmation = input("Do you want to proceed with downloading? (y/n): ")
    if confirmation.lower() != 'y':
        logger.info("Download cancelled.")
        return

    dest_dir = Path(f"training/datasets/raw/{args.dataset}")
    dest_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Downloading {args.dataset} to {dest_dir} ... (Placeholder)")
    # Logic to download based on source (e.g., wget, huggingface-cli, curl)
    logger.success(f"Finished downloading {args.dataset}.")

if __name__ == "__main__":
    main()
