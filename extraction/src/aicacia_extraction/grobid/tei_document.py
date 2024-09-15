from bs4 import BeautifulSoup
from .idno import IDNO, IDNOType


class TEIDocument:
    authors: list[str]
    title: str

    def __init__(self, path: str):
        with open(path) as f:
            self.soup = BeautifulSoup(f, "lxml-xml")

    @property
    def authors(self) -> list[str]:
        def full_name(author):
            pers_name = author.persName
            return f"{pers_name.forename.text} {pers_name.surname.text}"

        source_desc = self.soup.find("sourceDesc")
        authors = source_desc.find_all("author")
        return [full_name(author) for author in authors if author.persName is not None]

    @property
    def idno(self) -> IDNO:
        source_desc = self.soup.find("sourceDesc")
        idno = source_desc.find("idno")
        return IDNO(IDNOType(idno.get("type")), idno.text)

    @property
    def title(self) -> str:
        title_stmt = self.soup.find("titleStmt")
        return title_stmt.title.text
