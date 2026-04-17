import requests
from bs4 import BeautifulSoup
import re

import logging
import os

os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    filename="logs/app.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


BASE_URL = "https://entisi.com"

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}


def scrape_entisi():
    url = f"{BASE_URL}/collections/all"

    response = requests.get(url, headers=HEADERS)
    logger.info(f"Status: {response.status_code}")

    soup = BeautifulSoup(response.text, "html.parser")

    products = []

    items = soup.find_all("div", class_="product-card-info")

    logger.info(f"Items found: {len(items)}")

    for item in items:
        try:
            link_tag = item.find("a", class_="product-card-title")
            price_tag = item.find("span", class_="price")

            if not link_tag or not price_tag:
                continue

            name = link_tag.text.strip()
            relative_url = link_tag.get("href")
            product_url = BASE_URL + relative_url

            price_text = price_tag.text.replace(",", "")
            prices = re.findall(r"\d+\.?\d*", price_text)
            price = str(max([float(p) for p in prices])) if prices else None

            products.append({
                "name": name,
                "price": price,
                "url": product_url
            })

        except:
            continue

    return products


if __name__ == "__main__":
    data = scrape_entisi()

    logger.info("\n--- SAMPLE ---\n")
    for d in data[:5]:
        logger.info(d)

    logger.info(f"\nTotal: {len(data)}")