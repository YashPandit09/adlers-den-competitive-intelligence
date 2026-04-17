"""
advanced_cleaner.py — Production-ready data cleaning pipeline
─────────────────────────────────────────────────────────────
Functions for price parsing, weight normalization, text cleaning,
deduplication hashing, and missing value handling.
"""

import re
import hashlib

import logging
import os

os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    filename="logs/app.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)



# ── Static conversion rate ────────────────────────────────────────────────────
USD_TO_INR = 83.50


# ── 1. Price Parsing ─────────────────────────────────────────────────────────

def parse_price(raw_price):
    """
    Parse messy price strings into structured output.

    Input:  "₹1,499", "Rs. 499.00", "$25", 1499.0, None
    Output: dict with original_currency, original_value, standardized_price_inr
    """
    if raw_price is None:
        return {"original_currency": None, "original_value": None, "standardized_price_inr": None}

    # If already a number, assume INR
    if isinstance(raw_price, (int, float)):
        return {
            "original_currency": "INR",
            "original_value": float(raw_price),
            "standardized_price_inr": float(raw_price),
        }

    text = str(raw_price).strip()
    if not text:
        return {"original_currency": None, "original_value": None, "standardized_price_inr": None}

    # Detect currency
    currency = "INR"  # default
    if "$" in text and "₹" not in text:
        currency = "USD"
    elif "€" in text:
        currency = "EUR"
    elif "£" in text:
        currency = "GBP"

    # Extract numeric value — strip currency symbols first
    cleaned = re.sub(r"(₹|Rs\.?|INR|USD|\$|€|£)", "", text, flags=re.IGNORECASE).strip()
    numeric = re.sub(r"[^\d.]", "", cleaned)
    if not numeric:
        return {"original_currency": currency, "original_value": None, "standardized_price_inr": None}

    try:
        value = float(numeric)
    except ValueError:
        return {"original_currency": currency, "original_value": None, "standardized_price_inr": None}

    # Convert to INR
    if currency == "USD":
        price_inr = round(value * USD_TO_INR, 2)
    else:
        price_inr = round(value, 2)

    return {
        "original_currency": currency,
        "original_value": round(value, 2),
        "standardized_price_inr": price_inr,
    }


# ── 2. Weight Normalization ──────────────────────────────────────────────────

def normalize_weight(raw_weight):
    """
    Normalize weight strings to grams (float).

    Input:  "1kg", "250 g", "0.5 kg", "500gm", 250.0, None
    Output: float (grams) or None
    """
    if raw_weight is None:
        return None

    # If already a number, assume grams
    if isinstance(raw_weight, (int, float)):
        return float(raw_weight) if raw_weight > 0 else None

    text = str(raw_weight).strip().lower()
    if not text:
        return None

    # Match number followed by unit
    match = re.match(r"([\d.]+)\s*(kg|kgs|kilogram|kilograms|g|gm|gms|gram|grams|mg|ml|l|ltr|litre|pcs|pieces)?", text)
    if not match:
        return None

    try:
        value = float(match.group(1))
    except ValueError:
        return None

    unit = match.group(2) or "g"

    if unit in ("kg", "kgs", "kilogram", "kilograms"):
        return round(value * 1000, 2)
    elif unit in ("mg",):
        return round(value / 1000, 2)
    elif unit in ("g", "gm", "gms", "gram", "grams"):
        return round(value, 2)
    elif unit in ("l", "ltr", "litre", "ml"):
        # ml ≈ g for liquids; litre = 1000ml
        if unit == "ml":
            return round(value, 2)
        return round(value * 1000, 2)
    else:
        return round(value, 2)


# ── 3. Text Cleaning ────────────────────────────────────────────────────────

# Noise words to strip from product names
NOISE_WORDS = {
    "sale", "bestseller", "best seller", "limited", "limited edition",
    "offer", "deal", "discount", "clearance", "hot", "new arrival",
    "trending", "top rated", "free shipping", "buy now", "hurry",
    "exclusive", "special", "combo offer", "mega", "super",
}

# Regex to strip emojis
EMOJI_PATTERN = re.compile(
    "["
    "\U0001F600-\U0001F64F"  # emoticons
    "\U0001F300-\U0001F5FF"  # symbols & pictographs
    "\U0001F680-\U0001F6FF"  # transport & map
    "\U0001F1E0-\U0001F1FF"  # flags
    "\U00002702-\U000027B0"
    "\U000024C2-\U0001F251"
    "\U0001f926-\U0001f937"
    "\U00010000-\U0010ffff"
    "]+",
    flags=re.UNICODE,
)


