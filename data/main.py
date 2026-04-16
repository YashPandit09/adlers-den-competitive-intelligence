"""
pipeline.py  –  Entisi competitor intelligence pipeline (MVP)
─────────────────────────────────────────────────────────────
Stage 1: search_scraper  → product list  (name, price, url)
Stage 2: product_scraper → product detail (description, ingredients, weight_g)
Stage 3: merge + save    → data/raw.csv
"""

import sys
import os
import csv
import time

# ── Make project root importable so sibling packages resolve ─────────────────
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from scraper.search_scraper import scrape_entisi          # Stage 1
from scraper.product_scraper import scrape_product_details  # Stage 2

# ── Config ────────────────────────────────────────────────────────────────────
MAX_PRODUCTS   = 20          # MVP limit
REQUEST_DELAY  = 0.6         # seconds between detail requests (polite crawl)
OUTPUT_CSV     = os.path.join(os.path.dirname(__file__), "raw.csv")

CSV_FIELDS = ["name", "price", "url", "description", "ingredients", "weight_g"]


# ── Helpers ───────────────────────────────────────────────────────────────────
def _progress(current: int, total: int, name: str) -> None:
    bar_len = 30
    filled  = int(bar_len * current / total)
    bar     = "#" * filled + "-" * (bar_len - filled)
    print(f"  [{bar}] {current}/{total}  {name[:50]}", flush=True)


def _merge(search_item: dict, detail: dict) -> dict:
    """Combine a search result row with its product detail row."""
    return {
        "name":        detail.get("name")        or search_item.get("name"),
        "price":       search_item.get("price"),
        "url":         search_item.get("url"),
        "description": detail.get("description"),
        "ingredients": detail.get("ingredients"),
        "weight_g":    detail.get("weight_g"),
    }


def save_csv(rows: list[dict], path: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    print(f"\n[OK] Saved {len(rows)} rows -> {path}")


# ── Main pipeline ─────────────────────────────────────────────────────────────
def run_pipeline() -> list[dict]:
    # ── Stage 1: search ───────────────────────────────────────────────────────
    print("\n=== Stage 1: Fetching product list from entisi.com ===")
    all_products = scrape_entisi()                        # returns list[dict]
    products     = all_products[:MAX_PRODUCTS]
    print(f"    Found {len(all_products)} products, capping at {len(products)}.")

    # ── Stage 2 + 3: detail scrape → merge ───────────────────────────────────
    print(f"\n=== Stage 2: Scraping product details ({len(products)} URLs) ===")
    results: list[dict] = []
    failed:  list[str]  = []

    for i, item in enumerate(products, start=1):
        url  = item.get("url", "")
        name = item.get("name", "unknown")
        _progress(i, len(products), name)

        try:
            detail  = scrape_product_details(url, delay=REQUEST_DELAY)
            merged  = _merge(item, detail)
            results.append(merged)
        except Exception as exc:
            print(f"  [SKIP] {url}  ->  {exc}")
            failed.append(url)
            time.sleep(REQUEST_DELAY)   # still wait before next request

    # ── Stage 4: save CSV ─────────────────────────────────────────────────────
    print("\n=== Stage 3: Saving results ===")
    save_csv(results, OUTPUT_CSV)

    # ── Summary ───────────────────────────────────────────────────────────────
    print(f"\n--- Pipeline complete ---")
    print(f"  Scraped : {len(results)}")
    print(f"  Skipped : {len(failed)}")
    if failed:
        print("  Failed URLs:")
        for u in failed:
            print(f"    - {u}")

    return results


if __name__ == "__main__":
    data = run_pipeline()

    # Quick preview of first 3 rows
    print("\n--- Preview (first 3 rows) ---")
    for row in data[:3]:
        print()
        for k, v in row.items():
            val = str(v or "")
            print(f"  {k:<14}: {val[:100]}")
