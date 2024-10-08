from playwright.sync_api import sync_playwright

# Path to store browser context files (session, cookies)
USER_DATA_DIR = "playwright_user_data"


def scrape_funding_opportunities():
    with sync_playwright() as p:
        # Launch browser with persistent context to store session data
        browser = p.chromium.launch_persistent_context(
            USER_DATA_DIR,
            headless=False,  # Use False to see the browser and log in manually the first time
            args=["--start-maximized"],  # Start the browser maximized
        )

        # Open a new page in the persistent context
        page = browser.new_page()

        # Check if already logged in by navigating directly to the funding opportunities
        page.goto("https://restor.eco/platform/funding-opportunities/?page=1")

        page.wait_for_timeout(60000)

        # Wait for the funding cards to load on the page
        page.wait_for_selector('[data-gtm-loc="funding-opportunities"]', timeout=10000)

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
