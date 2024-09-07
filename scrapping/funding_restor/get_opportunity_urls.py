import pandas as pd
import requests
from bs4 import BeautifulSoup

# Base URL pattern with page number placeholder
base_url = "https://restor.eco/platform/funding-opportunities/?page={}"

# List to store extracted opportunities
opportunities = []

# Iterate through the first 10 pages (adjust the range if needed)
for page in range(1):  # Adjust range if there are more pages
    url = base_url.format(page)
    print(f"Scraping {url}...")

    try:
        # Send GET request to the current page
        response = requests.get(url)
        response.raise_for_status()  # Raise an error if the request was unsuccessful

        print(response.text)

        # Parse the page content with BeautifulSoup
        soup = BeautifulSoup(response.text, "html.parser")

        # Find all opportunity cards with data-gtm-loc="funding-opportunities"
        cards = soup.find_all("div", {"data-test-id": "funding-opportunity-card"})

        # Extract data from each card
        for card in cards:
            title = card.find("h3").text.strip() if card.find("h3") else "N/A"
            link = card.find("a")["href"] if card.find("a") else "N/A"
            description = card.find("p").text.strip() if card.find("p") else "N/A"

            opportunities.append(
                {"Title": title, "Link": link, "Description": description}
            )

        print(f"Extracted {len(cards)} cards from page {page}.")

    except requests.exceptions.RequestException as e:
        print(f"Error fetching {url}: {e}")
        continue

# Save the results to a CSV file
df = pd.DataFrame(opportunities)
df.to_csv("funding_opportunities.csv", index=False)

print("Scraping complete. Data saved to funding_opportunities.csv")
