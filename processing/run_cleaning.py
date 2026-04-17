"""
run_cleaning.py — Apply advanced_cleaner functions to all_products.csv
"""

import sys
import os
import pandas as pd

# Make project root importable
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from processing.advanced_cleaner import (
    parse_price,
    normalize_weight,
    clean_text,
    dedup_hash,
    safe_get,
    extract_weight_from_text,
)

import logging
import os

os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    filename="logs/app.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def main():
    # ── 1. Load data ─────────────────────────────────────────────────────────
    input_path = os.path.join(PROJECT_ROOT, "data", "all_products.csv")
    df = pd.read_csv(input_path)
    total_before = len(df)
    logger.info(f"Loaded: {total_before} rows from all_products.csv")

    # ── 2. Apply parse_price ─────────────────────────────────────────────────
    price_parsed = df["price"].apply(parse_price)
    df["original_currency"] = price_parsed.apply(lambda x: x["original_currency"])
    df["original_value"] = price_parsed.apply(lambda x: x["original_value"])
    df["standardized_price_inr"] = price_parsed.apply(lambda x: x["standardized_price_inr"])
    df["price_inr"] = df["standardized_price_inr"]

    # ── 3. Apply clean_text on product name ──────────────────────────────────
    df["cleaned_name"] = df["name"].apply(clean_text)

    # ── 3.5 Apply weight normalization & extraction ──────────────────────────
    df["weight_g"] = df["weight_g"].apply(normalize_weight)
    
    # Fill missing weights by extracting from title
    def fill_weight(row):
        weight = row.get("weight_g")

        # If already valid → keep
        if pd.notna(weight) and weight > 0:
            return weight

        # Try extraction from cleaned_name first
        text = safe_get(row.get("cleaned_name"), "")
        extracted = extract_weight_from_text(text)

        # Fallback to original name
        if not extracted:
            text = safe_get(row.get("name"), "")
            extracted = extract_weight_from_text(text)

        return extracted if extracted else None
        
    df["weight_g"] = df.apply(fill_weight, axis=1)

    # ── 5. Skip rows with missing critical data ─────────────────────────────
    df = df.dropna(subset=["cleaned_name", "price_inr"])
    total_after_clean = len(df)
    logger.info(f"After cleaning (removed missing name/price): {total_after_clean} rows")

    # ── 5.5 Filter relevant product types ────────────────────────────────────
    before_filter = len(df)
    
    keep_required = "chocolate"
    keep_any = ["gift", "box", "hamper", "combo", "pack"]
    exclude_keywords = ["dry fruit", "muesli", "sprinkles", "spread", "protein", "nuts"]

    def is_relevant(name):
        if pd.isna(name): return False
        name_lower = str(name).lower()
        
        has_required = keep_required in name_lower
        has_any = any(k in name_lower for k in keep_any)
        has_exclude = any(e in name_lower for e in exclude_keywords)
        
        return has_required and has_any and not has_exclude

    df = df[df["cleaned_name"].apply(is_relevant)]
    total_after_filter = len(df)
    logger.info(f"Rows before filter: {before_filter} | After filter: {total_after_filter}")

    # ── 6. Compute price_per_gram (safe division) ────────────────────────────
    df["price_per_gram"] = df.apply(
    lambda row: round(row["price_inr"] / row["weight_g"], 2)
    if pd.notna(row["weight_g"]) and row["weight_g"] > 0
    else None,
    axis=1,
)

    # ── 7. Generate dedup hash ───────────────────────────────────────────────
    df["dedup_hash"] = df.apply(
        lambda row: dedup_hash(
            brand=None,
            cleaned_name=row["cleaned_name"],
            weight_g=safe_get(row["weight_g"], default=0),
        ),
        axis=1,
    )

    # ── 8. Drop duplicates using hash ────────────────────────────────────────
    df = df.drop_duplicates(subset=["dedup_hash"], keep="first")
    total_after_dedup = len(df)
    logger.info(f"After dedup: {total_after_dedup} rows")

    # ── 9. Save output ───────────────────────────────────────────────────────
    output_path = os.path.join(PROJECT_ROOT, "data", "cleaned_products.csv")
    df.to_csv(output_path, index=False)

    # ── 10. Summary ──────────────────────────────────────────────────────────
    logger.info(f"\n{'='*35}")
    logger.info("Cleaning Pipeline Complete!")
    logger.info(f"{'='*35}")
    logger.info(f"  Total before   : {total_before}")
    logger.info(f"  After cleaning : {total_after_clean}")
    logger.info(f"  After dedup    : {total_after_dedup}")
    logger.info(f"\nSaved → {output_path}")

    logger.info(f"Weights filled: {df['weight_g'].notna().sum()}")
    logger.info(f"PPG filled: {df['price_per_gram'].notna().sum()}")
if __name__ == "__main__":
    main()
