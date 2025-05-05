from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    POSTGRES_HOST: str = "aicacia-postgres"
    POSTGRES_PORT: str = "5432"
    POSTGRES_USER: str = "postgres"
    POSTGRES_DB: str = "aicacia_db"
    POSTGRES_PASSWORD: str = "aicacia"

    OPENAI_API_KEY: str = "Hello!"

    SECRET_KEY: str = "Hello!"

    QDRANT_URL: str = "localhost:6333"
    QDRANT_API_KEY: str = "Hello!"
    QDRANT_COLLECTION: str = "aicacia"

    EMBEDDING_MODEL_NAME: str = "BAAI/bge-m3"

    model_config = SettingsConfigDict()


settings = Settings()
