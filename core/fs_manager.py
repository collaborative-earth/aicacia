from pathlib import Path
import fsspec

from core.app_config import configs


class FilesystemManager:
    def __init__(self, filesystem: str) -> None:  # Options: local | s3 | etc.
        # S3 uses .env keys (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY) if available.
        self.fs = fsspec.filesystem(filesystem)

    def download_filepaths(self, filepaths: list[str], local_dir: str) -> list[str]:
        '''Download files from given filepaths to local directory.'''
        local_path = Path(local_dir)
        local_path.mkdir(parents=True, exist_ok=True)
        self.fs.get(filepaths, local_dir)
        return [str(local_path.joinpath(Path(s3_path).name)) for s3_path in filepaths]

    def upload_filepaths(self, local_filepaths: list[str], dest_dir: str) -> list[str]:
        '''Upload local files to the destination directory.'''
        dest_paths = [f"{dest_dir}/{Path(fp).name}" for fp in local_filepaths]
        self.fs.put(local_filepaths, dest_paths)
        return dest_paths


# TODO. Load filesystem config from env or config file
fs_manager = FilesystemManager(configs.SOURCE_FILESYSTEM)  # 's3' or 'local' for local filesystem
