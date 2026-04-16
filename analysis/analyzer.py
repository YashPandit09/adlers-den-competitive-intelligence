import pandas as pd
import numpy as np
import google.genai as genai

GEMINI_API_KEY = "AQ.Ab8RN6KHhQTpoL4ekNPEVR2_7f_R3xZtlzkggnxQ6kUFi6QLmQ"


def analyze_data():
    df = pd.read_csv("data/clean.csv")

    print("\n--- BASIC STATS ---")
    print("Total products:", len(df))
    print("Price range:", df["price"].min(), "-", df["price"].max())
    print("Average price:", round(df["price"].mean(), 2))

    # Price buckets
    bins = [0, 3000, 6000, 10000, 20000]
    labels = ["Low", "Mid", "Premium", "Luxury"]

    df["price_category"] = pd.cut(df["price"], bins=bins, labels=labels)

    print("\n--- PRICE DISTRIBUTION ---")
    print(df["price_category"].value_counts())

    # Popularity score (mock for now since no reviews)
    df["score"] = df["price"] / df["weight_g"]

    print("\n--- TOP PRODUCTS (VALUE) ---")
    print(df.sort_values(by="score", ascending=False)[["name", "price", "weight_g"]].head(5))

    print("\n--- PRICE PER GRAM ---")
    df["price_per_gram"] = df["price"] / df["weight_g"]
    df = df[df["price_per_gram"].notna()]
    print("Average:", round(df["price_per_gram"].mean(), 2))

    return df


def generate_ai_insights(df):
    client = genai.Client(api_key=GEMINI_API_KEY)

    summary = f"""
    Total products: {len(df)}
    Average price: {round(df['price'].mean(), 2)}
    Price range: {df['price'].min()} - {df['price'].max()}
    Average price per gram: {round((df['price']/df['weight_g']).mean(), 2)}
    """

    prompt = f"""You are a business analyst.

Based on this competitor product dataset:
{summary}

Generate 4 short, practical insights about:
- Pricing trends
- Product strategy
- Market opportunities

Keep each insight to 1-2 sentences."""

    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt,
        )
        print("\n--- AI GENERATED INSIGHTS ---\n")
        print(response.text)
    except Exception as e:
        print(f"\n[AI Insights skipped] {e}")

def generate_recommendations(df):
    avg_price = df["price"].mean()

    print("\n--- RECOMMENDATIONS ---\n")

    if avg_price < 3000:
        print("- Introduce products in Rs.1500-Rs.2500 range to target high-demand segment")

    df.sort_values(by="price_per_gram").head(3)

    print("- Focus on products with price per gram around Rs.7-Rs.10 for competitive positioning")

    print("- Consider launching premium hampers (>Rs.6000) due to low competition")

def value_analysis(df):
    df["price_per_gram"] = df["price"] / df["weight_g"]

    print("\n--- VALUE INSIGHTS ---\n")

    print("Cheapest products (best value):")
    print(df.sort_values(by="price_per_gram")[["name", "price_per_gram"]].head(3))

    print("\nMost expensive per gram (premium):")
    print(df.sort_values(by="price_per_gram", ascending=False)[["name", "price_per_gram"]].head(3))

def price_distribution(df):
    bins = [0, 3000, 6000, 10000, 20000]
    labels = ["Low", "Mid", "Premium", "Luxury"]

    df["price_category"] = pd.cut(df["price"], bins=bins, labels=labels)

    print("\n--- PRICE DISTRIBUTION ---")
    print(df["price_category"].value_counts())

    # Optional: plot this later


if __name__ == "__main__":
    df = analyze_data()
    generate_ai_insights(df)
    generate_recommendations(df)
    value_analysis(df)
    price_distribution(df)