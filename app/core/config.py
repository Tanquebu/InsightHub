from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "InsightHub"
    env: str = "local"
    log_level: str = "INFO"

    database_url: (
        str  # es: postgresql+psycopg://insighthub:insighthub@db:5432/insighthub
    )

    celery_broker_url: str = "redis://redis:6379/0"
    celery_result_backend: str = "redis://redis:6379/1"
    celery_task_always_eager: bool = False
    ingestion_max_retries: int = 3
    ingestion_retry_delay_seconds: int = 5

    # Milestone 4 — Insight Engine: quality-rule thresholds (fractions, 0.0-1.0).
    quality_missing_warning_threshold: float = 0.2
    quality_missing_critical_threshold: float = 0.5
    quality_min_completeness_score: float = 0.7

    # Milestone 5 — Hardening: auth (JWT) and rate limiting.
    jwt_secret_key: str  # es: stringa casuale lunga, letta da .env
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    redis_url: str = "redis://redis:6379/2"
    rate_limit_per_minute: int = 60

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


# database_url/jwt_secret_key have no Python-level default because they're required
# to come from the environment/.env — mypy can't see pydantic-settings' env loading,
# so it flags them as missing constructor args. See pydantic-settings docs.
settings = Settings()  # type: ignore[call-arg]
