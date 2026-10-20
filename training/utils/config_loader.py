import yaml
from pathlib import Path
from pydantic import BaseModel, Field

class TrainingConfig(BaseModel):
    model_name: str
    dataset: str
    seed: int = 42
    batch_size: int = 8
    epochs: int = 10
    learning_rate: float = 1e-4
    mixed_precision: str = "fp16"
    
    # Additional raw dictionary to hold extra parameters (e.g. peft, bit_args)
    extra_params: dict = Field(default_factory=dict)

def load_config(config_path: str | Path) -> TrainingConfig:
    """Load and validate training configuration."""
    with open(config_path, "r") as f:
        data = yaml.safe_load(f)
        
    # Extract known keys
    known_keys = TrainingConfig.model_fields.keys()
    known_data = {k: v for k, v in data.items() if k in known_keys}
    extra_data = {k: v for k, v in data.items() if k not in known_keys}
    
    known_data["extra_params"] = extra_data
    return TrainingConfig(**known_data)
