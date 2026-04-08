"""pydantic-settings 기반 환경 설정."""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # Database
    database_url: str = "postgresql://edupulse:edupulse@localhost:5432/edupulse"

    # External API
    naver_client_id: str = ""
    naver_client_secret: str = ""

    # Server
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    # Model
    model_dir: str = "edupulse/model/saved"

    # Collection
    naver_daily_quota: int = 1000
    search_trends_output: str = "edupulse/data/raw/external/search_trends.csv"
    cache_dir: str = "edupulse/data/raw/external/cache"
    cache_staleness_weeks: int = 4


settings = Settings()
