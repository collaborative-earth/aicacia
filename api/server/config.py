from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    POSTGRES_HOST: str = "aicacia-postgres"
    POSTGRES_PORT: str = "5432"
    POSTGRES_USER: str = "postgres"
    POSTGRES_DB: str = "aicacia_db"
    POSTGRES_PASSWORD: str
    OPENAI_API_KEY: str
    SECRET_KEY: str = "aicacia_secret_key"

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()
