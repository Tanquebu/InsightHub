from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "InsightHub"
    env: str = "local"
    log_level: str = "INFO"

    database_url: str  # es: postgresql+psycopg://insighthub:insighthub@db:5432/insighthub

    celery_broker_url: str = "redis://redis:6379/0"
    celery_result_backend: str = "redis://redis:6379/1"
    celery_task_always_eager: bool = False
    ingestion_max_retries: int = 3
    ingestion_retry_delay_seconds: int = 5

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
