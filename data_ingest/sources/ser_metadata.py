import time
import requests

from datetime import datetime
from playwright.sync_api import sync_playwright
from data_ingest.entities.Document import SourcedDocumentMetadata, SourceLink, DocumentSourceCorpus

BASE_URL = 'https://ser-rrc.org/restoration-database/'


def extract_ser_metadata(start_page=1, page_limit=-1):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(BASE_URL)
        page.wait_for_load_state("domcontentloaded")
        time.sleep(10)

        if page_limit < 0:
            last_page = -1
        else:
            last_page = start_page + page_limit - 1

        current_page = start_page

        while True:
            next_button = page.locator(f"span.pagebutton:has-text('{current_page}')").first

            if not next_button.is_visible():
                print("No more pages.")
                break
            else:
                print(f"Going to page #{current_page}")
                next_button.click()
                page.wait_for_load_state("domcontentloaded")
                time.sleep(30)

            page.wait_for_selector(".project")

            project_elements = page.query_selector_all(".project h3 a")

            project_links = [el.get_attribute("href") for el in project_elements]

            for project_link in project_links:
                response = requests.get(project_link)

                if response.status_code == 200:
                    json_data = response.json()["data"]
                    print(json_data["title"])

                yield SourcedDocumentMetadata(
                    title=json_data["title"],
                    source_corpus=DocumentSourceCorpus.SER,
                    sourced_at=datetime.now(),
                    source_links=[SourceLink(link=project_link, type="application/json")],
                    page_link=project_link,
                    abstract=json_data["details"]["description"],
                    geo_location=f'lat={json_data["details"]["lat"]},lng={json_data["details"]["lng"]}',
                    revision_date=json_data["published_at"],
                    other_metadata={
                        "language": json_data["language"]
                    }
                )

            if current_page == last_page:
                break

            current_page += 1

        browser.close()


extract_ser_metadata()
