"""LlamaIndex file reader for GROBID TEI XML output.

This reader integrates with `llama_index`'s `SimpleDirectoryReader` file
extraction mechanism by implementing `load_data` / `aload_data` and
returning a list of `Document` objects.

Behavior:
- By default it will produce one `Document` per TEI section (if any),
  plus a document for the combined content. Metadata includes title,
  authors, doi, keywords, and any `extra_info` passed by the directory
  reader (e.g. file metadata).
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional
from pathlib import Path
import io

from llama_index.core.readers.base import BaseReader
from llama_index.core.schema import Document

from extraction.src.aicacia_extraction.grobid import TEIDocument


class GrobidReader(BaseReader):
    """Reader for GROBID TEI XML files.

    Args:
        split_sections: If True, return one Document per TEI <div> section in
            addition to a combined document. If False, return only the combined
            document.
    """

    def __init__(self, split_sections: bool = True) -> None:
        super().__init__()
        self.split_sections = split_sections

    def _build_combined_text(self, tei: TEIDocument) -> str:
        parts: List[str] = []
        if tei.title:
            parts.append(f"Title: {tei.title}\n")
        if tei.authors:
            parts.append(f"Authors: {', '.join(tei.authors)}\n")
        if tei.doi:
            parts.append(f"DOI: {tei.doi}\n")
        if tei.keywords:
            parts.append(f"Keywords: {', '.join(tei.keywords)}\n")

        # abstract
        try:
            if tei.abstract:
                parts.append("Abstract:\n" + tei.abstract + "\n")
        except Exception:
            # some TEI documents may not have abstract
            pass

        # sections
        sections = tei.sections
        if sections:
            for sec in sections:
                title = sec.title or ""
                text = sec.text or ""
                if title:
                    parts.append(f"Section: {title}\n")
                parts.append(text + "\n")

        return "\n".join(parts).strip()

    def _build_metadata(self, tei: TEIDocument, extra_info: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        md: Dict[str, Any] = {}
        if tei.title:
            md["title"] = tei.title
        if tei.authors:
            md["authors"] = tei.authors
        if tei.doi:
            md["doi"] = tei.doi
        if tei.keywords:
            md["keywords"] = tei.keywords
        if extra_info:
            # keep extra_info under its own key to avoid clobbering
            md["file_meta"] = extra_info
        return md

    def load_data(self, input_file: Path, extra_info: Optional[Dict[str, Any]] = None, fs: Optional[object] = None, **kwargs: Any) -> List[Document]:
        """Load a single TEI file and return list of Documents.

        This method matches the expectations of `SimpleDirectoryReader.load_file`.
        """
        # open file either using provided fs (fsspec) or local open
        if fs is None:
            with open(input_file, "r", encoding=kwargs.get("encoding", "utf-8")) as f:
                tei = TEIDocument(f)
        else:
            # fsspec file-like object: read string and wrap
            with fs.open(input_file) as f:
                data = f.read()
            tei = TEIDocument(io.StringIO(data))

        combined_text = self._build_combined_text(tei)
        metadata = self._build_metadata(tei, extra_info)

        # combined document
        document = Document(text=combined_text, metadata=metadata)

        return document
