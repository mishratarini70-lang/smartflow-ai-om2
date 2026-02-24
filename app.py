import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="AI Inventory Simulator", layout="wide")

# =====================================================
# HEADER
# =====================================================

st.markdown("""
# 📦 AI Inventory Simulator  
### OM-II Decision Support Tool | Optimize Inventory & Profitability
""")

st.divider()

# =====================================================
# PARAMETERS
# =====================================================

CATEGORIES = {
    "Smartphones": {"forecast": 50000, "volatility": 0.20, "margin": 3000},
    "Laptops": {"forecast": 15000, "volatility": 0.30, "margin": 7000},
    "Apparel & Fashion": {"forecast": 120000, "volatility": 0.40, "margin": 600},
}

HOLDING_COST = 200
STOCKOUT_COST = 1500

# =====================================================
# SESSION STATE
# =====================================================

if "results" not in st.session_state:
    st.session_state.results = {}

# =====================================================
# MAIN LAYOUT
# =====================================================

left, right = st.columns([1, 2])

# =====================================================
# LEFT PANEL – CATEGORY DECISIONS
# =====================================================

with left:
    st.markdown("## Category Decisions")
    st.write("Review AI forecast and set order quantity.")

    orders = {}

    for category, data in CATEGORIES.items():
        st.markdown(f"### {category}")
        st.caption(f"AI Forecast: {data['forecast']:,} | Volatility: {int(data['volatility']*100)}% | Margin: ₹{data['margin']:,}")

        order_qty = st.slider(
            f"Order Quantity – {category}",
            min_value=0,
            max_value=data["forecast"] * 2,
            value=data["forecast"],
            key=f"order_{category}"
        )

        st.write(f"Order: **{order_qty:,} units**")
        st.divider()

        orders[category] = order_qty

    run_sim = st.button("🚀 Run Simulation")

# =====================================================
# RIGHT PANEL – RESULTS
# =====================================================

with right:

    if run_sim:

        total_profit = 0
        total_holding = 0
        total_stockout = 0

        results = []

        for category, data in CATEGORIES.items():

            demand = int(np.random.normal(
                data["forecast"],
                data["forecast"] * data["volatility"]
            ))

            order = orders[category]

            sold = min(order, demand)
            leftover = max(order - demand, 0)
            stockout = max(demand - order, 0)

            profit = sold * data["margin"]
            holding_cost = leftover * HOLDING_COST
            stockout_cost = stockout * STOCKOUT_COST

            net_profit = profit - holding_cost - stockout_cost

            service_level = sold / demand if demand > 0 else 1

            total_profit += net_profit
            total_holding += holding_cost
            total_stockout += stockout_cost

            results.append({
                "Category": category,
                "Service Level": round(service_level * 100, 1),
                "Leftover": leftover,
                "Profit": net_profit
            })

        # =====================================================
        # KPI CARDS
        # =====================================================

        col1, col2, col3 = st.columns(3)

        col1.metric("Net Profit", f"₹{total_profit/1e7:.2f} Cr")
        col2.metric("Stockout Cost", f"₹{total_stockout/1e7:.2f} Cr")
        col3.metric("Holding Cost", f"₹{total_holding/1e7:.2f} Cr")

        st.divider()

        # =====================================================
        # PERFORMANCE TABLE
        # =====================================================

        df = pd.DataFrame(results)

        st.markdown("## Category Performance Breakdown")
        st.dataframe(df, use_container_width=True)

        # =====================================================
        # INSIGHT BOX
        # =====================================================

        st.markdown("### 📘 Managerial Insight (OM Concept)")
        st.info("""
        This simulation models the **Newsvendor Problem**.
        AI forecast gives expected demand, but volatility affects optimal order quantity.
        Ordering exactly the forecast is rarely optimal.
        Managers must balance underage cost (stockout) vs overage cost (holding).
        """)
