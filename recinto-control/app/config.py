from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    HOST_HTTP_PORT: int = Field(default=8089)
    HOST_BIND_IP: str = Field(default="127.0.0.1")

    POSTGRES_DB: str = Field(default="recinto_control_db")
    POSTGRES_USER: str = Field(default="recinto_admin")
    POSTGRES_PASSWORD: str = Field(default="recinto_secure_pass")
    POSTGRES_HOST: str = Field(default="postgres_db")
    POSTGRES_PORT: int = Field(default=5432)

    DEVICE_API_SECRET: str = Field(default="esp32_device_secret_token_seguro_fase1")
    ESP32_BASE_URL: str = Field(default="http://192.168.1.111")

    @property
    def database_url(self) -> str:
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"


settings = Settings()
