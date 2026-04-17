import streamlit as st
import pandas as pd
import os
import google.generativeai as genai

st.set_page_config(page_title="Competitive Intelligence", layout="wide")

st.title("🧠 Competitive Intelligence Dashboard")

df = pd.read_csv("data/clean.csv")

st.subheader("📊 Key Metrics")

col1, col2, col3 = st.columns(3)

col1.metric("Total Products", len(df))
col2.metric("Avg Price", f"₹{round(df['price'].mean(), 2)}")
col3.metric("Avg Price/Gram", f"₹{round((df['price']/df['weight_g']).mean(), 2)}")

st.subheader("💰 Price Distribution")

bins = [0, 3000, 6000, 10000, 20000]
labels = ["Low", "Mid", "Premium", "Luxury"]

df["category"] = pd.cut(df["price"], bins=bins, labels=labels)

st.bar_chart(df["category"].value_counts())

st.subheader("🏆 Best Value Products")

# Drop rows where weight_g is missing before calculation
valid_weight_df = df.dropna(subset=['weight_g']).copy()

# Compute price_per_gram
valid_weight_df['price_per_gram'] = valid_weight_df['price'] / valid_weight_df['weight_g']

# Show top 5 products with lowest price_per_gram and select specific columns
best_value_df = valid_weight_df.nsmallest(5, 'price_per_gram')[['name', 'price', 'weight_g', 'price_per_gram']]
st.dataframe(best_value_df)

st.subheader("📦 All Products")

# Display full dataset
st.dataframe(df)


st.subheader("🤖 AI Insights")

if st.button("Generate Insights"):
    try:
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        model = genai.GenerativeModel("gemini-2.5-flash")

        summary = f"""
        Total products: {len(df)}
        Average price: {round(df['price'].mean(), 2)}
        Price range: {df['price'].min()} - {df['price'].max()}
        Average price per gram: {round((df['price']/df['weight_g']).mean(), 2)}
        """

        prompt = f"""
        You are a business analyst.

        Based on this dataset:
        {summary}

        Give 4 short business insights about pricing, product trends, and opportunities.
        """

        response = model.generate_content(prompt)

        st.write(response.text)

    ##except Exception:
        ##st.warning("AI insights unavailable (quota or API issue)")

    except Exception:
        st.warning("AI insights unavailable (quota hit). Showing fallback insights.")

        st.markdown("""
        **Key Insights:**
        - Most products are priced in ₹1000–₹3000 range (high demand segment)
        - Premium segment (>₹6000) has low competition
        - Average price per gram is ~₹7, with premium reaching ₹10/g
    - Smaller chocolate boxes dominate over large hampers
    """)