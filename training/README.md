# Astra AI — Training Layer

This directory handles dataset management, model fine-tuning, evaluation, and checkpoint generation. It is entirely decoupled from the production backend.

## Why Training Exists
We do **not** train foundation models from scratch. We use pretrained models (GeoChat, BIT) and selectively fine-tune/adapt specialist components where it provides measurable improvement.

The workflow is strictly:
`Pretrained Model` → `Baseline Evaluation` → `Domain Adaptation (Fine-tuning)` → `Held-out Evaluation` → `Compare against Baseline` → `Only Adopt if Better`.

## Models We Adapt
1. **Remote-Sensing VLM**: GeoChat (LoRA/QLoRA) for VQA, captioning, and scene understanding.
2. **Change Detection**: BIT (Bitemporal Image Transformer) for detecting changes between two optical images.
3. **Multimodal Experiments**: Fusion experiments using BigEarthNet / SEN12MS.

## Datasets
- **VQA / Captioning**: VRSBench, RSVQA
- **Change Detection**: LEVIR-CD, WHU-CD
- **Multimodal**: BigEarthNet v2, SEN12MS

## Quick Start

### 1. Download Datasets
Datasets are not included in the repository. Use the download manager:
```powershell
python scripts/download_datasets.py --dataset vrsbench
```
Downloaded data goes to `datasets/raw/`.

### 2. Prepare Datasets
```powershell
python scripts/prepare_dataset.py --dataset vrsbench
```
Preprocessed data goes to `datasets/processed/`.

### 3. Start Training
```powershell
python scripts/train.py --model geochat --config configs/geochat/default.yaml
```
Progress is reported in the terminal (overall progress, phase, epoch, batch, loss).

### 4. GPU Requirements
- LoRA/QLoRA tuning: ~8-12GB VRAM
- Full fine-tuning: 16GB+ VRAM
- If no compatible GPU is found, the script will halt with `GPU_UNAVAILABLE`.

### 5. Checkpoints & Evaluation
- Checkpoints are saved under `models/checkpoints/<model_name>/run_<timestamp>/`.
- For LoRA, adapters are saved under `models/adapters/`.
- Training automatically evaluates against a baseline. Compare results in `baseline_vs_finetuned.json`.

### 6. Export to Backend
If a model improves over the baseline, export it to the production backend:
```powershell
python scripts/export_checkpoint.py --run_id run_1234567890
```
This moves the checkpoint to `backend/models/` and registers its metadata.

## Known Limitations
- The training framework does not support distributed multi-GPU training currently.
- Fake multimodal fusion is not permitted. Any multimodal model must clearly document its capabilities.
