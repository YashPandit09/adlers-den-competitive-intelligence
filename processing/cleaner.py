import pandas as pd


def clean_text(text):
    if pd.isna(text):
        return None

    text = str(text)

    # remove weird encoding characters
    text = text.encode("ascii", "ignore").decode()

    # remove extra spaces and newlines
    text = " ".join(text.split())

    return text


def clean_data(input_path="data/raw.csv", output_path="data/clean.csv"):
    df = pd.read_csv(input_path)

    # Clean text fields
    df["description"] = df["description"].apply(clean_text)
    df["ingredients"] = df["ingredients"].apply(clean_text)

    # Ensure price is float
    df["price"] = pd.to_numeric(df["price"], errors="coerce")

    # Ensure weight is float
    df["weight_g"] = pd.to_numeric(df["weight_g"], errors="coerce")
    df["weight_g"] = df["weight_g"].apply(
    lambda x: x if pd.notna(x) and x >= 100 else None
    )

    # Drop rows with no price
    df = df[df["price"].notna()]

    # Optional: drop duplicates by name + weight
    df = df.drop_duplicates(subset=["name", "weight_g"])

    # Save clean data
    df.to_csv(output_path, index=False)

    print("Cleaned data saved to:", output_path)
    print(df.head())

    return df


if __name__ == "__main__":
    clean_data()