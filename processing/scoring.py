"""
scoring.py — Compute popularity scores and rank products
"""

import os
import math
import pandas as pd

import logging
import os

os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    filename="logs/app.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def main():
    # ── 1. Load cleaned data ─────────────────────────────────────────────────
    input_path = os.path.join(PROJECT_ROOT, "data", "cleaned_products.csv")
    df = pd.read_csv(input_path)
    logger.info(f"Loaded: {len(df)} rows from cleaned_products.csv")

    # ── 2. Compute popularity_score ──────────────────────────────────────────
    def calc_score(row):
        rating = row.get("rating")
        ppg = row.get("price_per_gram")
        price_inr = row.get("price_inr")
        has_rating = not pd.isna(rating) if rating is not None else False
        has_ppg = not pd.isna(ppg) if ppg is not None else False
        has_price = not pd.isna(price_inr) if price_inr is not None else False

        if has_rating and has_ppg and ppg > 0:
            return round((rating * 10) / ppg, 2)
        elif has_rating and has_price and price_inr > 0:
            return round((rating * 1000) / price_inr, 2)
        else:
            return 0

    df["popularity_score"] = df.apply(calc_score, axis=1)

    # ── 3. Rank (descending by score) ────────────────────────────────────────
    df = df.sort_values("popularity_score", ascending=False).reset_index(drop=True)
    df["popularity_rank"] = range(1, len(df) + 1)

    # ── 4. Print top 5 ──────────────────────────────────────────────────────
    scored = df[df["popularity_score"] > 0]
    unscored = len(df) - len(scored)
    logger.info(f"\nScored: {len(scored)} | Unscored (missing rating/reviews): {unscored}")

    logger.info(f"\n{'='*50}")
    logger.info("Top 5 Products by Popularity Score")
    logger.info(f"{'='*50}")
    top5 = scored.head(5) if len(scored) > 0 else df.head(5)
    for _, row in top5.iterrows():
        logger.info(f"  #{int(row['popularity_rank'])} | Score: {row['popularity_score']:.2f} | "
              f"Rating: {row['rating']} | Reviews: {row.get('reviews', 'N/A')} | "
              f"{str(row['cleaned_name'])[:60]}")

    # ── 5. Save ──────────────────────────────────────────────────────────────
    output_path = os.path.join(PROJECT_ROOT, "data", "scored_products.csv")
    df.to_csv(output_path, index=False)
    logger.info(f"\nSaved → {output_path}")


if __name__ == "__main__":
    main()
