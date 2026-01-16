"""Application configuration module for loading environment variables."""

import logging
import os
from pathlib import Path

from dotenv import load_dotenv


logger = logging.getLogger(__name__)


# Determine project root directory
# Load .env file from project root
# Find project root by going up from this file's location
def _get_project_root(project_name: str) -> Path:
    # Find the project root by looking for pyproject.toml and matching folder name
    current_dir = Path(__file__).parent
    for parent in [current_dir, *current_dir.parents]:
        if (parent / "pyproject.toml").exists() and parent.name.lower() == project_name.lower():
            return parent
    return current_dir


def _get_env_path(project_root: Path) -> Path | None:
    env_path = project_root / ".env"
    if env_path.exists():
        return env_path

    logger.warning(".env file not found in project hierarchy.")
    return None


aicacia_project_root = _get_project_root("aicacia")
dotenv_path = _get_env_path(aicacia_project_root)
load_dotenv(dotenv_path=dotenv_path)


# TODO: Use pydantic for settings management
class AppConfig:
    """Centralized configuration class for accessing environment variables."""

    CWD = Path(os.getcwd())

    # Configure logging
    logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
    logging.getLogger('sqlalchemy').setLevel(logging.WARNING)

    APP_NAME: str = os.getenv("APP_NAME", "aicacia")

    # Database configuration
    DB_HOST: str = os.getenv("DB_HOST", "localhost")
    DB_PORT: str = os.getenv("DB_PORT", "5432")
    DB_USER: str = os.getenv("DB_USER", "postgres")
    DB_NAME: str = os.getenv("DB_NAME", "aicacia_db")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "")

    # Filesystem configuration
    S3_BUCKET: str = os.getenv("S3_BUCKET", "data/parsed_outputs")
    TMP_LOCAL_DIR: str | None = os.getenv("TMP_LOCAL_DIR", None)
    if TMP_LOCAL_DIR:
        if TMP_LOCAL_DIR.startswith('./') or TMP_LOCAL_DIR.startswith('../'):
            TMP_LOCAL_DIR = str(CWD.joinpath(TMP_LOCAL_DIR).resolve())  # if relative force CWD
        logger.info(f"Temporary local directory set to: {TMP_LOCAL_DIR}")

    # Grobid
    GROBID_URL: str = os.getenv("GROBID_URL", "http://localhost:8070")
    # GROBID_CONFIG_FILE: str = os.path.join(CWD, os.getenv("GROBID_CONFIG_FILE", "grobid.yaml"))

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
            f"postgresql://{cls.DB_USER}:{cls.DB_PASSWORD}"
            f"@{cls.DB_HOST}:{cls.DB_PORT}/{cls.DB_NAME}"
        )


# singleton instance for easy access
configs = AppConfig()
