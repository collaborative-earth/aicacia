from concurrent.futures import ThreadPoolExecutor
from itertools import repeat
import logging
from pathlib import Path
from typing import List
import fsspec

from core.app_config import configs

logger = logging.getLogger(__name__)


class FilesystemManager:
    def __init__(self, fs_protocol: str) -> None:  # Options: local | s3 | etc.
        # S3 uses .env keys (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY) if available.
        self.fs: fsspec.AbstractFileSystem = fsspec.filesystem(fs_protocol)

    def download_filepaths(self, filepaths: list[str], local_dir: str) -> list[str]:
        '''Download files from given filepaths to local directory.'''
        local_path = Path(local_dir)
        local_path.mkdir(parents=True, exist_ok=True)
        self.fs.get(filepaths, local_dir)
        return [str(local_path.joinpath(Path(s3_path).name)) for s3_path in filepaths]

    def upload_filepaths(self, local_filepaths: list[str], dest_dir: str) -> list[str]:
        '''Uploads local files to the destination directory.'''
        dest_paths = [
            self._get_dest_path(lfp, dest_dir) for lfp in local_filepaths
        ]
        self.fs.put(local_filepaths, dest_paths)
        return dest_paths

    def upload_filepath(self, local_filepath: str, dest_dir: str) -> str:
        '''Upload a single local file to the destination directory.'''
        dest_path = self._get_dest_path(local_filepath, dest_dir)
        self.fs.put_file(local_filepath, dest_path)
        return dest_path

    def _safe_upload_filepath(self, local_filepath: str, dest_dir: str):
        try:
            return self.upload_filepath(local_filepath, dest_dir)  # raises exception if upload fails
        except Exception as e:
            logger.error(
                f"Error uploading file: {local_filepath} to {dest_dir} - ({e})",
                exc_info=True
            )
            return None  # Indicate failure with None

    def _get_dest_path(self, local_filepath: str, dest_dir: str):
        '''Creates the dest_path by concatenating the dest_dir and the local_filepath'''
        return f"{dest_dir}/{Path(local_filepath).name}"

    def upload_filepaths_in_parallel(
        self, local_filepaths: list[str], dest_dir: str
    ) -> List[str | None]:
        '''Upload local files to the destination directory in parallel.
        Returns list of destination paths or None for failed uploads.
        Output order corresponds to input order.
        '''

        with ThreadPoolExecutor() as exec:
            results = exec.map(
                self._safe_upload_filepath, local_filepaths, repeat(dest_dir)
            )

        return list(results)


# protocol is None for local paths; using "file" as default
filesystem_protocol = fsspec.core.split_protocol(configs.S3_BUCKET)[0] or "file"
logger.info(f"Source filesystem protocol set to: {filesystem_protocol}")

fs_manager = FilesystemManager(filesystem_protocol)
