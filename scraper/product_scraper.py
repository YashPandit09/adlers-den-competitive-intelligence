import requests
from bs4 import BeautifulSoup
import re
import json
import time

import logging
import os

os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    filename="logs/app.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}

# Weight regex: matches "1360 g", "1.5kg", "500g", "2 kg" etc.
WEIGHT_RE = re.compile(
    r"(\d+(?:\.\d+)?)\s*(kg|g)\b",
    re.IGNORECASE,
)

# Keywords that signal an ingredients / contains line
INGREDIENT_KEYWORDS = re.compile(
    r"\b(ingredients?|contains?|composition|made\s+(with|from))\b",
    re.IGNORECASE,
)


# ─────────────────────────────────────────────────────────────────────────────
# Helper: normalise any weight hit to grams
# ─────────────────────────────────────────────────────────────────────────────
def _parse_weight_g(text: str):
    """Return the first weight value found in *text* converted to grams, or None."""
    match = WEIGHT_RE.search(text)
    if not match:
        return None
    value = float(match.group(1))
    unit = match.group(2).lower()
    return value * 1000 if unit == "kg" else value


# ─────────────────────────────────────────────────────────────────────────────
# Helper: extract ingredients from plain text
# ─────────────────────────────────────────────────────────────────────────────
def _extract_ingredients(text: str):
    """
    Scan *text* sentence-by-sentence for an ingredients / contains line.
    Returns the first matching sentence, or None.
    """
    if not text:
        return None
    for sentence in re.split(r"(?<=[.!?])\s+|\n", text):
        if INGREDIENT_KEYWORDS.search(sentence):
            return sentence.strip() or None
    return None


# ─────────────────────────────────────────────────────────────────────────────
# Strategy 1 – Shopify product JSON endpoint  (primary, preferred)
# ─────────────────────────────────────────────────────────────────────────────
def _fetch_via_json(product_url: str):
    """
    Shopify exposes /products/<handle>.json for every store.
    Returns a populated dict on success, None if the endpoint is unavailable.
    """
    handle_match = re.search(r"/products/([^/?#]+)", product_url)
    if not handle_match:
        return None

    handle = handle_match.group(1)
    base = re.match(r"https?://[^/]+", product_url).group(0)
    json_url = f"{base}/products/{handle}.json"

    try:
        resp = requests.get(json_url, headers=HEADERS, timeout=10)
        if resp.status_code != 200:
            return None
        data = resp.json().get("product", {})
    except (requests.RequestException, json.JSONDecodeError):
        return None

    # ── Name ──────────────────────────────────────────────────────────────
    name = data.get("title") or None

    # ── Description: strip HTML → plain text ──────────────────────────────
    desc_html = data.get("body_html") or ""
    desc_text = BeautifulSoup(desc_html, "html.parser").get_text(
        separator=" ", strip=True
    ) or None

    # ── Weight from variant (Shopify stores in grams by default) ──────────
    weight_g = None
    variants = data.get("variants") or []
    if variants:
        raw_w = variants[0].get("weight")
        raw_unit = (variants[0].get("weight_unit") or "g").lower()
        if raw_w:
            weight_g = float(raw_w) * 1000 if raw_unit == "kg" else float(raw_w)

    # If the variant weight is missing / zero, fall back to regex on text
    if not weight_g:
        # Check the description text first, then the raw HTML (catches spec tables)
        weight_g = _parse_weight_g(desc_text or "") or _parse_weight_g(desc_html)

    # ── Ingredients ───────────────────────────────────────────────────────
    ingredients = _extract_ingredients(desc_text)

    return {
        "name": name,
        "description": desc_text,
        "ingredients": ingredients,
        "weight_g": weight_g,
        "source": "json",
        "url": product_url,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Strategy 2 – BeautifulSoup HTML fallback
# ─────────────────────────────────────────────────────────────────────────────
def _fetch_via_html(product_url: str) -> dict:
    """Parse the rendered product HTML page. Always returns a result dict."""
    result = {
        "name": None,
        "description": None,
        "ingredients": None,
        "weight_g": None,
        "source": "html",
        "url": product_url,
    }

    try:
        resp = requests.get(product_url, headers=HEADERS, timeout=12)
        resp.raise_for_status()
    except requests.RequestException:
        return result

    soup = BeautifulSoup(resp.text, "html.parser")

    # ── Product name: <h1> in the product section ─────────────────────────
    name_tag = soup.find("h1", class_=re.compile(r"product", re.I)) or soup.find("h1")
    if name_tag:
        result["name"] = name_tag.get_text(strip=True)

    # ── Description: common Shopify theme containers ───────────────────────
    desc_tag = None
    for selector in [
        {"class": re.compile(r"product[_-]?description", re.I)},
        {"class": re.compile(r"product[_-]?(detail|body|content)", re.I)},
        {"class": re.compile(r"\brte\b", re.I)},   # Shopify "rich-text editor"
        {"itemprop": "description"},
    ]:
        desc_tag = soup.find(["div", "section", "article", "p"], selector)
        if desc_tag:
            break

    description = desc_tag.get_text(separator=" ", strip=True) if desc_tag else None
    result["description"] = description or None

    # ── Weight: regex over full page text ─────────────────────────────────
    page_text = soup.get_text(separator=" ")
    result["weight_g"] = _parse_weight_g(page_text)

    # ── Ingredients ───────────────────────────────────────────────────────
    result["ingredients"] = _extract_ingredients(description or page_text)

    return result


# ─────────────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────────────
def scrape_product_details(product_url: str, delay: float = 0.5) -> dict:
    """
    Extract structured product details from an entisi.com product URL.

    Parameters
    ----------
    product_url : str
        Full URL to a product page, e.g.
        ``https://entisi.com/products/grandeur-gift-basket``
    delay : float
        Seconds to sleep before each request (polite crawling).

    Returns
    -------
    dict with keys:
        name        – str | None
        description – str | None
        ingredients – str | None   (first matching sentence)
        weight_g    – float | None (always in grams)
        source      – "json" | "html"
        url         – str

    Missing fields are ``None``; the function never raises.
    """
    time.sleep(delay)

    # Prefer the clean JSON route
    result = _fetch_via_json(product_url)
    if result and result.get("name"):
        return result

    # Fall back to HTML scraping
    return _fetch_via_html(product_url)


# ─────────────────────────────────────────────────────────────────────────────
# Smoke-test
# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    TEST_URLS = [
        "https://entisi.com/collections/all/products/grandeur-gift-basket",
        "https://entisi.com/collections/all/products/delight-hamper-basket",
        "https://entisi.com/products/41-plain-milk-bar",
    ]

    for url in TEST_URLS:
        logger.info(f"\n{'-' * 62}")
        logger.info(f"URL        : {url}")
        d = scrape_product_details(url)
        logger.info(f"Name       : {d['name']}")
        logger.info(f"Weight (g) : {d['weight_g']}")
        logger.info(f"Ingredients: {d['ingredients']}")
        desc = d["description"]
        snippet = (desc[:220] + "…") if desc and len(desc) > 220 else desc
        logger.info(f"Description: {snippet}")
        logger.info(f"Source     : {d['source']}")
