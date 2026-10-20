import argparse
from loguru import logger
from training.utils.config_loader import load_config
from training.utils.gpu import check_gpu_available

def main():
    parser = argparse.ArgumentParser(description="Unified Training Entry Point for Astra AI")
    parser.add_argument("--model", type=str, required=True, choices=["geochat", "change_detection", "multimodal"], help="Which model to train")
    parser.add_argument("--config", type=str, required=True, help="Path to YAML configuration file")
    args = parser.parse_args()

    logger.info(f"Starting training run for model: {args.model}")
    
    # 1. Validate Config
    try:
        config = load_config(args.config)
        logger.info(f"Loaded config: {args.config}")
    except Exception as e:
        logger.error(f"Failed to load config: {e}")
        return

    # 2. Validate GPU
    if not check_gpu_available():
        return

    # 3. Route to Pipeline
    if args.model == "geochat":
        from training.pipelines.geochat_pipeline import GeoChatPipeline
        pipeline = GeoChatPipeline(config)
    elif args.model == "change_detection":
        from training.pipelines.change_detection_pipeline import ChangeDetectionPipeline
        pipeline = ChangeDetectionPipeline(config)
    elif args.model == "multimodal":
        from training.pipelines.multimodal_pipeline import MultimodalPipeline
        pipeline = MultimodalPipeline(config)
    else:
        logger.error(f"Unknown model: {args.model}")
        return

    # 4. Execute Pipeline
    try:
        pipeline.run()
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")

if __name__ == "__main__":
    main()
