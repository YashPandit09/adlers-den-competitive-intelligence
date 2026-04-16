# 🧠 AI-Powered Competitive Intelligence Pipeline  
### (Adler’s Den – Part A)

---

## 📌 Overview

This project builds an **AI-driven competitive intelligence system** for Adler’s Den to analyze competitor products at a **product level (not just brand level)**.

The system extracts, cleans, and analyzes e-commerce product data to generate **actionable insights for pricing and product strategy**.

---

## 🎯 Objective

- Identify competitor products across e-commerce platforms  
- Extract structured product data  
- Clean and normalize data  
- Analyze pricing and product trends  
- Generate actionable business insights  

---

## ⚙️ System Architecture
Data Collection → Data Cleaning → Structuring → Analysis → Insights

---

## 🌐 Data Collection

- Source: **Entisi (Shopify-based competitor)**
- Extracted fields:
  - Product name  
  - Price  
  - URL  
  - Description  
  - Ingredients  
  - Weight  

### 🔍 Scraping Strategy
- Search page scraping (product listings)
- Product page scraping using **Shopify JSON API** /products/<handle>.json
- HTML fallback for non-Shopify sites

---

## 🧹 Data Processing

### Cleaning Steps:
- Text normalization (remove encoding issues, extra spaces)
- Price conversion to numeric format
- Weight normalization (grams)
- Missing value handling
- Deduplication (name + weight)

---

## 📊 Analysis

### Key Metrics:
- Price range
- Average price
- Price distribution (Low / Mid / Premium / Luxury)
- Price per gram (core comparison metric)

---

## 📈 Results

### 💰 Pricing Insights
- **Average Price:** ₹2985  
- **Price Range:** ₹1375 – ₹10990  
- Majority of products fall in **₹1000–₹3000 range**

---

### 📦 Market Distribution
- Low: 14  
- Mid: 4  
- Premium: 1  
- Luxury: 1  

👉 Market is heavily skewed toward **affordable gifting products**

---

### ⚖️ Price Per Gram
- **Average:** ₹7.12/g  
- Best value: ~₹4–₹5/g  
- Premium products: ~₹10/g  

---

### 🏆 Key Observations
- Smaller chocolate boxes dominate over large hampers  
- Clear pricing benchmark between **₹7–₹10 per gram**  
- Limited competition in premium segment (>₹6000)  

---

## 🤖 AI Insights Layer

Integrated **Google Gemini API** to generate business insights automatically.

- Converts structured data → human-readable insights  
- Includes fallback handling for API quota limits  

---

## 🧠 Business Value

This system helps:
- Identify optimal pricing ranges  
- Understand competitor positioning  
- Discover market gaps  
- Support product decision-making  

---

## 🚀 Tech Stack

- Python  
- BeautifulSoup (scraping)  
- Requests  
- Pandas  
- Google Gemini API  

---

## ⚠️ Limitations

- Uses proxy metrics (no actual sales data)  
- Limited dataset (MVP scope: ~20 products)  
- API rate limits for AI insights  

---

## 🏁 Conclusion

This project demonstrates how raw competitor data can be transformed into **actionable business intelligence using AI and data pipelines**.

---

## 👤 Author

**Yash Pandit**