import csv
import time

from playwright.sync_api import sync_playwright


def scrape_initiatives(good_practices: list[dict]):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        page.goto("https://ferm.fao.org/search/initiatives")

        page.wait_for_load_state("networkidle")

        def get_div_count():
            return len(page.query_selector_all("div.relative.cursor-pointer"))

        while True:
            # Get current count
            current_count = get_div_count()
            print(f"Current count: {current_count}")
            if current_count >= 93:
                break

            # Scroll down
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            time.sleep(2)

        divs = page.query_selector_all("div.relative.cursor-pointer")

        for index, div in enumerate(divs):

            print("scrapping div", index)

            div.click()

            page.wait_for_selector('div[id^="headlessui-dialog-panel"]', timeout=10000)

            try:
                heading_element = page.query_selector(
                    "h3.text-md.font-medium.line-clamp-2"
                )
                if heading_element is not None:
                    heading = heading_element.inner_text()
                else:
                    print("Error in heading")
                    heading = page.query_selector(
                        "text-sm.font-medium.line-clamp-3.shadow-black.text-shadow-sm"
                    ).inner_text()

                description_element = page.query_selector(
                    "p.text-sm.text-gray-700.line-clamp-3.w-auto.mt-3"
                )

                if description_element is not None:
                    description = description_element.inner_text()
                else:
                    print("Error in description")
                    description = None

                external_url = page.query_selector(
                    "div.flex.flex-row.justify-between.items-center a"
                ).get_attribute("href")

                if external_url.startswith("/"):
                    external_url = f"https://ferm.fao.org{external_url}"

            except Exception as e:
                print(f"Error: {e}")

                page_html = page.content()

                print(f"Page HTML after clicking on div {index}:\n{page_html}")

                continue

            # Print or store the extracted information
            print(f"Popup {index} Details:")
            print(f"Heading: {heading}")
            print(f"Description: {description}")
            print(f"External URL: {external_url}")

            good_practices.append(
                {
                    "heading": heading,
                    "description": description,
                    "external_url": external_url,
                    "domain": external_url.split("/")[2],
                }
            )

            page.mouse.click(10, 10)

        browser.close()


initiatives = []
scrape_initiatives(initiatives)

with open("temp/foa_initiatives_list.csv", "w", newline="") as file:
    writer = csv.DictWriter(
        file,
        fieldnames=["heading", "description", "external_url", "domain"],
        delimiter=";",
    )
    writer.writeheader()
    writer.writerows(initiatives)
