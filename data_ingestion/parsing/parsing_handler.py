from typing import Optional, Sequence

from core.app_config import configs
from core.db_manager import db_manager
from data_ingestion.parsing.parsers.grobid_parser import GrobidParser
from data_ingestion.parsing.parsers.abstract_parser import AbstractParser, DocumentLoader
from core.fs_manager import fs_manager


class ParsingHandler():
    def __init__(self, default_parser: AbstractParser) -> None:
        # assert fs is not None, "A filesystem instance must be provided."

        self.default_parser: AbstractParser = default_parser

    def parse_filepaths(self, filepaths: list[str]) -> Sequence[DocumentLoader]:
        '''Parse files from given filepaths using the default parser.'''
        local_folder: str = configs.TMP_LOCAL_FOLDER
        downloaded_filepaths: list[str] = fs_manager.download_filepaths(filepaths, local_folder)
        parsed_files: Sequence[DocumentLoader] = self.default_parser.parse_files(downloaded_filepaths)

        print(
            f"Parsed {len(parsed_files)} out of {len(filepaths)} successfully."
        )

        return parsed_files

    def parse_and_upload(self, filepaths: list[str], dest_dir: str) -> list[str]:
        '''Parse files from given filepaths and upload parsed results to destination directory.'''

        parsed_files: Sequence[DocumentLoader] = self.parse_filepaths(filepaths)

        uploaded_filepaths: list[str] = []
        if parsed_files:
            uploaded_filepaths = fs_manager.upload_filepaths(
                local_filepaths=[parsed_file.filepath for parsed_file in parsed_files],
                dest_dir=dest_dir
            )

        return uploaded_filepaths


#  TODO: REMOVE this section after testing
if __name__ == "__main__":
    print("In ParsingHandler main!")

    # Configure parameters
    default_parser = GrobidParser(host_url=configs.GROBID_URL)
    local_folder: str = configs.TMP_LOCAL_FOLDER
    dest_dir: str = configs.PARSED_OUTPUTS_FOLDER

    parsing_handler = ParsingHandler(default_parser=default_parser)

    filepaths = db_manager.get_ready_to_parse_files()
    # --- for parsing without uploading
    # parsed_files = parsing_handler.parse_filepaths(filepaths)

    # if parsed_files:
    #     fs_manager.upload_filepaths(
    #         local_filepaths=[parsed_file.filepath for parsed_file in parsed_files],
    #         dest_dir=dest_dir
    #     )
    # ---

    # --- for parsing with uploading
    # uploaded_paths = parsing_handler.parse_and_upload(filepaths, dest_dir=dest_dir) 

    # for uploaded_path in uploaded_paths:
    #     print(uploaded_path)
    # ---






