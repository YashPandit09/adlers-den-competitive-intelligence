import time
import os
import urllib.parse
import pandas as pd
from bs4 import BeautifulSoup

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

import logging
import os

os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    filename="logs/app.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def scrape_flipkart():
    queries = [
        "gourmet chocolate box",
        "premium chocolate gift box",
        "chocolate gift hamper",
        "dry fruit chocolate combo",
        "luxury chocolates india"
    ]

    all_products = []

    # 1. Setup Chrome
    options = Options()
    # Open Chrome in normal (non-headless) explicitly
    options.add_argument("--start-maximized")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    wait = WebDriverWait(driver, 10)

    try:
        # 2. Queries
        for query in queries:
            logger.info(f"\n{'='*50}")
            logger.info(f"Scraping Flipkart: {query}")
            logger.info('='*50)
            
            query_encoded = urllib.parse.quote_plus(query)
            query_products = []
            
            # 3. Pagination
            for page in range(1, 3):
                url = f"https://www.flipkart.com/search?q={query_encoded}&page={page}"
                driver.get(url)
                
                # 4. Wait
                time.sleep(3)  # basic wait to ensure product grid scripts finish loading
                
                soup = BeautifulSoup(driver.page_source, "html.parser")
                
                # 6. Selectors - product container
                # Trying _1AtVbE similar containers or data-id based tracking divs
                item_divs = soup.find_all("div", class_="_1AtVbE")
                if not item_divs:
                    item_divs = soup.find_all("div", attrs={"data-id": True})
                
                for item in item_divs:
                    try:
                        # 5. Extract Details
                        
                        # Name
                        name = None
                        name_elem = item.find("div", class_="_4rR01T") or item.find("a", class_="s1Q9rs")
                        if name_elem:
                            name = name_elem.get("title") or name_elem.text.strip()
                            
                        # Generic fallback if classes changed slightly
                        if not name:
                            a_tags = item.find_all("a", title=True)
                            for a in a_tags:
                                if "₹" not in a.text:
                                    name = a.get("title") or a.text.strip()
                                    if name:
                                        break

                        if not name:
                            continue
                            
                        # Price
                        price = None
                        price_elem = item.find("div", class_="_30jeq3")
                        
                        # Generic fallback for price
                        if not price_elem:
                            prices = item.find_all(string=lambda text: "₹" in text if text else False)
                            for p_text in prices:
                                clean_val = p_text.replace("₹", "").replace(",", "").strip()
                                if clean_val.isdigit():
                                    price = float(clean_val)
                                    break
                        else:
                            # 7. Clean price
                            price_text = price_elem.text.replace("₹", "").replace(",", "").strip()
                            if price_text.isdigit():
                                price = float(price_text)
                        
                        if not price:
                            continue
                            
                        # Rating
                        rating = None
                        rating_elem = item.find("div", class_="_3LWZlK")
                        if rating_elem:
                            try:
                                rating = float(rating_elem.text.strip())
                            except ValueError:
                                pass
                                
                        # URL
                        url = None
                        link_elem = item.find("a", href=True)
                        if link_elem:
                            url = link_elem["href"]
                            if not url.startswith("http"):
                                url = "https://www.flipkart.com" + url
                            if "?" in url:
                                url = url.split("?")[0]
                                
                        query_products.append({
                            "name": name,
                            "price": price,
                            "rating": rating,
                            "url": url,
                            "source": "flipkart"
                        })
                        
                    except Exception:
                        continue
                        
            # 10. Print per query count
            logger.info(f"Products found: {len(query_products)}")
            all_products.extend(query_products)
            
    finally:
        # 11. Close driver at end
        driver.quit()

    # 10. Print total collected
    logger.info(f"\nTotal collected: {len(all_products)}")

    # 8. Deduplicate
    seen = {}
    for p in all_products:
        key = (p["name"], p["price"])
        if key not in seen:
            seen[key] = p

    final_data = list(seen.values())
    
    # 10. Print after dedup
    logger.info(f"After dedup: {len(final_data)}")

    # 9. Save
    os.makedirs("data", exist_ok=True)
    df = pd.DataFrame(final_data)
    df.to_csv("data/flipkart_raw.csv", index=False)
    
    # 10. Print sample 3 rows
    logger.info("\nSample (first 3):")
    for d in final_data[:3]:
        logger.info(d)

if __name__ == "__main__":
    scrape_flipkart()
