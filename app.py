import streamlit as st
import pandas as pd
import numpy as np
import math

st.set_page_config(page_title="SmartFlow AI – 5 Year Strategic Simulation", layout="wide")

# ==============================
# CONSTANTS
# ==============================

DAYS = 365
YEARS = 5
BASE_MONTHLY_DEMAND = 10000

AVAILABLE_HOURS_MONTH = 160
UNITS_PER_MACHINE_PER_HOUR = 7

BODY_FACTOR = 5
PAINT_FACTOR = 7
ENGINE_FACTOR = 3
FINAL_FACTOR = 4

LEAD_TIME_DAYS = 15
LOT_SIZE = 10000

RAW_COST_BASE = 500
HOLDING_DAILY_BASE = 10
SHORTAGE_COST_BASE = 200
ORDER_COST_BASE = 100000
SELLING_PRICE_BASE = 3000

# ==============================
# SESSION STATE INIT
# ==============================

if "year" not in st.session_state:
    st.session_state.year = 1
    st.session_state.results = []
    st.session_state.raw_inventory = 50000
    st.session_state.wip_inventory = 0
    st.session_state.fg_inventory = 0
    st.session_state.yearly_demand = BASE_MONTHLY_DEMAND * 12
    st.session_state.selling_price = SELLING_PRICE_BASE
    st.session_state.raw_cost = RAW_COST_BASE
    st.session_state.holding_daily = HOLDING_DAILY_BASE
    st.session_state.shortage_cost = SHORTAGE_COST_BASE
    st.session_state.order_cost = ORDER_COST_BASE

# ==============================
# HEADER
# ==============================

st.title("🏭 5-Year Strategic Production Simulation")
st.markdown(f"## Year {st.session_state.year}")

# ==============================
# SHOW PREVIOUS YEAR RESULTS
# ==============================

if st.session_state.results:
    last = st.session_state.results[-1]

    st.markdown("### 📊 Previous Year Performance")

    c1, c2, c3 = st.columns(3)
    c1.metric("Demand", f"{last[1]:,}")
    c2.metric("Production", f"{last[2]:,}")
    c3.metric("Net Profit", f"₹{last[3]/1e7:.2f} Cr")

    c4, c5 = st.columns(2)
    c4.metric("Cost per Unit", f"₹{last[5]:,}")
    c5.metric("Price per Unit", f"₹{last[6]:,}")

    c6, c7, c8 = st.columns(3)
    c6.metric("Ending Raw", f"{last[7]:,}")
    c7.metric("Ending WIP", f"{last[8]:,}")
    c8.metric("Ending FG", f"{last[9]:,}")

    st.metric("Service Level", f"{last[4]}%")

    st.divider()

# ==============================
# DECISION PANEL
# ==============================

