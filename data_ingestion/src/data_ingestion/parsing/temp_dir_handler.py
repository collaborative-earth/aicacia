# needed by the parsers to manage temporary directories
import tempfile
from pathlib import Path
import logging

from core.app_config import configs


logger = logging.getLogger(__name__)


class TempDirectoryContext:
    def __init__(self, local_dir: str | None = None):
        self._tmp_obj = None
        self._path = None
        self._local_dir = local_dir

    @property
    def path(self) -> Path:
        """Create the temp dir on first access and return its path."""
        # lazy initialization
        if self._tmp_obj is None:
            logger.info(f"Initializing temporary directory in {self._local_dir}...")
            self._tmp_obj = tempfile.TemporaryDirectory(
                dir=self._local_dir if self._local_dir else None,  # None means: use default temp dir
            )
            self._path = Path(self._tmp_obj.name)
            logger.info(f"Temporary directory created at {self._path}")
        return self._path

    def teardown(self):
        """Call this only when the entire multi-step process is done."""

        if self._tmp_obj is None:
            logger.info("Temporary directory not initialized. Skipping cleanup.")
            return

        logger.info(f"Cleaning up temporary directory: {self.path}")
        self._tmp_obj.cleanup()  # Explicitly triggers deletion
        self._tmp_obj = None
        self._path = None


# Singleton instance to be used across the parsing workflow
# uses default temporary directory from app config (TMP_LOCAL_DIR)
tmp_dir_context = TempDirectoryContext(local_dir=configs.TMP_LOCAL_DIR)
