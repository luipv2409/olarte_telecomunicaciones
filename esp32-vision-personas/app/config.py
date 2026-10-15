from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator
from typing import Optional


class Settings(BaseSettings):
    """
    Configuración de la aplicación cargada desde variables de entorno o archivo .env
    """
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    APP_BIND_IP: str = Field(
        default="127.0.0.1",
        description="IP a la que se vinculará la aplicación (127.0.0.1 para PC local, o IP LAN)"
    )
    APP_HOST_PORT: int = Field(
        default=8088,
        description="Puerto host configurado para la aplicación"
    )

    ESP32_BASE_URL: str = Field(
        default="",
        description="URL base HTTP del ESP32-S3 (ejemplo: http://192.168.1.150)"
    )

    CAPTURE_INTERVAL_SECONDS: float = Field(
        default=2.0,
        ge=0.5,
        le=60.0,
        description="Frecuencia de captura en segundos"
    )

    DETECTION_CONFIDENCE: float = Field(
        default=0.45,
        ge=0.05,
        le=0.99,
        description="Umbral de confianza mínimo para detección de personas"
    )

    DEEPSEEK_API_KEY: Optional[str] = Field(
        default=None,
        description="Clave de API de DeepSeek para análisis visual opcional"
    )

    DEEPSEEK_MODEL: str = Field(
        default="deepseek-flash",
        description="Nombre del modelo multimodal en la API de DeepSeek"
    )

    DEEPSEEK_VISION_ENABLED: bool = Field(
        default=False,
        description="Bandera para habilitar o deshabilitar consultas a DeepSeek Vision"
    )

    YOLO_MODEL_NAME: str = Field(
        default="yolov8n.pt",
        description="Modelo de YOLO ligero a utilizar en CPU"
    )

    @field_validator("ESP32_BASE_URL")
    @classmethod
    def clean_esp32_url(cls, v: str) -> str:
        if not v:
            return ""
        v = v.strip()
        if not (v.startswith("http://") or v.startswith("https://")):
            v = f"http://{v}"
        return v.rstrip("/")


settings = Settings()