if st.session_state.year <= YEARS:

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Capacity Decision")

        machines_body = st.slider("Body Machines", 1, 20, 4)
        machines_paint = st.slider("Paint Machines", 1, 20, 4)
        machines_engine = st.slider("Engine Machines", 1, 20, 4)
        machines_final = st.slider("Final Machines", 1, 20, 4)

    with col2:
        st.subheader("Policy Decision")

        price_growth = st.slider("Price Increase %", 4, 14, 8)

        H_annual = st.session_state.holding_daily * 365
        D = st.session_state.yearly_demand
        S = st.session_state.order_cost

        rec_eoq = math.sqrt((2 * D * S) / H_annual)
        rec_eoq = int(round(rec_eoq / LOT_SIZE) * LOT_SIZE)
        rec_eoq = max(LOT_SIZE, rec_eoq)

        st.info(f"Recommended EOQ: {rec_eoq:,}")

        eoq = st.number_input("EOQ", min_value=LOT_SIZE, step=LOT_SIZE, value=rec_eoq)

        daily_demand = D / DAYS
        rec_rop = int(daily_demand * LEAD_TIME_DAYS)

        reorder_point = st.number_input("Reorder Point", min_value=0, value=rec_rop)

    simulate = st.button("Run Year Simulation")

    if simulate:

        # ===== Annual Growth =====

        demand_growth = np.random.uniform(0.10, 0.25)
        cost_inflation = np.random.uniform(0.06, 0.12)

        st.session_state.yearly_demand *= (1 + demand_growth)
        st.session_state.selling_price *= (1 + price_growth / 100)

        st.session_state.raw_cost *= (1 + cost_inflation)
        st.session_state.holding_daily *= (1 + cost_inflation)
        st.session_state.shortage_cost *= (1 + cost_inflation)
        st.session_state.order_cost *= (1 + cost_inflation)

        avg_daily_demand = st.session_state.yearly_demand / DAYS
        sigma = avg_daily_demand * np.random.uniform(0.10, 0.25)

        yearly_hours = AVAILABLE_HOURS_MONTH * 12
        base_cap = yearly_hours * UNITS_PER_MACHINE_PER_HOUR

        yearly_capacity = min(
            machines_body * base_cap * BODY_FACTOR,
            machines_paint * base_cap * PAINT_FACTOR,
            machines_engine * base_cap * ENGINE_FACTOR,
            machines_final * base_cap * FINAL_FACTOR
        )

        daily_capacity = yearly_capacity / DAYS

        total_prod = 0
        total_sold = 0
        total_hold = 0
        total_short = 0
        total_order_cost = 0

        pipeline = []

        # ===== Daily Simulation =====

        for day in range(DAYS):

            # Receive Orders
            arriving = [o for o in pipeline if o["arrival"] == day]
            for order in arriving:
                st.session_state.raw_inventory += order["qty"]

            pipeline = [o for o in pipeline if o["arrival"] > day]

            # Production -> WIP
            prod_today = min(daily_capacity, st.session_state.raw_inventory)
            st.session_state.raw_inventory -= prod_today
            st.session_state.wip_inventory += prod_today
            total_prod += prod_today

            # WIP -> FG (1 day lag simplified)
            st.session_state.fg_inventory += st.session_state.wip_inventory
            st.session_state.wip_inventory = 0

            # Demand
            demand_today = max(0, np.random.normal(avg_daily_demand, sigma))
            sold_today = min(demand_today, st.session_state.fg_inventory)
            short_today = max(demand_today - st.session_state.fg_inventory, 0)

            st.session_state.fg_inventory -= sold_today

            total_sold += sold_today
            total_short += short_today * st.session_state.shortage_cost

            # Holding cost
            total_hold += (
                st.session_state.raw_inventory +
                st.session_state.wip_inventory +
                st.session_state.fg_inventory
            ) * st.session_state.holding_daily

            # Reorder decision
            if st.session_state.raw_inventory <= reorder_point:
                pipeline.append({"qty": eoq, "arrival": day + LEAD_TIME_DAYS})
                total_order_cost += st.session_state.order_cost

        revenue = total_sold * st.session_state.selling_price
        raw_purchase = total_prod * st.session_state.raw_cost

        total_cost = total_hold + total_short + total_order_cost + raw_purchase
        net_profit = revenue - total_cost
        service = total_sold / st.session_state.yearly_demand

        cost_per_unit = total_cost / total_prod if total_prod > 0 else 0
        price_per_unit = st.session_state.selling_price

        st.session_state.results.append([
            st.session_state.year,
            int(st.session_state.yearly_demand),
            int(total_prod),
            int(net_profit),
            round(service * 100, 1),
            int(cost_per_unit),
            int(price_per_unit),
            int(st.session_state.raw_inventory),
            int(st.session_state.wip_inventory),
            int(st.session_state.fg_inventory)
        ])

        st.session_state.year += 1
        st.rerun()

# ==============================
# FINAL RESULTS
# ==============================

if st.session_state.year > YEARS:

    df = pd.DataFrame(
        st.session_state.results,
        columns=[
            "Year",
            "Demand",
            "Production",
            "Net Profit",
            "Service Level (%)",
            "Cost per Unit",
            "Price per Unit",
            "Ending Raw Inventory",
            "Ending WIP",
            "Ending FG Inventory"
        ]
    )

    st.success("Simulation Complete")
    st.dataframe(df, use_container_width=True)

    st.line_chart(df.set_index("Year")[["Demand", "Production"]])

    if st.button("Restart Simulation"):
        st.session_state.clear()
        st.rerun()
