import time
from urllib.request import urlopen, Request

from bs4 import BeautifulSoup


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