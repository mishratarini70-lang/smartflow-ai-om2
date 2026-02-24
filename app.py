import streamlit as st
import pandas as pd
import numpy as np
import math

st.set_page_config(page_title="AI Production Simulator", layout="wide")

# =====================================================
# HEADER
# =====================================================

st.markdown("""
# 🏭 AI Production & Inventory Simulator  
### OM-II Decision Support Tool | Multi-Stage Manufacturing Optimization
""")

st.divider()

# =====================================================
# CONSTANTS
# =====================================================

BASE_MONTHLY_DEMAND = 10000
AVAILABLE_HOURS_MONTH = 160
UNITS_PER_MACHINE_PER_HOUR = 7

BODY_FACTOR = 5
PAINT_FACTOR = 7
ENGINE_FACTOR = 3
FINAL_FACTOR = 4

LEAD_TIME_DAYS = 15
ORDERING_COST = 100000
LOT_SIZE = 10000

RAW_MATERIAL_COST = 500
HOLDING_COST_RAW_DAILY = 10  # ₹10 per unit per day
HOLDING_COST_RAW_ANNUAL = HOLDING_COST_RAW_DAILY * 365

SHORTAGE_COST = 200
SELLING_PRICE = 3000

# =====================================================
# SESSION STATE INIT
# =====================================================

defaults = {
    "monthly_demand": BASE_MONTHLY_DEMAND,
    "previous_year_demand": BASE_MONTHLY_DEMAND * 12,
    "raw_inventory": 50000,
    "raw_pipeline": [],
    "wip_body": 0,
    "wip_paint": 0,
    "wip_engine": 0,
    "fg_inventory": 0
}

for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# =====================================================
# LAYOUT
# =====================================================

left, right = st.columns([1, 2])

# =====================================================
# LEFT PANEL – DECISIONS
# =====================================================

with left:

    st.markdown("## ⚙️ Production Decisions")

    machines_body = st.slider("Body Machines", 1, 20, 4)
    machines_paint = st.slider("Paint Machines", 1, 20, 4)
    machines_engine = st.slider("Engine Machines", 1, 20, 4)
    machines_final = st.slider("Final Assembly Machines", 1, 20, 4)

    st.divider()

    st.markdown("## 📦 Inventory Policy")

    policy = st.radio(
        "Select Ordering Policy",
        ["EOQ with Reorder Point", "Monthly Ordering Capacity"]
    )

    if policy == "EOQ with Reorder Point":

        # Recommended EOQ based on previous year's demand
        D = st.session_state.previous_year_demand
        S = ORDERING_COST
        H = HOLDING_COST_RAW_ANNUAL

        recommended_eoq = math.sqrt((2 * D * S) / H)
        recommended_eoq = int(round(recommended_eoq / LOT_SIZE) * LOT_SIZE)

        st.success(f"📊 Recommended EOQ (based on last year demand): {recommended_eoq:,} units")

        eoq_quantity = st.number_input(
            "Enter EOQ Quantity",
            min_value=LOT_SIZE,
            step=LOT_SIZE,
            value=recommended_eoq
        )

        # ROP calculation (daily demand × lead time)
        daily_demand_prev = D / 365
        recommended_rop = int(daily_demand_prev * LEAD_TIME_DAYS)

        st.info(f"Suggested Reorder Point (15-day demand): {recommended_rop:,} units")

        reorder_point = st.number_input(
            "Enter Reorder Point",
            min_value=0,
            value=recommended_rop
        )

    else:

        monthly_capacity = st.number_input(
            "Monthly Ordering Capacity",
            min_value=LOT_SIZE,
            step=LOT_SIZE,
            value=10000
        )

        st.caption(f"Annual Equivalent: {monthly_capacity * 12:,} units")

    st.divider()

    simulate = st.button("🚀 Run Production Simulation")

# =====================================================
# RIGHT PANEL – RESULTS
# =====================================================