def clean_text(raw_text):
    """
    Remove promotional noise and emojis, keep core product meaning.

    Input:  "🔥 SALE Ferrero Rocher Premium 24 Pieces 🎁 LIMITED"
    Output: "Ferrero Rocher Premium 24 Pieces"
    """
    if raw_text is None:
        return None

    text = str(raw_text).strip()
    if not text:
        return None

    # Remove emojis
    text = EMOJI_PATTERN.sub("", text)

    # Remove noise words (case-insensitive, whole words only)
    for word in NOISE_WORDS:
        text = re.sub(rf"\b{re.escape(word)}\b", "", text, flags=re.IGNORECASE)

    # Collapse multiple spaces and strip
    text = re.sub(r"\s{2,}", " ", text).strip()

    # Remove leading/trailing punctuation artifacts
    text = text.strip("|-–—•·,;:")

    return text.strip() if text.strip() else None


# ── 4. Deduplication Hash ────────────────────────────────────────────────────

def dedup_hash(brand, cleaned_name, weight_g):
    """
    Generate MD5 hash for deduplication.

    Input:  brand="Ferrero", cleaned_name="Rocher Premium 24 Pieces", weight_g=300.0
    Output: "a3f2b8c1..." (32-char hex string)
    """
    brand_str = str(brand or "").strip().lower()
    name_str = str(cleaned_name or "").strip().lower()
    weight_str = str(weight_g or "0")

    key = f"{brand_str}|{name_str}|{weight_str}"
    return hashlib.md5(key.encode("utf-8")).hexdigest()


# ── 4.5 Extract Weight from Text ───────────────────────────────────────────────

def extract_weight_from_text(text):
    """
    Extract weight from product title and normalize to grams.
    Returns the largest found weight in the string.
    """
    if not text or not isinstance(text, str):
        return None
        
    matches = re.findall(r"(\d+\.?\d*)\s?(kg|g|gm|grams)\b", text, flags=re.IGNORECASE)
    weights = []
    
    for val, unit in matches:
        try:
            v = float(val)
            unit_lower = unit.lower()
            if unit_lower == "kg":
                weights.append(v * 1000)
            else:
                weights.append(v)
        except ValueError:
            pass
            
    return max(weights) if weights else None


# ── 5. Safe Missing Value Handler ───────────────────────────────────────────

def safe_get(value, default=None, dtype=None):
    """
    Safely extract a value, handling None/NaN/empty strings.

    Input:  safe_get("", default=0, dtype=float)  →  0
            safe_get(None)                         →  None
            safe_get("4.2", dtype=float)           →  4.2
    """
    if value is None:
        return default

    # Handle pandas NaN
    try:
        import math
        if isinstance(value, float) and math.isnan(value):
            return default
    except (TypeError, ValueError):
        pass

    # Handle empty strings
    if isinstance(value, str) and not value.strip():
        return default

    # Cast to dtype if specified
    if dtype is not None:
        try:
            return dtype(value)
        except (ValueError, TypeError):
            return default

    return value


# ── Quick Test ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    # Price parsing
    logger.info("=== Price Parsing ===")
    for p in ["₹1,499", "Rs. 499.00", "$25", 1200.0, None, ""]:
        logger.info(f"  {str(p):>15} → {parse_price(p)}")

    # Weight normalization
    logger.info("\n=== Weight Normalization ===")
    for w in ["1kg", "250 g", "0.5 kg", "500gm", "100mg", 300.0, None]:
        logger.info(f"  {str(w):>10} → {normalize_weight(w)} g")

    # Text cleaning
    logger.info("\n=== Text Cleaning ===")
    for t in [
        "🔥 SALE Ferrero Rocher Premium 24 Pieces 🎁 LIMITED",
        "Bestseller - Cadbury Dairy Milk 🍫 Offer",
        None,
    ]:
        logger.info(f"  '{t}' → '{clean_text(t)}'")

    # Dedup hash
    logger.info("\n=== Dedup Hash ===")
    h1 = dedup_hash("Ferrero", "Rocher Premium 24 Pieces", 300.0)
    h2 = dedup_hash("ferrero", "rocher premium 24 pieces", 300.0)
    logger.info(f"  Hash 1: {h1}")
    logger.info(f"  Hash 2: {h2}")
    logger.info(f"  Match:  {h1 == h2}")

    # Safe get
    logger.info("\n=== Safe Get ===")
    for v, d, dt in [(None, 0, float), ("", "N/A", None), ("4.2", None, float), (float("nan"), 0, None)]:
        logger.info(f"  safe_get({v!r}, default={d!r}, dtype={dt}) → {safe_get(v, d, dt)}")
