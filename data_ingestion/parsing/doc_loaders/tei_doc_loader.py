from typing import List, Dict, Any

from data_ingestion.parsing.doc_loaders import DocumentLoader
from data_ingestion.types.tei_document import TEIDocument


class TEIDocumentLoader(DocumentLoader):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

        self.tei_object: TEIDocument = TEIDocument(content=self.content)

    def get_textual_repr(self) -> str:
        # Reference: Taken from _build_combined_text from grobid_reader.py
        parts: List[str] = []
        if self.tei_object.title:
            parts.append(f"Title: {self.tei_object.title}\n")
        if self.tei_object.authors:
            parts.append(f"Authors: {', '.join(self.tei_object.authors)}\n")
        if self.tei_object.doi:
            parts.append(f"DOI: {self.tei_object.doi}\n")
        if self.tei_object.keywords:
            parts.append(f"Keywords: {', '.join(self.tei_object.keywords)}\n")

        # abstract
        try:
            if self.tei_object.abstract:
                parts.append("Abstract:\n" + self.tei_object.abstract + "\n")
        except Exception:
            # some TEI documents may not have abstract
            pass

        # sections
        sections = self.tei_object.sections
        if sections:
            for sec in sections:
                title = sec.title or ""
                text = sec.text or ""
                if title:
                    parts.append(f"Section: {title}\n")
                parts.append(text + "\n")

        return "\n".join(parts).strip()

    def get_metadata(self) -> dict:
        md: Dict[str, Any] = {}
        if self.tei_object.title:
            md["title"] = self.tei_object.title
        if self.tei_object.authors:
            md["authors"] = self.tei_object.authors
        if self.tei_object.doi:
            md["doi"] = self.tei_object.doi
        if self.tei_object.keywords:
            md["keywords"] = self.tei_object.keywords
        return md
