from bs4 import BeautifulSoup
from typing import Optional
from .figure import Figure
from .idno import IDNO, IDNOType
from .section import Section


class TEIDocument:
    def __init__(self, path: str):
        with open(path) as f:
            self.soup = BeautifulSoup(f, "lxml-xml")

    @property
    def abstract(self) -> str:
        return self.soup.abstract.text.strip()

    @property
    def authors(self) -> list[str]:
        def full_name(author):
            pers_name = author.persName
            return f"{pers_name.forename.text} {pers_name.surname.text}"

        authors = self.soup.sourceDesc.find_all("author")
        return [full_name(author) for author in authors if author.persName is not None]

    @property
    def keywords(self) -> Optional[list[str]]:
        keywords = self.soup.keywords
        if keywords:
            terms = keywords.find_all("term")
            return [term.text for term in terms]

    @property
    def idno(self) -> Optional[IDNO]:
        idno = self.soup.sourceDesc.idno
        if idno:
            return IDNO(IDNOType(idno.get("type")), idno.text)

    @property
    def sections(self) -> list[Section]:
        def map_section(div):
            title = div.head and div.head.text
            text = " ".join([p.text for p in div.find_all("p")])
            return Section(title, text)

        divs = self.soup.body.find_all("div")
        return [map_section(div) for div in divs]

    @property
    def title(self) -> Optional[str]:
        title = self.soup.titleStmt.title
        if title:
            return title.text

    @property
    def figures(self) -> list[Figure]:
        def map_figure(figure):
            title = figure.head and figure.head.text
            label = figure.label and figure.label.text
            description = figure.figDesc and figure.figDesc.text
            return Figure(title, label, description)

        figures = self.soup.body.find_all("figure")
        return [map_figure(figure) for figure in figures]
