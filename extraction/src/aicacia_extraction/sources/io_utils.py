import time
import typing
import json
from urllib.request import urlopen, Request
from bs4 import BeautifulSoup
from pathlib import Path


def read_html(url) -> BeautifulSoup | None:
    for attempt in range(3):
        time.sleep(attempt ** 2)
        try:
            with urlopen(Request(url, headers={'User-Agent': "Magic Browser"})) as resp:
                text = resp.read().decode("utf8")
                return BeautifulSoup(text, 'html.parser')
        except Exception as e:
            print(f"Request failed: attempt={attempt}, ex={e}")

    print("Max retries reached, returning None!")
    return None


def read_local_xml(path) -> BeautifulSoup:
    text = Path(path).read_text(encoding="utf8")
    return BeautifulSoup(text, 'xml')


def read_json(url) -> typing.Any:
    with urlopen(Request(url)) as resp:
        return json.loads(resp.read().decode("utf8"))
