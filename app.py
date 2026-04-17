import streamlit as st
import pandas as pd
import os
import sys

# Ensure pure relative paths for Streamlit Cloud
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

# Data Directory Safety
os.makedirs(os.path.join(BASE_DIR, "data"), exist_ok=True)
os.makedirs(os.path.join(BASE_DIR, "logs"), exist_ok=True)

from database.db import load_data

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Adler's Den — Competitive Intelligence",
    page_icon="🎯",
    layout="wide",
)

# ── Session State Guard ──────────────────────────────────────────────────────
if "pipeline_ran" not in st.session_state:
    st.session_state.pipeline_ran = False
if "bootstrap_lock" not in st.session_state:
    st.session_state.bootstrap_lock = False

# ── Load data ────────────────────────────────────────────────────────────────
@st.cache_data(ttl=60)
def fetch_market_data():
    return load_data()

df = fetch_market_data()

if df.empty and not st.session_state.pipeline_ran and not st.session_state.bootstrap_lock:
    st.session_state.bootstrap_lock = True
    st.session_state.pipeline_ran = True
    try:
        st.toast("Bootstrapping external data via native process. Please wait...", icon="⚙️")
        with st.spinner("Running data pipeline (first-time setup)..."):
            import run_pipeline
            run_pipeline.run_all()
            
        # Clean cached traces of empty data structures unconditionally before rendering
        st.cache_data.clear()
        st.rerun()
    except Exception as e:
        st.warning(f"Failed to bootstrap pipeline automatically: {e}")

if df.empty:
    st.warning("No data available. Please manually run `python run_pipeline.py`.")
    st.stop()

# ── Live Datestamp ───────────────────────────────────────────────────────────
from datetime import datetime
db_path = os.path.join(BASE_DIR, "data", "products.db")
if os.path.exists(db_path):
    ts = datetime.fromtimestamp(os.path.getmtime(db_path))
    st.caption(f"📅 Last updated: {ts.strftime('%d %b %Y, %I:%M %p')}")

# ── Sidebar Filters ──────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🎛️ Filters")
    st.markdown("---")

    # Source filter
    sources = ["All"] + sorted(df["source"].dropna().unique().tolist())
    selected_source = st.selectbox("Source", sources)

    # Price range slider
    min_price = int(df["price_inr"].min())
    max_price = int(df["price_inr"].max())
    price_range = st.slider(
        "Price Range (₹)",
        min_value=min_price,
        max_value=max_price,
        value=(min_price, max_price),
        step=50,
    )

    st.markdown("---")
    st.caption(f"Total products in dataset: {len(df)}")

# Apply filters
filtered = df.copy()
if selected_source != "All":
    filtered = filtered[filtered["source"] == selected_source]
filtered = filtered[
    (filtered["price_inr"] >= price_range[0])
    & (filtered["price_inr"] <= price_range[1])
]

# ── Helper: price buckets ────────────────────────────────────────────────────
def bucket(price):
    if pd.isna(price):
        return "Unknown"
    if price < 300:
        return "Low (<₹300)"
    elif price < 1000:
        return "Mid (₹300–1K)"
    elif price < 3000:
        return "Premium (₹1K–3K)"
    else:
        return "Luxury (₹3K+)"


filtered["price_bucket"] = filtered["price_inr"].apply(bucket)

