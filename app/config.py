from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "mistral"
    # если true — без Ollama, заглушки для разработки
    mock_llm: bool = False
    vision_model_path: str = "D:/recipiesAI/food-detection.onnx"
    vision_labels_path: str | None = "D:/recipiesAI/labels.txt"
    vision_input_size: int = 640
    vision_conf_threshold: float = 0.25
    vision_iou_threshold: float = 0.45


@lru_cache
def get_settings() -> Settings:
    return Settings()
