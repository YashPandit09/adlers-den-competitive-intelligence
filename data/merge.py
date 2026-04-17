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


def main():
    # File paths
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    amazon_path = os.path.join(project_root, "data", "amazon_raw.csv")
    flipkart_path = os.path.join(project_root, "data", "flipkart_raw.csv")
    adlers_path = os.path.join(project_root, "data", "adlers_raw.csv")
    entisi_path = os.path.join(project_root, "data", "clean.csv")
    output_path = os.path.join(project_root, "data", "all_products.csv")

    # Load Amazon data
    logger.info("Loading Amazon data...")
    if os.path.exists(amazon_path):
        df_amazon = pd.read_csv(amazon_path)
    else:
        logger.info(f"[WARNING] {amazon_path} not found.")
        df_amazon = pd.DataFrame()

    # Load Flipkart data
    logger.info("Loading Flipkart data...")
    if os.path.exists(flipkart_path):
        df_flipkart = pd.read_csv(flipkart_path)
    else:
        logger.info(f"[WARNING] {flipkart_path} not found.")
        df_flipkart = pd.DataFrame()

    # Load Adler's Den data
    logger.info("Loading Adler's Den data...")
    if os.path.exists(adlers_path):
        adlers_df = pd.read_csv(adlers_path)
        logger.info(f"Adlers rows: {len(adlers_df)}")
        logger.info(adlers_df.head())
        
        # Rename 'weight' to 'weight_g' if necessary to align schemas:
        if 'weight' in adlers_df.columns and 'weight_g' not in adlers_df.columns:
            adlers_df = adlers_df.rename(columns={'weight': 'weight_g'})
            
        adlers_df["source"] = "adlers"
        # Ensure required columns exist
        for col in ["rating", "reviews", "weight_g"]:
            if col not in adlers_df.columns:
                adlers_df[col] = None
    else:
        logger.info(f"[WARNING] {adlers_path} not found.")
        adlers_df = pd.DataFrame()

    # Load Entisi data
    logger.info("Loading Entisi data...")
    if os.path.exists(entisi_path):
        df_entisi = pd.read_csv(entisi_path)
        if not df_entisi.empty:
            df_entisi["source"] = "entisi"
    else:
        logger.info(f"[WARNING] {entisi_path} not found.")
        df_entisi = pd.DataFrame()

    # Combine all datasets
    logger.info("\nMerging datasets...")
    # ignore_index=True resets the index, avoiding duplicates across original row numbers
    df_all = pd.concat([df_amazon, df_flipkart, adlers_df, df_entisi], ignore_index=True)

    # Ensure consistent schema
    schema = ["name", "price", "url", "source", "rating", "reviews", "weight_g"]

    for col in schema:
        if col not in df_all.columns:
            df_all[col] = None

    # Select only targeted schema fields and reorder
    df_final = df_all[schema]

    # Save output
    df_final.to_csv(output_path, index=False)

    # Summary Prints
    total_count = len(df_final)
    logger.info("\n" + "="*30)
    logger.info("Dataset Merge Complete!")
    logger.info("="*30)
    logger.info(f"Total count      : {total_count}")
    logger.info("\nCount per source:")
    for source, count in df_final["source"].value_counts().items():
        logger.info(f"  - {source:12s}: {count}")
    logger.info(f"\nSaved to: {output_path}")

if __name__ == "__main__":
    main()
