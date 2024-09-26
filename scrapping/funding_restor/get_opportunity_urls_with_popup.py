from playwright.sync_api import sync_playwright


def scrape_funding_opportunities():
    with sync_playwright() as p:
        # Launch the browser in non-headless mode
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()  # Create a new browser context
        page = context.new_page()

        page.goto("https://restor.eco/login")

        with page.expect_popup() as popup_info:
            page.click('text="Log in with Google"')

        popup = popup_info.value

        popup.wait_for_selector('input[type="email"]', timeout=10000)

        popup.wait_for_timeout(60000)  # Wait for 60 seconds

        popup.wait_for_load_state("networkidle")

        popup.close()

        page.bring_to_front()

        page.goto("https://restor.eco/platform/funding-opportunities/?page=1")

        page.wait_for_selector('[data-gtm-loc="funding-opportunities"]')

        # Get all funding cards
        funding_cards = page.query_selector_all(
            '[data-gtm-loc="funding-opportunities"]'
        )

        # Extract details from each funding card
        for card in funding_cards:
            title = (
                card.query_selector(".funding-card-title").inner_text()
                if card.query_selector(".funding-card-title")
                else "N/A"
            )
            organization = (
                card.query_selector(".funding-card-organization").inner_text()
                if card.query_selector(".funding-card-organization")
                else "N/A"
            )
            deadline = (
                card.query_selector(".funding-card-deadline").inner_text()
                if card.query_selector(".funding-card-deadline")
                else "N/A"
            )
            status = (
                card.query_selector(".funding-card-status").inner_text()
                if card.query_selector(".funding-card-status")
                else "N/A"
            )

            # Print or process the details
            print(f"Title: {title}")
            print(f"Organization: {organization}")
            print(f"Deadline: {deadline}")
            print(f"Status: {status}")
            print("-" * 50)

        # Close the browser
        browser.close()


# Run the scraper function
scrape_funding_opportunities()
