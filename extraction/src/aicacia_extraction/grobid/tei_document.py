from bs4 import BeautifulSoup
from typing import Optional
from .idno import IDNO, IDNOType


class TEIDocument:
    def __init__(self, path: str):
        with open(path) as f:
            self.soup = BeautifulSoup(f, "lxml-xml")

    @property
    def abstract(self) -> list[str]:
        paragraphs = self.soup.abstract.find_all("p")
        return [paragraph.text for paragraph in paragraphs]

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
    def body(self):
        pass

    @property
    def title(self) -> Optional[str]:
        title = self.soup.titleStmt.title
        if title:
            return title.text