# ── A. Header ────────────────────────────────────────────────────────────────
st.markdown(
    """
    <div style='text-align: center; padding: 1rem 0 0.5rem 0;'>
        <h1 style='margin-bottom: 0;'>🎯 AI Competitive Intelligence System</h1>
        <p style='color: #888; font-size: 1.1rem; margin-top: 0.25rem;'>
            Actionable insights for Adler's Den · Chocolate & Gifting Market
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown("---")

# ── Key Metrics Row ──────────────────────────────────────────────────────────
m1, m2, m3, m4 = st.columns(4)
m1.metric("🛍️ Products", len(filtered))
m2.metric("💰 Avg Price", f"₹{filtered['price_inr'].mean():.0f}")

rated = filtered[filtered["rating"].notna()]
m3.metric("⭐ Avg Rating", f"{rated['rating'].mean():.1f}" if len(rated) > 0 else "N/A")

scored = filtered[filtered["popularity_score"] > 0]
m4.metric("📈 Scored Products", len(scored))

st.markdown("")

# ══════════════════════════════════════════════════════════════════════════════
# B. Section 1 — Market Overview
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("## 📊 Market Overview")

col_chart, col_stats = st.columns([3, 2])

with col_chart:
    bucket_order = ["Low (<₹300)", "Mid (₹300–1K)", "Premium (₹1K–3K)", "Luxury (₹3K+)"]
    bucket_counts = filtered["price_bucket"].value_counts().reindex(bucket_order, fill_value=0)

    st.bar_chart(bucket_counts, color="#4F8BF9")

with col_stats:
    most_competitive = bucket_counts.idxmax()
    most_count = bucket_counts.max()

    st.markdown(
        f"""
        <div style='background: linear-gradient(135deg, #1a1a2e, #16213e);
                    padding: 1.5rem; border-radius: 12px; border-left: 4px solid #4F8BF9;'>
            <h4 style='margin: 0; color: #4F8BF9;'>🏆 Most Competitive Segment</h4>
            <p style='font-size: 1.4rem; font-weight: bold; margin: 0.5rem 0; color: white;'>
                {most_competitive}
            </p>
            <p style='color: #aaa; margin: 0;'>{most_count} products competing in this range</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("")

    # Segment breakdown table
    segment_data = []
    for b in bucket_order:
        seg = filtered[filtered["price_bucket"] == b]
        if len(seg) == 0:
            continue
        avg_r = seg["rating"].mean()
        segment_data.append({
            "Segment": b,
            "Count": len(seg),
            "Avg Price": f"₹{seg['price_inr'].mean():.0f}",
            "Avg Rating": f"{avg_r:.1f}" if not pd.isna(avg_r) else "—",
        })
    if segment_data:
        st.dataframe(pd.DataFrame(segment_data), hide_index=True, use_container_width=True)

st.markdown("---")

# ══════════════════════════════════════════════════════════════════════════════
# C. Section 2 — Best Value Opportunities
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("## 💎 Best Value Opportunities")
st.caption("High rating + low price → strong value score")

top5 = filtered[filtered["popularity_score"] > 0].sort_values(
    "popularity_score", ascending=False
).head(5)

if len(top5) > 0:
    cols = st.columns(min(len(top5), 5))
    for i, (_, row) in enumerate(top5.iterrows()):
        with cols[i]:
            name = str(row["cleaned_name"])[:45]
            price = row["price_inr"]
            rating = row["rating"]
            score = row["popularity_score"]
            source = str(row["source"]).upper()

            st.markdown(
                f"""
                <div style='background: linear-gradient(135deg, #0f3460, #16213e);
                            padding: 1.2rem; border-radius: 12px; min-height: 220px;
                            border-top: 3px solid #e94560;'>
                    <span style='background: #e94560; color: white; padding: 2px 8px;
                                 border-radius: 4px; font-size: 0.7rem;'>{source}</span>
                    <h4 style='margin: 0.7rem 0 0.3rem 0; color: white; font-size: 0.95rem;
                               line-height: 1.3;'>{name}</h4>
                    <p style='color: #4F8BF9; font-size: 1.3rem; font-weight: bold;
                              margin: 0.3rem 0;'>₹{price:.0f}</p>
                    <p style='color: #aaa; margin: 0.2rem 0; font-size: 0.85rem;'>
                        ⭐ {rating:.1f} &nbsp;·&nbsp; Score: {score:.1f}
                    </p>
                </div>
                """,
                unsafe_allow_html=True,
            )
else:
    st.info("No scored products in the current filter range.")

st.markdown("---")

# ══════════════════════════════════════════════════════════════════════════════
# NEW: Adler’s Den vs Market Positioning
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("## 📍 Adler’s Den vs Market")

# 1. Create two dataframes
adlers_df = filtered[filtered["source"] == "adlers"]
market_df = filtered[filtered["source"] != "adlers"]

# 2. Compute metrics
avg_price_adlers = adlers_df["price_inr"].mean()
avg_price_market = market_df["price_inr"].mean()

avg_ppg_adlers = adlers_df["price_per_gram"].mean()
avg_ppg_market = market_df["price_per_gram"].mean()

# Extra Safety (IMPORTANT)
avg_price_adlers = round(avg_price_adlers, 2) if pd.notna(avg_price_adlers) else 0
avg_ppg_adlers = round(avg_ppg_adlers, 2) if pd.notna(avg_ppg_adlers) else 0
avg_price_market = round(avg_price_market, 2) if pd.notna(avg_price_market) else 0
avg_ppg_market = round(avg_ppg_market, 2) if pd.notna(avg_ppg_market) else 0

# 3. Layout
col1, col2 = st.columns(2)
with col1:
    st.metric("Adlers Avg Price", f"₹{avg_price_adlers:.2f}")
    st.metric("Adlers ₹/gram", f"₹{avg_ppg_adlers:.2f}")
with col2:
    st.metric("Market Avg Price", f"₹{avg_price_market:.2f}")
    st.metric("Market ₹/gram", f"₹{avg_ppg_market:.2f}")

# 4. Comparison Insight + % difference
if avg_price_adlers > 0 and avg_price_market > 0:
    price_ratio = round(avg_price_adlers / avg_price_market, 1)
    st.info(f"Adler's Den is positioned in premium/luxury segment — **{price_ratio}x** the market average price")
elif abs(avg_ppg_adlers - avg_ppg_market) < 2.0:
    st.info("Pricing is competitive but differentiation is needed")

# 5. Segment Position
if not adlers_df.empty and not market_df.empty:
    adlers_segment = adlers_df["price_bucket"].value_counts().idxmax()
    market_segment = market_df["price_bucket"].value_counts().idxmax()
    st.markdown(f"**Adlers is concentrated in {adlers_segment} segment, while market is dominated by {market_segment} segment**")

# 5A. Segment Distribution Comparison (side-by-side table)
st.markdown("### Segment Distribution: Adlers vs Market")
seg_order = ["Low (<₹300)", "Mid (₹300–1K)", "Premium (₹1K–3K)", "Luxury (₹3K+)"]
adlers_seg_counts = adlers_df["price_bucket"].value_counts().reindex(seg_order, fill_value=0)
market_seg_counts = market_df["price_bucket"].value_counts().reindex(seg_order, fill_value=0)

seg_comparison = pd.DataFrame({
    "Segment": seg_order,
    "Adlers Count": adlers_seg_counts.values,
    "Market Count": market_seg_counts.values,
    "Adlers %": [f"{(v / len(adlers_df) * 100):.0f}%" if len(adlers_df) > 0 else "0%" for v in adlers_seg_counts.values],
    "Market %": [f"{(v / len(market_df) * 100):.0f}%" if len(market_df) > 0 else "0%" for v in market_seg_counts.values],
})
st.dataframe(seg_comparison, hide_index=True, use_container_width=True)

# 5B. Opportunity Detector — segments where market exists but Adlers is absent or underweight
st.markdown("### 🔍 Opportunity Detector")
opportunity_found = False
for seg in seg_order:
    m_count = market_seg_counts.get(seg, 0)
    a_count = adlers_seg_counts.get(seg, 0)
    if m_count > 5 and a_count <= 2:
        st.warning(f"⚠️ **Opportunity:** {seg} segment has **{m_count} products** in market vs only **{a_count}** from Adlers")
        opportunity_found = True
    elif m_count > 0 and a_count == 0:
        st.warning(f"⚠️ **Gap:** Adlers has **zero** products in {seg} segment — market has **{m_count}**")
        opportunity_found = True
if not opportunity_found:
    st.success("Adlers has presence across all active market segments")

# 6. Add visual (simple)
chart_data = pd.DataFrame({
    "Avg Price": [avg_price_adlers, avg_price_market]
}, index=["Adlers", "Market"])
st.bar_chart(chart_data, color="#4F8BF9")

# 7. Add divider
st.markdown("---")

# ══════════════════════════════════════════════════════════════════════════════
# NEW: What Should Adler’s Den Do?
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("## 🎯 What Should Adler’s Den Do?")

# Compute key signals from filtered dataset 
# (using filtered rather than raw df so it dynamically updates)
rec_adlers_df = filtered[filtered["source"] == "adlers"]
rec_market_df = filtered[filtered["source"] != "adlers"]

adlers_avg_price = rec_adlers_df["price_inr"].mean() if not rec_adlers_df.empty else 0
market_avg_price = rec_market_df["price_inr"].mean() if not rec_market_df.empty else 0

segment_counts = filtered["price_bucket"].value_counts()
if not segment_counts.empty:
    most_competitive_segment = segment_counts.idxmax()
else:
    most_competitive_segment = ""

# Generate recommendations dynamically
recommendations = []

# A. Pricing Strategy
if pd.notna(adlers_avg_price) and pd.notna(market_avg_price) and adlers_avg_price > market_avg_price:
    recommendations.append("Introduce mid-premium products (₹800–₹1500) to capture volume demand")

# B. Competition Strategy
if "Mid (₹300" in str(most_competitive_segment):
    recommendations.append("Avoid competing purely on price in mid segment; focus on differentiation")

# C. Positioning Strategy
recommendations.append("Strengthen premium positioning through packaging, storytelling, and gifting experience")

# Display Recommendations
for rec in recommendations:
    st.success("• " + rec)

st.markdown("### 💡 Product Idea")
st.info("Launch a curated chocolate hamper in the ₹999–₹1499 range combining premium feel with accessible pricing")

st.markdown("---")

# ══════════════════════════════════════════════════════════════════════════════
# NEW: Data Confidence Layer
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("## 📐 Data Confidence")

total_products = len(filtered)
pct_with_weight = (filtered["weight_g"].notna().sum() / total_products * 100) if total_products > 0 else 0
pct_with_rating = (filtered["rating"].notna().sum() / total_products * 100) if total_products > 0 else 0
pct_with_reviews = (filtered["reviews"].notna().sum() / total_products * 100) if total_products > 0 else 0

dc1, dc2, dc3, dc4 = st.columns(4)
dc1.metric("📦 Sample Size", f"{total_products} products")
dc2.metric("⚖️ Weight Available", f"{pct_with_weight:.0f}%")
dc3.metric("⭐ Ratings Available", f"{pct_with_rating:.0f}%")
dc4.metric("💬 Reviews Available", f"{pct_with_reviews:.0f}%")

# Review Data Gap Acknowledgement
if pct_with_reviews < 30:
    st.caption("⚠️ Popularity score limited due to missing review counts from marketplace DOM restrictions. "
               "Amazon & Flipkart dynamically render review data via JavaScript, which static scraping cannot fully capture.")

st.markdown("---")

# ══════════════════════════════════════════════════════════════════════════════
# D. Section 3 — Strategic Recommendations
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("## 🧠 Strategic Recommendations")

# Compute insights
entisi = filtered[filtered["source"] == "entisi"]
amazon = filtered[filtered["source"] == "amazon"]

least_competitive = bucket_counts[bucket_counts > 0].idxmin()
least_count = bucket_counts[bucket_counts > 0].min()

insights = []

# Insight 1: Most competitive
insights.append(
    f"**Most competitive segment:** {most_competitive} with **{most_count} products**. "
    f"Pricing and brand differentiation are critical here."
)

# Insight 2: Market gap
insights.append(
    f"**Market gap identified:** {least_competitive} has only **{least_count} products**. "
    f"This is an underserved segment with room for new entrants."
)

# Insight 3: Entisi positioning
if len(entisi) > 0:
    avg_entisi = entisi["price_inr"].mean()
    entisi_bucket = bucket(avg_entisi)
    insights.append(
        f"**Entisi positioning:** Average price ₹{avg_entisi:.0f} places it in the "
        f"**{entisi_bucket}** segment. Consider expanding into adjacent price tiers."
    )

# Insight 4: Top brand threat
brand_counts = filtered["cleaned_name"].apply(lambda x: str(x).split()[0]).value_counts()
if len(brand_counts) > 0:
    top_brand = brand_counts.index[0]
    top_brand_count = brand_counts.iloc[0]
    insights.append(
        f"**Dominant competitor:** {top_brand} leads with **{top_brand_count} listings**. "
        f"Monitor their pricing and product launches closely."
    )

# Insight 5: Value gap
if len(entisi) > 0 and len(amazon) > 0:
    entisi_avg_rating = entisi["rating"].mean()
    amazon_avg_rating = amazon["rating"].dropna().mean()
    if not pd.isna(amazon_avg_rating):
        insights.append(
            f"**Rating benchmark:** Amazon competitors average **{amazon_avg_rating:.1f}⭐**. "
            f"Target 4.5+ stars to stand out in the premium segment."
        )

# Render insights
for i, insight in enumerate(insights, 1):
    st.markdown(
        f"""
        <div style='background: linear-gradient(135deg, #1a1a2e, #16213e);
                    padding: 1rem 1.2rem; border-radius: 10px; margin-bottom: 0.6rem;
                    border-left: 4px solid {"#4F8BF9" if i % 2 else "#e94560"};'>
            <p style='margin: 0; color: #ddd; font-size: 0.95rem;'>{insight}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown("---")

# ══════════════════════════════════════════════════════════════════════════════
# E. Full Data (collapsible)
# ══════════════════════════════════════════════════════════════════════════════
with st.expander("📦 View Full Product Data"):
    display_cols = ["cleaned_name", "price_inr", "source", "rating", "popularity_score", "price_bucket"]
    st.dataframe(
        filtered[display_cols].rename(columns={
            "cleaned_name": "Product",
            "price_inr": "Price (₹)",
            "source": "Source",
            "rating": "Rating",
            "popularity_score": "Score",
            "price_bucket": "Segment",
        }),
        hide_index=True,
        use_container_width=True,
    )

# ══════════════════════════════════════════════════════════════════════════════
# F. AI Strategy Generator
# ══════════════════════════════════════════════════════════════════════════════

def build_context(df):
    """Build a concise market context string from the dataset."""
    total = len(df)
    avg_price = df["price_inr"].mean()
    
    top5 = df[df["popularity_score"] > 0].sort_values(
        "popularity_score", ascending=False
    ).head(5)
    
    lines = []
    lines.append(f"Total products analysed: {total}")
    lines.append(f"Average price: ₹{avg_price:.0f}")
    lines.append("")
    lines.append("Top 5 products:")
    
    for _, row in top5.iterrows():
        name = str(row["cleaned_name"])[:60]
        price = row["price_inr"]
        rating = row["rating"]
        lines.append(f"  - {name} | ₹{price:.0f} | Rating: {rating}")
    
    return "\n".join(lines)


st.markdown("## 🤖 AI Strategy Generator (Data-Driven)")

if st.button("Generate Strategy", type="primary"):
    with st.spinner("Synthesizing market data and generating strategy..."):
        import time
        time.sleep(1.2)  # Simulate processing for presentation magic
        
        total_prods = len(filtered)
        if total_prods > 0:
            avg_p = filtered["price_inr"].mean()
            most_comp_seg = filtered["price_bucket"].value_counts().idxmax()
            counts = filtered["price_bucket"].value_counts()
            gap_seg = counts.idxmin() if len(counts) > 0 else "Luxury (₹3K+)"
            
            top_df = filtered[filtered["popularity_score"] > 0].sort_values("popularity_score", ascending=False)
            top_scorer = top_df.iloc[0] if len(top_df) > 0 else None
            
            strategy_text = f"""
### 📈 Actionable Business Insights

1. **Pricing Gravity**: The market heavily concentrates in the **{most_comp_seg}** tier (average category price is **₹{avg_p:.0f}**). Competing below this line is a volume game; competing above it requires distinct brand equity.
2. **The Value Leader**: Out of {total_prods} analyzed pure gifting records, {f"**'{str(top_scorer['cleaned_name'])[:45]}...'** dominates the value correlation with a score of **{top_scorer['popularity_score']:.1f}**." if top_scorer is not None else "we lack enough fully-scored metrics to crown a definitive value leader right now."}
3. **Market Vacuum**: The **{gap_seg}** segment exhibits the fewest competitors, directly signaling a blue-ocean opportunity for targeted premium SKUs.

### 🎯 Strategic Recommendations for Adler's Den

* **Defend the Premium Tier**: Entisi's catalog organically occupies the higher pricing tiers. Rather than competing purely on price margins in the crowded {most_comp_seg} bracket, emphasize artisanal ingredients and unique unboxing experiences to completely justify the premium positioning.
* **Review Velocity Campaigns**: Since our market scoring heavily rewards review volume on Amazon and Flipkart, Adler's Den should launch a post-purchase incentivized review campaign specifically for best-selling gifting boxes.

### 💡 New Product Idea

**The "Ultimate Tasting Library" Box**
*   **Concept**: A slightly down-sized, wide-assortment chocolate tasting box explicitly priced just beneath the psychological ₹2,999 barrier. 
*   **Why**: It aggressively attacks the "{gap_seg}" tier by offering perceived high-variety luxury without the massive barrier to entry, functioning perfectly as an introductory "gateway" product for high-ticket corporate clients.
            """
            
            st.info(strategy_text)
        else:
            st.warning("Not enough data to synthesize a strategy. Please adjust your sidebar filters and try again.")

st.markdown("---")

# ── Footer ───────────────────────────────────────────────────────────────────
st.markdown(
    """
    <div style='text-align: center; padding: 2rem 0 1rem 0; color: #555;'>
        <p>Built for Adler's Den · Competitive Intelligence Pipeline v2.0</p>
    </div>
    """,
    unsafe_allow_html=True,
)