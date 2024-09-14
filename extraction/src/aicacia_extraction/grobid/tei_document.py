from bs4 import BeautifulSoup


class TEIDocument:
    authors: list[str]
    title: str

    def __init__(self, path: str):
        with open(path) as f:
            self.soup = BeautifulSoup(f, "lxml-xml")

    @property
    def authors(self) -> list[str]:
        title_stmt = self.soup.find("titleStmt")
        return title_stmt.title.text

    @property
    def title(self) -> str:
        title_stmt = self.soup.find("titleStmt")
        return title_stmt.title.text
