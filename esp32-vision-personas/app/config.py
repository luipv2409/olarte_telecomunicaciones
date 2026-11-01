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

    CONTINUOUS_CAPTURE_ENABLED: bool = Field(
        default=False,
        description="Si es true, consulta la cámara periódicamente (consume ESP32). Por defecto solo se captura al activarse el IR"
    )

    BURST_FRAMES: int = Field(
        default=5,
        ge=1,
        le=10,
        description="Cantidad de fotos que se piden al ESP32 por activación del IR"
    )

    BURST_WINDOW_SECONDS: float = Field(
        default=1.0,
        ge=0.2,
        le=5.0,
        description="Ventana de tiempo en la que se reparten las fotos de la ráfaga"
    )

    BURST_COOLDOWN_SECONDS: float = Field(
        default=3.0,
        ge=0.0,
        le=60.0,
        description="Tiempo mínimo entre ráfagas para no sobrecargar el ESP32"
    )

    BURST_MIN_PERSON_FRAMES: int = Field(
        default=2,
        ge=1,
        le=10,
        description="Fotos de la ráfaga en las que debe aparecer una persona para confirmar PERSONA"
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
