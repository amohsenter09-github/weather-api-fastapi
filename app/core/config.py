from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "weather-api-fastapi"
    log_level: str = "INFO"

    open_meteo_base_url: str = "https://api.open-meteo.com/v1"
    open_meteo_geocoding_base_url: str = "https://geocoding-api.open-meteo.com/v1"
    http_timeout_seconds: float = 10.0
    database_url: str = "postgresql+asyncpg://weather:weather@127.0.0.1:5434/weather"
    ui_theme: str = "orange"


UI_THEMES = frozenset({
    "blue",
    "green",
    "yellow",
    "orange",
    "red",
    "purple",
    "pink",
    "brown",
    "black",
    "white",
    "gray",
})


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
