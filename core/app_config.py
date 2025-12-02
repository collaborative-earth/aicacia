"""Application configuration module for loading environment variables."""

import os
from pathlib import Path


class AppConfig:
    """Centralized configuration class for accessing environment variables."""

    CWD = Path(os.getcwd())

    # Database configuration
    POSTGRES_HOST: str = os.getenv("POSTGRES_HOST", "localhost")
    POSTGRES_PORT: str = os.getenv("POSTGRES_PORT", "5432")
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "postgres")
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "aicacia_db")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "aicacia")

    # Filesystem configuration
    SOURCE_FILESYSTEM: str = os.getenv("SOURCE_FILESYSTEM", "s3")    # Options: local | s3 | etc.
    TMP_LOCAL_FOLDER: str = os.path.join(CWD, os.getenv("TMP_LOCAL_FOLDER", "data/tmp"))
    PARSED_OUTPUTS_FOLDER: str = os.getenv("PARSED_OUTPUTS_FOLDER", "data/parsed_outputs")
    # Grobid
    GROBID_URL: str = os.getenv("GROBID_URL", "http://localhost:8070")
    GROBID_CONFIG_FILE: str = os.path.join(CWD, os.getenv("GROBID_CONFIG_FILE", "grobid.yaml"))

    # API keys
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    SECRET_KEY: str = os.getenv("SECRET_KEY", "")

    # Qdrant configuration
    QDRANT_URL: str = os.getenv("QDRANT_URL", "localhost:6333")
    QDRANT_API_KEY: str = os.getenv("QDRANT_API_KEY", "")
    QDRANT_COLLECTION: str = os.getenv("QDRANT_COLLECTION", "aicacia")

    # Model configuration
    # TODO: separate configs into proper .env and config.yml depending on usage.
    EMBEDDING_MODEL_NAME: str = os.getenv("EMBEDDING_MODEL_NAME", "BAAI/bge-m3")

    @classmethod
    def get_database_url(cls) -> str:
        """Construct PostgreSQL database URL."""
        return (
            f"postgresql://{cls.POSTGRES_USER}:{cls.POSTGRES_PASSWORD}"
            f"@{cls.POSTGRES_HOST}:{cls.POSTGRES_PORT}/{cls.POSTGRES_DB}"
        )

    # def _load_config(file_path: str):
    #     with open(file_path, 'r') as file:
    #         return yaml.safe_load(file)


# TODO: Instance not needed
# Create a singleton instance for easy access
configs = AppConfig()
