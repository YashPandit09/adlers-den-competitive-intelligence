import os
import re
import csv
import requests
from bs4 import BeautifulSoup

import logging
import os

os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    filename="logs/app.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def scrape_adlers():
    logger.info("Fetching product list from Adler's Den sitemap...")
    sitemap_url = "https://adlersden.com/product-sitemap.xml"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }
    
    try:
        response = requests.get(sitemap_url, headers=headers, timeout=15)
        response.raise_for_status()
    except Exception as e:
        logger.info(f"Failed to fetch sitemap: {e}")
        return
    
    import concurrent.futures

    soup = BeautifulSoup(response.content, 'xml')
    product_urls = [loc.text for loc in soup.find_all('loc') if '/product/' in loc.text]
    
    logger.info(f"Found {len(product_urls)} products via sitemap. Starting fast scrape...")
    
    scraped_data = []
    
    def fetch_product(url):
        try:
            prod_req = requests.get(url, headers=headers, timeout=10)
            if prod_req.status_code != 200:
                return None
            
            prod_soup = BeautifulSoup(prod_req.content, 'html.parser')
            
            name_tag = prod_soup.find('h1', class_=re.compile(r'product_title|title', re.I))
            if not name_tag:
                name_tag = prod_soup.find('h1')
            if not name_tag:
                return None
            name = name_tag.text.strip()
            
            price = None
            price_container = prod_soup.find('p', class_='price')
            if not price_container:
                price_container = prod_soup.find('div', class_=re.compile(r'price', re.I))
                
            if price_container:
                price_amounts = price_container.find_all(class_='woocommerce-Price-amount')
                if price_amounts:
                    price_text = price_amounts[-1].text
                    clean_price = price_text.replace('₹', '').replace(',', '').strip()
                    try:
                        price = float(re.sub(r'[^\d.]', '', clean_price))
                    except ValueError:
                        pass
                        
            if price is None:
                return None
                
            weight = None
            weight_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:g|gm|grams|kg)\b', name, re.IGNORECASE)
            if weight_match:
                weight = weight_match.group(0)
                
            return {
                'name': name,
                'price': price,
                'weight': weight if weight else '',
                'url': url,
                'source': 'adlers'
            }
        except Exception as e:
            return None

    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        results = list(executor.map(fetch_product, product_urls))
        
    for res in results:
        if res:
            scraped_data.append(res)

    
    # Removed sequential loop because threading replaced it

    total_scraped = len(scraped_data)
    logger.info(f"\nScraping complete.")
    logger.info(f"Total products scraped: {total_scraped}")
    
    if total_scraped == 0:
        logger.info("No products data could be extracted.")
        return
        
    # 5. Save output
    os.makedirs('data', exist_ok=True)
    output_file = 'data/adlers_raw.csv'
    
    fieldnames = ['name', 'price', 'weight', 'url', 'source']
    
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(scraped_data)
        
    logger.info(f"Data saved to {output_file}")
    
    # 6. Print sample
    logger.info("\nSample 3 rows:")
    for row in scraped_data[:3]:
        # Handle printing unicode safely
        logger.info({k: str(v).encode('ascii', 'ignore').decode() if isinstance(v, str) else v for k, v in row.items()})

if __name__ == "__main__":
    scrape_adlers()
