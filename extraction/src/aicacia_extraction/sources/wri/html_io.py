from urllib.request import urlopen, Request
from bs4 import BeautifulSoup
from pathlib import Path


def read_html(url) -> BeautifulSoup:
    with urlopen(Request(url, headers={'User-Agent': "Magic Browser"})) as resp:
        text = resp.read().decode("utf8")
        return BeautifulSoup(text, 'html.parser')


def read_xml(path) -> BeautifulSoup:
    text = Path(path).read_text(encoding="utf8")
    return BeautifulSoup(text, 'xml')
