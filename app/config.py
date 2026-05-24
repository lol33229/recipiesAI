from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict

_PROJECT_ROOT = Path(__file__).resolve().parents[1]
_ENV_FILE = _PROJECT_ROOT / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(_ENV_FILE) if _ENV_FILE.is_file() else None,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # LLM
    llm_provider: Literal["ollama", "mistral", "openrouter"] = "mistral"
    mock_llm: bool = False

    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "mistral"

    mistral_api_key: str | None = None
    mistral_model: str = "mistral-small-latest"
    mistral_base_url: str = "https://api.mistral.ai/v1"

    openrouter_api_key: str | None = None
    openrouter_model: str = "mistralai/mistral-small-3.1-24b-instruct"
    openrouter_base_url: str = "https://openrouter.ai/api/v1"

    llm_timeout_sec: float = 60.0

    main_api_base_url: str = "http://158.160.6.41"
    main_api_bearer_token: str | None = None
    main_api_timeout_sec: float = 30.0

    vision_model_path: str = "food-detection.onnx"
    vision_labels_path: str | None = "labels.txt"
    vision_input_size: int = 640
    vision_conf_threshold: float = 0.25
    vision_iou_threshold: float = 0.45


@lru_cache
def get_settings() -> Settings:
    return Settings()
