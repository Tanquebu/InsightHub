from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "InsightHub"
    env: str = "local"
    log_level: str = "INFO"

    database_url: str  # es: postgresql+psycopg://insighthub:insighthub@db:5432/insighthub

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
