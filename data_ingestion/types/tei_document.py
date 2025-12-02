# Reference: Taken from grobid_reader.py
from bs4 import BeautifulSoup
from functools import cached_property
from typing import Optional, TextIO

from dataclasses import dataclass
from enum import Enum


@dataclass
class Section:
    title: Optional[str]
    text: Optional[str]


# https://github.com/kermitt2/grobid/blob/master/grobid-core/src/main/java/org/grobid/core/document/TEIFormatter.java
class IDNOType(Enum):
    ARK = "ark"
    ARXIV = "arXiv"
    DOI = "DOI"
    EISSN = "eISSN"
    HALID = "halId"
    ISBN = "ISBN"
    ISSN = "ISSN"
    ISTEXID = "istexId"
    MD5 = "MD5"
    PII = "PII"
    PMCID = "PMCID"
    PMID = "PMID"
    URI = "URI"


@dataclass
class IDNO:
    type: Optional[IDNOType]
    value: str


@dataclass
class Figure:
    title: Optional[str]
    label: Optional[str]
    description: Optional[str]


class TEIDocument:
    def __init__(self, content: str):
        self.soup = BeautifulSoup(content, "lxml-xml")

    @cached_property
    def abstract(self) -> str:
        return self.soup.abstract.text.strip()

    @cached_property
    def authors(self) -> list[str]:
        def full_name(persname):
            if not persname:
                return

            names = [name.text for name in [persname.forename, persname.surname] if name is not None]
            return " ".join(names)

        authors = self.soup.sourceDesc.find_all("author")
        full_names = [full_name(author.persName) for author in authors]
        return [full_name for full_name in full_names if full_name]

    @cached_property
    def doi(self) -> Optional[str]:
        for idno in self.idnos:
            if idno.type == IDNOType.DOI:
                return idno.value

    @cached_property
    def keywords(self) -> Optional[list[str]]:
        keywords = self.soup.keywords
        if keywords:
            terms = keywords.find_all("term")
            return [term.text for term in terms]

    @cached_property
    def idnos(self) -> list[IDNO]:
        idnos = self.soup.sourceDesc.find_all("idno")
        return [IDNO(IDNOType(idno.get("type")), idno.text) for idno in idnos]

    @property
    def sections(self) -> list[Section]:
        def map_section(div):
            title = div.head and div.head.text
            text = " ".join([p.text for p in div.find_all("p")])
            return Section(title, text)

        divs = self.soup.body.find_all("div")
        return [map_section(div) for div in divs]

    @cached_property
    def title(self) -> Optional[str]:
        title = self.soup.titleStmt.title
        if title:
            return title.text

    @cached_property
    def figures(self) -> list[Figure]:
        def map_figure(figure):
            title = figure.head and figure.head.text
            label = figure.label and figure.label.text
            description = figure.figDesc and figure.figDesc.text
            return Figure(title, label, description)

        figures = self.soup.body.find_all("figure")
        return [map_figure(figure) for figure in figures]
