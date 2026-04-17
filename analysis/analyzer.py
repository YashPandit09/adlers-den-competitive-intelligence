import pandas as pd
import numpy as np
import google.genai as genai

import logging
import os

os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    filename="logs/app.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


GEMINI_API_KEY = "AQ.Ab8RN6KHhQTpoL4ekNPEVR2_7f_R3xZtlzkggnxQ6kUFi6QLmQ"


def analyze_data():
    df = pd.read_csv("data/clean.csv")

    logger.info("\n--- BASIC STATS ---")
    logger.info(f"Total products: {len(df)}")
    logger.info(f"Price range: {df['price'].min()} - {df['price'].max()}")
    logger.info(f"Average price: {round(df['price'].mean(), 2)}")

    # Price buckets
    bins = [0, 3000, 6000, 10000, 20000]
    labels = ["Low", "Mid", "Premium", "Luxury"]

    df["price_category"] = pd.cut(df["price"], bins=bins, labels=labels)

    logger.info("\n--- PRICE DISTRIBUTION ---")
    logger.info(df["price_category"].value_counts())

    # Popularity score (mock for now since no reviews)
    df["score"] = df["price"] / df["weight_g"]

    logger.info("\n--- TOP PRODUCTS (VALUE) ---")
    logger.info(df.sort_values(by="score", ascending=False)[["name", "price", "weight_g"]].head(5))

    logger.info("\n--- PRICE PER GRAM ---")
    df["price_per_gram"] = df["price"] / df["weight_g"]
    df = df[df["price_per_gram"].notna()]
    logger.info(f"{"Average:", round(df["price_per_gram"].mean(), 2))

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
        logger.info("\n--- AI GENERATED INSIGHTS ---\n")
        logger.info(response.text)
    except Exception as e:
        logger.info(f"\n[AI Insights skipped] {e}")

def generate_recommendations(df):
    avg_price = df["price"].mean()

    logger.info("\n--- RECOMMENDATIONS ---\n")

    if avg_price < 3000:
        logger.info("- Introduce products in Rs.1500-Rs.2500 range to target high-demand segment")

    best_value = df.sort_values(by="price_per_gram").head(3)
    logger.info("- Best value products (lowest Rs./g):")
    for _, row in best_value.iterrows():
        logger.info(f"    {row['name']} : Rs.{round(row['price_per_gram'], 2)}/g")

    logger.info("- Focus on products with price per gram around Rs.7-Rs.10 for competitive positioning")

    logger.info("- Consider launching premium hampers (>Rs.6000) due to low competition")

def value_analysis(df):
    df["price_per_gram"] = df["price"] / df["weight_g"]

    logger.info("\n--- VALUE INSIGHTS ---\n")

    logger.info("Cheapest products (best value):")
    logger.info(f"{df.sort_values(by="price_per_gram")[["name", "price_per_gram"]].head(3))

    logger.info("\nMost expensive per gram (premium):")
    logger.info(f"{df.sort_values(by="price_per_gram", ascending=False)[["name", "price_per_gram"]].head(3))



if __name__ == "__main__":
    df = analyze_data()
    generate_ai_insights(df)
    generate_recommendations(df)
    value_analysis(df)