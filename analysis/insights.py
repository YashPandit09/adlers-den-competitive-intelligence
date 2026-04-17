"""
insights.py — Generate business insights from scored product data
"""

import os
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


def assign_bucket(price):
    """Assign price bucket to a product."""
    if pd.isna(price):
        return "Unknown"
    if price < 300:
        return "Low (<₹300)"
    elif price < 1000:
        return "Mid (₹300–1000)"
    elif price < 3000:
        return "Premium (₹1000–3000)"
    else:
        return "Luxury (₹3000+)"


def extract_brand(name):
    """Extract brand (first word) from product name."""
    if pd.isna(name) or not name:
        return "Unknown"
    return str(name).split()[0].strip(",").strip("|")


def main():
    # ── 1. Load data ─────────────────────────────────────────────────────────
    input_path = os.path.join(PROJECT_ROOT, "data", "scored_products.csv")
    df = pd.read_csv(input_path)
    logger.info(f"Loaded: {len(df)} products\n")

    # ── 2. Create price buckets ──────────────────────────────────────────────
    df["price_bucket"] = df["price_inr"].apply(assign_bucket)
    df["brand"] = df["cleaned_name"].apply(extract_brand)

    # ── 3. Bucket analysis ───────────────────────────────────────────────────
    bucket_order = ["Low (<₹300)", "Mid (₹300–1000)", "Premium (₹1000–3000)", "Luxury (₹3000+)"]

    logger.info("=" * 60)
    logger.info("SEGMENT ANALYSIS")
    logger.info("=" * 60)

    bucket_stats = {}
    for bucket in bucket_order:
        segment = df[df["price_bucket"] == bucket]
        if len(segment) == 0:
            continue
        count = len(segment)
        avg_rating = segment["rating"].mean()
        avg_ppg = segment["price_per_gram"].mean()
        bucket_stats[bucket] = {
            "count": count,
            "avg_rating": avg_rating,
            "avg_ppg": avg_ppg,
        }
        logger.info(f"\n  {bucket}")
        logger.info(f"    Products       : {count}")
        logger.info(f"    Avg Rating     : {avg_rating:.2f}" if not pd.isna(avg_rating) else "    Avg Rating     : N/A")
        logger.info(f"    Avg ₹/gram     : {avg_ppg:.2f}" if not pd.isna(avg_ppg) else "    Avg ₹/gram     : N/A")

    # ── 4a. Top 5 best value products ────────────────────────────────────────
    logger.info("\n" + "=" * 60)
    logger.info("TOP 5 BEST VALUE PRODUCTS")
    logger.info("=" * 60)

    scored = df[df["popularity_score"] > 0].sort_values("popularity_score", ascending=False)
    for i, (_, row) in enumerate(scored.head(5).iterrows(), 1):
        name = str(row["cleaned_name"])[:55]
        price = row.get("price_inr", "N/A")
        score = row.get("popularity_score", 0)
        source = row.get("source", "")
        logger.info(f"  #{i} | ₹{price:.0f} | Score: {score:.2f} | [{source}] {name}")

    # ── 4b. Most common brands (top 5) ───────────────────────────────────────
    logger.info("\n" + "=" * 60)
    logger.info("TOP 5 BRANDS BY PRODUCT COUNT")
    logger.info("=" * 60)

    brand_counts = df["brand"].value_counts().head(5)
    for brand, count in brand_counts.items():
        logger.info(f"  {brand.ljust(20)} : {count} products")

    # ── 4c. Most competitive segment ─────────────────────────────────────────
    if bucket_stats:
        most_competitive = max(bucket_stats, key=lambda b: bucket_stats[b]["count"])
        least_competitive = min(bucket_stats, key=lambda b: bucket_stats[b]["count"])

    # ── 5. Business insights ─────────────────────────────────────────────────
    logger.info("\n" + "=" * 60)
    logger.info("BUSINESS INSIGHTS")
    logger.info("=" * 60)

    if bucket_stats:
        mc = most_competitive
        mc_count = bucket_stats[mc]["count"]
        logger.info(f"\n  1. Most competitive segment is '{mc}' with {mc_count} products.")
        logger.info(f"     → High competition means pricing and differentiation are key.")

        lc = least_competitive
        lc_count = bucket_stats[lc]["count"]
        logger.info(f"\n  2. Gap identified in '{lc}' segment (only {lc_count} products).")
        logger.info(f"     → Opportunity for Adlers Den to position a product here.")

    if len(scored) > 0:
        top = scored.iloc[0]
        logger.info(f"\n  3. Best value product: '{str(top['cleaned_name'])[:50]}'")
        logger.info(f"     → ₹{top['price_inr']:.0f} | Rating: {top['rating']} | Score: {top['popularity_score']:.2f}")

    # Entisi positioning
    entisi = df[df["source"] == "entisi"]
    if len(entisi) > 0:
        avg_entisi_price = entisi["price_inr"].mean()
        entisi_bucket = assign_bucket(avg_entisi_price)
        logger.info(f"\n  4. Entisi avg price: ₹{avg_entisi_price:.0f} → positions in '{entisi_bucket}' segment.")
        if len(entisi[entisi["price_per_gram"].notna()]) > 0:
            avg_entisi_ppg = entisi["price_per_gram"].mean()
            logger.info(f"     Entisi avg ₹/gram: {avg_entisi_ppg:.2f}")

    # Brand dominance
    top_brand = brand_counts.index[0] if len(brand_counts) > 0 else "N/A"
    logger.info(f"\n  5. Most dominant brand: '{top_brand}' ({brand_counts.iloc[0]} listings)")
    logger.info(f"     → Key competitor to monitor for pricing and product strategy.")

    logger.info(f"\n{'='*60}")
    logger.info("Insights complete.")
    logger.info(f"{'='*60}")


if __name__ == "__main__":
    main()
