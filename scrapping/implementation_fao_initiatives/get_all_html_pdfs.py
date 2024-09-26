import csv
import dataclasses
import re

import requests
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright


@dataclasses.dataclass
class Intiative:
    title: str
    description: str
    url: str
    domain: str


def sanitize_filename(filename):
    return re.sub(r'[\/:*?"<>|]', "_", filename)


def handle_ferm_fao_org(url, filename):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        page.goto(url)

        page.wait_for_load_state("networkidle")

        html = page.content()

        with open(f"temp/ferm_fao_org/{filename}.html", "w") as f:
            f.write(html)


def handle_nature_commitments(url, filename):
    html = requests.get(url)

    with open(f"temp/nature_commitments/html/{filename}.html", "w") as f:
        f.write(html.text)

    soup = BeautifulSoup(html.text, "html.parser")

    div_with_pdf_link = soup.find("div", class_="list--targets-additional")

    if div_with_pdf_link is None:
        print("Could not find div with PDF link")
        return

    pdf_link_tag = div_with_pdf_link.find("a")

    print(f"PDF link tag: {pdf_link_tag}")

    if pdf_link_tag and "href" in pdf_link_tag.attrs:
        # Extract the href attribute (PDF URL)
        pdf_url = pdf_link_tag["href"]

        # Handle relative URL by combining with the base URL
        full_pdf_url = f"https://www.naturecommitments.org{pdf_url}"

        print(f"Downloading PDF from: {full_pdf_url}")

        # Download the PDF
        pdf_response = requests.get(full_pdf_url)

        # Save the PDF to a file
        with open(f"temp/nature_commitments/pdf/{filename}.pdf", "wb") as f:
            f.write(pdf_response.content)
        print("PDF downloaded successfully")
    else:
        print("No PDF link found")


# TODO Take path as argument
with open("temp/foa_initiatives_list.csv", newline="") as csvfile:
    initiatives = csv.reader(csvfile, delimiter=",", quotechar="|")
    for i, initiative in enumerate(initiatives):
        if i == 0:
            continue
        gp = Intiative(
            title=initiative[0],
            description=initiative[1],
            url=initiative[-2],
            domain=initiative[-1],
        )

        domain = gp.domain
        if domain not in ["www.naturecommitments.org"]:
            continue

        print(f"Downloading {i}, {gp.url}")

        filename = sanitize_filename(f"{i}_{gp.title}")

        if domain == "ferm.fao.org":
            handle_ferm_fao_org(gp.url, filename)

        elif domain == "www.naturecommitments.org":
            handle_nature_commitments(gp.url, filename)
        else:
            raise ValueError(f"Unknown domain {domain}")
