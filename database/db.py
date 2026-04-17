import sqlite3
import pandas as pd
import os
import logging

logging.basicConfig(
    filename="logs/app.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Paths
# Ensure generic relative paths for cloud compatibility
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, '..'))

DB_PATH = os.path.join(PROJECT_ROOT, "data", "products.db")
CSV_PATH = os.path.join(PROJECT_ROOT, "data", "scored_products.csv")

os.makedirs(os.path.join(PROJECT_ROOT, "data"), exist_ok=True)
os.makedirs(os.path.join(PROJECT_ROOT, "logs"), exist_ok=True)

SCHEMA_COLS = [
    "name",
    "cleaned_name",
    "price_inr",
    "weight_g",
    "price_per_gram",
    "rating",
    "reviews",
    "popularity_score",
    "source",
]


def init_db():
    """Create the products table and populate it from scored_products.csv."""
    logger.info("Starting db initialization...")
    if not os.path.exists(CSV_PATH):
        logger.error(f"CSV not found: {CSV_PATH}")
        return

    df = pd.read_csv(CSV_PATH)

    # Ensure only schema columns are used; fill missing ones with None
    for col in SCHEMA_COLS:
        if col not in df.columns:
            df[col] = None
    df = df[SCHEMA_COLS]

    # Drop exact duplicate rows before inserting
    df = df.drop_duplicates()

    # Ensure data directory exists
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    try:
        # Replace existing table entirely (avoids duplicate inserts on re-run)
        df.to_sql("products", conn, if_exists="replace", index=False)
        logger.info(f"Inserted {len(df)} rows into products table")
        logger.info(f"Database saved to {DB_PATH}")
    except Exception as e:
        logger.error(f"Failed to insert into database: {e}")
    finally:
        conn.close()


def load_data():
    """Return the products table as a pandas DataFrame."""
    if not os.path.exists(DB_PATH):
        init_db()
        
    if not os.path.exists(DB_PATH):
        logger.warning("Database fallback engaged. Return empty DataFrame.")
        return pd.DataFrame()
        
    conn = sqlite3.connect(DB_PATH)
    try:
        df = pd.read_sql("SELECT * FROM products", conn)
        return df
    except sqlite3.OperationalError:
        init_db()
        try:
            df = pd.read_sql("SELECT * FROM products", conn)
            return df
        except Exception:
            return pd.DataFrame()
    finally:
        conn.close()


if __name__ == "__main__":
    logger.info("Initializing database...")
    init_db()

    logger.info("Verifying load_data()...")
    df = load_data()
    logger.info(f"Total rows verified: {len(df)}")
