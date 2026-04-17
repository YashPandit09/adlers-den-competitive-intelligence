import os
import pandas as pd

def main():
    # File paths
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    amazon_path = os.path.join(project_root, "data", "amazon_raw.csv")
    entisi_path = os.path.join(project_root, "data", "clean.csv")
    output_path = os.path.join(project_root, "data", "all_products.csv")

    # Load Amazon data
    print("Loading Amazon data...")
    if os.path.exists(amazon_path):
        df_amazon = pd.read_csv(amazon_path)
    else:
        print(f"[WARNING] {amazon_path} not found. Run amazon_scraper.py first.")
        df_amazon = pd.DataFrame()

    # Load Entisi data
    print("Loading Entisi data...")
    if os.path.exists(entisi_path):
        df_entisi = pd.read_csv(entisi_path)
        if not df_entisi.empty:
            df_entisi["source"] = "entisi"
    else:
        print(f"[WARNING] {entisi_path} not found.")
        df_entisi = pd.DataFrame()

    # Combine datasets
    df_all = pd.concat([df_entisi, df_amazon], ignore_index=True)

    # Ensure consistent schema
    schema = ["name", "price", "url", "source", "rating", "reviews", "weight_g"]
    
    for col in schema:
        if col not in df_all.columns:
            df_all[col] = None
            
    # Select only targeting schema fields and order them
    df_final = df_all[schema]
    
    # Save the output
    df_final.to_csv(output_path, index=False)
    
    # Summary
    print("\n" + "="*30)
    print("Dataset Merge Complete!")
    print("="*30)
    print(f"Total count      : {len(df_final)}")
    print("\nCount per source :")
    
    if "source" in df_final.columns:
        source_counts = df_final["source"].value_counts()
        for src, count in source_counts.items():
            print(f"  - {src.ljust(8)} : {count}")

if __name__ == "__main__":
    main()
