from bs4 import BeautifulSoup
from functools import cached_property
from typing import Optional, TextIO
from .figure import Figure
from .idno import IDNO, IDNOType
from ..document.document import Document
from ..document.section import Section


class GROBIDDocument(Document):
    @cached_property
    def abstract(self) -> Optional[str]:
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

    @cached_property
    def figures(self) -> list[Figure]:
        def map_figure(figure):
            title = figure.head and figure.head.text
            label = figure.label and figure.label.text
            description = figure.figDesc and figure.figDesc.text
            return Figure(title, label, description)

        figures = self.soup.body.find_all("figure")
        return [map_figure(figure) for figure in figures]

    @cached_property
    def references(self) -> list[str]:
        # TODO: Implement references. list[str] may be too limiting for GROBID as it seems to parse author, title, etc.
        return []

    @cached_property
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

    def __init__(self, file: TextIO):
        self.soup = BeautifulSoup(file, "lxml-xml")

    @classmethod
    def from_path(cls, path: str):
        with open(path) as f:
            return cls(f)
