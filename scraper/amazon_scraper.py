from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import urllib.parse
import time
import random

import logging
import os

os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    filename="logs/app.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)



BASE_URL = "https://www.amazon.in/s"


def get_driver():
    """Create a headless Chrome driver with anti-detection settings."""
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--window-size=1920,1080")
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
    )
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)

    # Remove webdriver flag to avoid detection
    driver.execute_cdp_cmd(
        "Page.addScriptToEvaluateOnNewDocument",
        {"source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"},
    )

    return driver


def scrape_amazon_search(query):
    """Scrape Amazon India search results for a given query."""
    driver = get_driver()

    try:
        url = f"{BASE_URL}?k={query.replace(' ', '+')}&ref=nb_sb_noss"
        logger.info(f"Opening: {url}")
        driver.get(url)

        # Wait for search results to load
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div[data-component-type='s-search-result']"))
        )

        # Scroll down to trigger lazy loading
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight / 2);")
        time.sleep(2)
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)

        logger.info("Status: 200 (page loaded)")

        page_source = driver.page_source

    except Exception as e:
        logger.info(f"Page load failed: {e}")
        return []

    finally:
        driver.quit()

    # Parse products
    soup = BeautifulSoup(page_source, "html.parser")
    products = []
    results = soup.find_all("div", {"data-component-type": "s-search-result"})

    logger.info(f"Found {len(results)} result divs")

    for item in results:
        try:
            # FIX 1 — Skip sponsored/ad products
            if "AdHolder" in str(item.get("class", [])):
                continue

            # Name — img alt always has full product name
            img = item.find("img", {"class": "s-image"})
            h2 = item.find("h2")
            name = None
            if img and img.get("alt"):
                name = img["alt"].strip()
            if not name and h2:
                name = h2.text.strip()
            if not name:
                continue

            # URL — clean /dp/ASIN
            asin = item.get("data-asin")
            product_link = item.find("a", class_=lambda c: c and "s-line-clamp" in " ".join(c) if isinstance(c, list) else c and "s-line-clamp" in c)

            if product_link and product_link.get("href"):
                href = product_link["href"]
                # If it's a sspa redirect, extract the real URL
                parsed = urllib.parse.urlparse(href)
                query_params = urllib.parse.parse_qs(parsed.query)
                if "url" in query_params:
                    clean_path = urllib.parse.unquote(query_params["url"][0])
                    url = "https://www.amazon.in" + clean_path
                elif href.startswith("/"):
                    url = "https://www.amazon.in" + href
                else:
                    url = href
            elif asin:
                url = f"https://www.amazon.in/dp/{asin}"
            else:
                url = None

            # Simplify URL to /dp/ASIN if possible
            if asin and url:
                url = f"https://www.amazon.in/dp/{asin}"

            # Price
            price_whole = item.find("span", "a-price-whole")
            if price_whole:
                price_text = price_whole.text.strip().replace(",", "").rstrip(".")
                price = float(price_text)
            else:
                price = None

            # Rating
            rating_tag = item.find("span", "a-icon-alt")
            rating = None
            if rating_tag:
                try:
                    rating = float(rating_tag.text.split()[0])
                except (ValueError, IndexError):
                    pass

            # Reviews — extract review count from star-rating popover
            reviews = None
            popover = item.find("a", class_="a-popover-trigger")
            if popover:
                aria = popover.get("aria-label", "")
                # Look for link AFTER the star rating (sibling)
                next_link = popover.find_next_sibling("a")
                if next_link:
                    text = next_link.text.strip().replace(",", "")
                    if text.isdigit():
                        reviews = int(text)

            products.append({
                "name": name,
                "price": price,
                "rating": rating,
                "reviews": reviews,
                "url": url,
                "source": "amazon"
            })

        except Exception:
            continue

    return products


if __name__ == "__main__":
    queries = [
        "gourmet chocolate box",
        "premium chocolate gift box",
        "chocolate gift hamper",
        "dry fruit chocolate combo",
        "luxury chocolates india"
    ]

    all_products = []

    for q in queries:
        logger.info(f"\n{'='*50}")
        logger.info(f"Scraping: {q}")
        logger.info('='*50)
        results = scrape_amazon_search(q)
        all_products.extend(results)
        logger.info(f"Got {len(results)} products")

    logger.info(f"\n\nTotal collected: {len(all_products)}")

    # Deduplicate using (name, price) as key
    seen = {}
    for p in all_products:
        key = (p["name"], p["price"])
        if key not in seen:
            seen[key] = p

    final_data = list(seen.values())
    logger.info(f"After dedup: {len(final_data)}")

    import pandas as pd
    import os
    
    # Save to data/amazon_raw.csv
    os.makedirs("data", exist_ok=True)
    df = pd.DataFrame(final_data)
    df.to_csv("data/amazon_raw.csv", index=False)
    
    logger.info(f"\nSaved amazon_raw.csv with {len(final_data)} rows")