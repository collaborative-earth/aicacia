from dataclasses import dataclass
from enum import Enum
from typing import Optional


# https://github.com/kermitt2/grobid/blob/master/grobid-core/src/main/java/org/grobid/core/document/TEIFormatter.java
class IDNOType(Enum):
    ark = "ark"
    arXiv = "arXiv"
    DOI = "DOI"
    eISSN = "eISSN"
    halId = "halId"
    ISBN = "ISBN"
    ISSN = "ISSN"
    istexId = "istexId"
    MD5 = "MD5"
    PII = "PII"
    PMCID = "PMCID"
    PMID = "PMID"
    URI = "URI"


@dataclass
class IDNO:
    type: Optional[IDNOType]
    value: str
