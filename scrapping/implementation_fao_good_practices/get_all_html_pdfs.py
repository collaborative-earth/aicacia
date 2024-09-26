import csv
import dataclasses
import re
from typing import Optional

import requests
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright


@dataclasses.dataclass
class GoodPractice:
    title: str
    description: str
    url: str
    domain: str


@dataclasses.dataclass
class LifeGoProFor:
    title: str
    description: str
    url: str
    domain: str
    pdf_url: Optional[str] = None


def sanitize_filename(filename):
    return re.sub(r'[\/:*?"<>|]', "_", filename)


def handle_panorama_solutions(url, filename):
    html = requests.get(url)
    with open(f"temp/panorama_solutions/{filename}.html", "w") as f:
        f.write(html.text)


def handle_qcat_wocat_net(url, filename):
    html = requests.get(url)
    with open(f"temp/qcat_wocat/html/{filename}.html", "w") as f:
        f.write(html.text)

    soup = BeautifulSoup(html.content, "html.parser")

    ul_tag = soup.find("ul", id="tech-details-print")

    if ul_tag is None:
        print(f"Could not find ul tag in {url}")
        return

    first_a_tag = ul_tag.find("a")
    if first_a_tag is None:
        print(f"Could not find a tag in {url}")
        return

    pdf_url = first_a_tag["href"]
    pdf_url = f"https://qcat.wocat.net{pdf_url}"
    pdf = requests.get(pdf_url)

    with open(f"temp/qcat_wocat/pdf/{filename}.pdf", "wb") as f:
        f.write(pdf.content)


def handle_lifegoprofor_gp_eu(url, filename):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        page.goto(url)

        page.wait_for_load_state("networkidle")

        html = page.content()

        with open(f"temp/lifegopro/{filename}.html", "w") as f:
            f.write(html)


# TODO Take path as argument
with open("temp/good_practices_list.csv", newline="") as csvfile:
    good_practices = csv.reader(csvfile, delimiter=",", quotechar="|")
    gp_filegoprofors = []
    for i, good_practice in enumerate(good_practices):
        if i == 0:
            continue
        gp = GoodPractice(
            title=good_practice[0],
            description=good_practice[1],
            url=good_practice[-2],
            domain=good_practice[-1],
        )

        domain = gp.domain
        if domain not in ["www.lifegoprofor-gp.eu"]:
            continue

        print(f"Downloading {i}, {gp.url}")

        filename = sanitize_filename(f"{i}_{gp.title}")

        if domain == "ferm-search.fao.org":
            print(f"Invalid link {gp.url}")

        elif domain == "panorama.solutions":
            handle_panorama_solutions(gp.url, filename)

        elif domain == "qcat.wocat.net":
            handle_qcat_wocat_net(gp.url, filename)

        elif domain == "www.lifegoprofor-gp.eu":
            handle_lifegoprofor_gp_eu(gp.url, filename)
        else:
            raise ValueError(f"Unknown domain {domain}")