with right:

    if simulate:

        # =============================
        # POLICY DECISION
        # =============================

        if policy == "EOQ with Reorder Point":
            if st.session_state.raw_inventory <= reorder_point:
                order_qty = eoq_quantity
            else:
                order_qty = 0
        else:
            order_qty = monthly_capacity * 12

        # =============================
        # LEAD TIME ARRIVAL
        # =============================

        if len(st.session_state.raw_pipeline) >= 1:
            arriving = st.session_state.raw_pipeline.pop(0)
            st.session_state.raw_inventory += arriving

        st.session_state.raw_pipeline.append(order_qty)

        ordering_cost_total = ORDERING_COST if order_qty > 0 else 0

        # =============================
        # DEMAND (STOCHASTIC)
        # =============================

        growth = np.random.uniform(-0.10, 0.25)
        st.session_state.monthly_demand *= (1 + growth)
        yearly_demand = st.session_state.monthly_demand * 12
        st.session_state.previous_year_demand = yearly_demand

        # =============================
        # CAPACITY
        # =============================

        yearly_hours = AVAILABLE_HOURS_MONTH * 12
        base_capacity = yearly_hours * UNITS_PER_MACHINE_PER_HOUR

        cap_body = machines_body * base_capacity * BODY_FACTOR
        cap_paint = machines_paint * base_capacity * PAINT_FACTOR
        cap_engine = machines_engine * base_capacity * ENGINE_FACTOR
        cap_final = machines_final * base_capacity * FINAL_FACTOR

        # =============================
        # PRODUCTION FLOW
        # =============================

        body_out = min(cap_body, st.session_state.raw_inventory)
        st.session_state.raw_inventory -= body_out
        st.session_state.wip_body += body_out

        paint_out = min(cap_paint, st.session_state.wip_body)
        st.session_state.wip_body -= paint_out
        st.session_state.wip_paint += paint_out

        engine_out = min(cap_engine, st.session_state.wip_paint)
        st.session_state.wip_paint -= engine_out
        st.session_state.wip_engine += engine_out

        final_out = min(cap_final, st.session_state.wip_engine)
        st.session_state.wip_engine -= final_out

        production = final_out
        st.session_state.fg_inventory += production

        # =============================
        # SALES
        # =============================

        units_sold = min(yearly_demand, st.session_state.fg_inventory)
        shortage = max(yearly_demand - st.session_state.fg_inventory, 0)
        st.session_state.fg_inventory -= units_sold

        # =============================
        # COST CALCULATIONS (DAILY → YEARLY)
        # =============================

        daily_raw_holding_cost = st.session_state.raw_inventory * HOLDING_COST_RAW_DAILY
        yearly_raw_holding_cost = daily_raw_holding_cost * 365

        raw_purchase_cost = order_qty * RAW_MATERIAL_COST
        shortage_cost = shortage * SHORTAGE_COST

        total_cost = (
            raw_purchase_cost +
            yearly_raw_holding_cost +
            ordering_cost_total +
            shortage_cost
        )

        revenue = units_sold * SELLING_PRICE
        net_profit = revenue - total_cost
        service_level = units_sold / yearly_demand if yearly_demand > 0 else 1

        # =============================
        # KPI CARDS
        # =============================

        k1, k2, k3 = st.columns(3)

        k1.metric("Net Profit", f"₹{net_profit/1e7:.2f} Cr")
        k2.metric("Yearly Raw Holding Cost", f"₹{yearly_raw_holding_cost/1e7:.2f} Cr")
        k3.metric("Service Level", f"{service_level*100:.1f}%")

        st.divider()

        breakdown = pd.DataFrame({
            "Metric": [
                "Demand",
                "Production",
                "Units Sold",
                "Order Quantity",
                "Raw Inventory",
                "Daily Holding Cost",
                "Yearly Holding Cost"
            ],
            "Value": [
                int(yearly_demand),
                int(production),
                int(units_sold),
                int(order_qty),
                int(st.session_state.raw_inventory),
                int(daily_raw_holding_cost),
                int(yearly_raw_holding_cost)
            ]
        })

        st.dataframe(breakdown, use_container_width=True)

# =====================================================
# RESET
# =====================================================

st.divider()

if st.button("🔄 Reset Simulation"):
    st.session_state.clear()
    st.rerun()
