import streamlit as st
import pandas as pd
import numpy as np

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
# PARAMETERS
# =====================================================

BASE_MONTHLY_DEMAND = 10000
AVAILABLE_HOURS_MONTH = 160
UNITS_PER_MACHINE_PER_HOUR = 7

BODY_FACTOR = 5
PAINT_FACTOR = 7
ENGINE_FACTOR = 3
FINAL_FACTOR = 4

# Inventory Policy Constants
LEAD_TIME_CYCLES = 1   # 15 days approximated as 1 cycle delay
ORDERING_COST = 100000
LOT_SIZE = 10000

RAW_MATERIAL_COST = 500
HOLDING_COST_FG = 50
HOLDING_COST_WIP = 30
SHORTAGE_COST = 200

# =====================================================
# SESSION STATE INIT
# =====================================================

defaults = {
    "monthly_demand": BASE_MONTHLY_DEMAND,
    "raw_inventory": 50000,
    "raw_pipeline": [],
    "wip_body": 0,
    "wip_paint": 0,
    "wip_engine": 0,
    "fg_inventory": 0,
    "results": None
}

for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# =====================================================
# MAIN LAYOUT
# =====================================================

left, right = st.columns([1, 2])

# =====================================================
# LEFT PANEL – DECISIONS
# =====================================================

with left:

    st.markdown("## Production Decisions")

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

        eoq_quantity = st.number_input(
            "EOQ Quantity (units)",
            min_value=LOT_SIZE,
            step=LOT_SIZE,
            value=20000
        )

        reorder_point = st.number_input(
            "Reorder Point (units)",
            min_value=0,
            value=30000
        )

    else:

        monthly_capacity = st.number_input(
            "Monthly Ordering Capacity (units)",
            min_value=LOT_SIZE,
            step=LOT_SIZE,
            value=50000
        )

    st.divider()

    simulate = st.button("🚀 Run Production Simulation")

# =====================================================
# RIGHT PANEL – RESULTS
# =====================================================

with right:

    if simulate:

        # -------------------------------------------------
        # POLICY LOGIC
        # -------------------------------------------------

        if policy == "EOQ with Reorder Point":

            if st.session_state.raw_inventory <= reorder_point:
                order_qty = eoq_quantity
            else:
                order_qty = 0

        else:

            order_qty = monthly_capacity

        # -------------------------------------------------
        # LEAD TIME PROCESSING
        # -------------------------------------------------

        if len(st.session_state.raw_pipeline) >= LEAD_TIME_CYCLES:
            arriving = st.session_state.raw_pipeline.pop(0)
            st.session_state.raw_inventory += arriving

        st.session_state.raw_pipeline.append(order_qty)

        ordering_cost_total = ORDERING_COST if order_qty > 0 else 0

        # -------------------------------------------------
        # DEMAND SHOCK
        # -------------------------------------------------

        growth = np.random.uniform(-0.10, 0.25)
        st.session_state.monthly_demand *= (1 + growth)
        yearly_demand = st.session_state.monthly_demand * 12

        # -------------------------------------------------
        # CAPACITY CALCULATION
        # -------------------------------------------------

        yearly_hours = AVAILABLE_HOURS_MONTH * 12
        base_capacity = yearly_hours * UNITS_PER_MACHINE_PER_HOUR

        cap_body = machines_body * base_capacity * BODY_FACTOR
        cap_paint = machines_paint * base_capacity * PAINT_FACTOR
        cap_engine = machines_engine * base_capacity * ENGINE_FACTOR
        cap_final = machines_final * base_capacity * FINAL_FACTOR

        # -------------------------------------------------
        # PRODUCTION FLOW
        # -------------------------------------------------

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

        # -------------------------------------------------
        # SALES
        # -------------------------------------------------

        units_sold = min(yearly_demand, st.session_state.fg_inventory)
        shortage = max(yearly_demand - st.session_state.fg_inventory, 0)
        st.session_state.fg_inventory -= units_sold

        # -------------------------------------------------
        # COST CALCULATION
        # -------------------------------------------------

        raw_cost = order_qty * RAW_MATERIAL_COST
        holding_fg = st.session_state.fg_inventory * HOLDING_COST_FG
        holding_wip = (
            st.session_state.wip_body +
            st.session_state.wip_paint +
            st.session_state.wip_engine
        ) * HOLDING_COST_WIP

        shortage_cost = shortage * SHORTAGE_COST

        total_cost = (
            raw_cost +
            holding_fg +
            holding_wip +
            shortage_cost +
            ordering_cost_total
        )

        revenue = units_sold * 3000
        net_profit = revenue - total_cost

        service_level = units_sold / yearly_demand if yearly_demand > 0 else 1

        # =====================================================
        # KPI CARDS
        # =====================================================

        k1, k2, k3 = st.columns(3)

        k1.metric("Net Profit", f"₹{net_profit/1e7:.2f} Cr")
        k2.metric("Ordering Cost", f"₹{ordering_cost_total/1e7:.2f} Cr")
        k3.metric("Holding + Shortage Cost", f"₹{(holding_fg+holding_wip+shortage_cost)/1e7:.2f} Cr")

        st.divider()

        # =====================================================
        # PERFORMANCE BREAKDOWN
        # =====================================================

        breakdown = pd.DataFrame({
            "Metric": [
                "Demand",
                "Production",
                "Units Sold",
                "Service Level (%)",
                "Raw Inventory",
                "WIP Body",
                "WIP Paint",
                "WIP Engine",
                "Finished Goods Inventory",
                "Order Quantity"
            ],
            "Value": [
                int(yearly_demand),
                int(production),
                int(units_sold),
                round(service_level * 100, 1),
                int(st.session_state.raw_inventory),
                int(st.session_state.wip_body),
                int(st.session_state.wip_paint),
                int(st.session_state.wip_engine),
                int(st.session_state.fg_inventory),
                int(order_qty)
            ]
        })

        st.markdown("## Production Performance Breakdown")
        st.dataframe(breakdown, use_container_width=True)

        st.divider()

        # =====================================================
        # INSIGHT BOX
        # =====================================================

        st.markdown("### 📘 Managerial Insight (OM Concept)")
        st.info("""
        This model compares Continuous Review (EOQ + ROP) and Capacity-Based Ordering policies.
        EOQ minimizes ordering + holding trade-offs, while reorder point protects against stockouts under lead time.
        Monthly capacity policy reflects operational or supplier constraints.
        Profitability depends on ordering frequency, service level, and bottleneck capacity.
        """)

# =====================================================
# RESET BUTTON
# =====================================================

st.divider()

if st.button("🔄 Reset Simulation"):
    st.session_state.clear()
    st.rerun()
