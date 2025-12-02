

from data_ingestion.parsing.doc_loaders.doc_loader import DocumentLoader


class RawDocumentLoader(DocumentLoader):
    '''A raw document loader that returns the file content as-is. No formatting'''
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

    def get_textual_repr(self) -> str:
        return self.content or ""
