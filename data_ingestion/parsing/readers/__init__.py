from llama_index.core import download_loader
from llama_index.core.readers.base import BaseReader

# Download the UnstructuredReader
UnstructuredReader = download_loader("UnstructuredReader")
# TODO: Move to config file
readers_registry: dict[str, BaseReader] = {
        ".pdf": UnstructuredReader()
    }
