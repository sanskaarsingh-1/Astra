"""
Astra AI Backend — Configuration
All configuration is loaded from environment variables (.env file).
Never hardcode secrets.
"""

import os
import sys
from pathlib import Path
from pydantic_settings import BaseSettings

# Ensure repository root is in sys.path
_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))


class Settings(BaseSettings):
    # ─── API Keys ───────────────────────────────────────────────────────────
    GEMINI_API_KEY: str = ""
    API_KEY: str = ""

    # ─── Server ─────────────────────────────────────────────────────────────
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = False

    # ─── CORS ───────────────────────────────────────────────────────────────
    # Comma-separated list of allowed origins
    ALLOWED_ORIGINS: str = (
        "https://sih-orbilens-2026-tm.web.app,"
        "http://localhost:3000,"
        "http://localhost:3001"
    )

    @property
    def allowed_origins_list(self) -> list[str]:
        return [o.strip() for o in self.ALLOWED_ORIGINS.split(",") if o.strip()]

    # ─── File Upload ─────────────────────────────────────────────────────────
    MAX_FILE_SIZE_MB: int = 200
    MAX_FILES_PER_REQUEST: int = 2
    UPLOAD_DIR: Path = Path("./uploads")
    OUTPUT_DIR: Path = Path("./outputs")

    @property
    def max_file_size_bytes(self) -> int:
        return self.MAX_FILE_SIZE_MB * 1024 * 1024

    # ─── Model Paths ─────────────────────────────────────────────────────────
    MODEL_CACHE_DIR: Path = Path("./models")
    GEOCHAT_MODEL_ID: str = "MBZUAI/geochat-7B"
    BEN_CLASSIFIER_PATH: Path = Path("./models/ben_classifier.pth")

    # ─── Model Loading ────────────────────────────────────────────────────────
    # Use INT4 quantization to fit in consumer GPU VRAM
    USE_INT4_QUANTIZATION: bool = True
    # Maximum VRAM to use before triggering model unload (in GB)
    MAX_VRAM_GB: float = 10.0

    # ─── Gemini ───────────────────────────────────────────────────────────────
    GEMINI_MODEL: str = "gemini-2.0-flash"
    GEMINI_TEMPERATURE: float = 0.1  # Low temperature for planning; higher for synthesis
    GEMINI_MAX_OUTPUT_TOKENS: int = 4096

    # ─── Pipeline ─────────────────────────────────────────────────────────────
    MAX_PLAN_STEPS: int = 5
    STEP_TIMEOUT_SECONDS: int = 90
    MAX_RETRIES_PER_STEP: int = 1
    RATE_LIMIT_REQUESTS_PER_MINUTE: int = 6

    # ─── Confidence Thresholds ────────────────────────────────────────────────
    HIGH_CONFIDENCE_THRESHOLD: float = 0.75
    LOW_CONFIDENCE_THRESHOLD: float = 0.40

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# Singleton settings instance
settings = Settings()

# Ensure required directories exist
settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
settings.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
settings.MODEL_CACHE_DIR.mkdir(parents=True, exist_ok=True)
