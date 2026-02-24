import streamlit as st
import pandas as pd
import numpy as np
import math

st.set_page_config(page_title="SmartFlow AI – Dynamic Simulation", layout="wide")

# =====================================================
# CONSTANTS
# =====================================================

DAYS_IN_YEAR = 365
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
HOLDING_COST_RAW_DAILY = 10
SHORTAGE_COST = 200
SELLING_PRICE = 3000

# =====================================================
# UI
# =====================================================

st.title("🏭 Dynamic Production + Inventory Simulation")

left, right = st.columns([1, 2])

with left:

    st.subheader("Production Capacity")

    machines_body = st.slider("Body Machines", 1, 20, 4)
    machines_paint = st.slider("Paint Machines", 1, 20, 4)
    machines_engine = st.slider("Engine Machines", 1, 20, 4)
    machines_final = st.slider("Final Assembly Machines", 1, 20, 4)

    st.subheader("EOQ Policy")

    yearly_demand_est = BASE_MONTHLY_DEMAND * 12
    H_annual = HOLDING_COST_RAW_DAILY * 365

    recommended_eoq = math.sqrt((2 * yearly_demand_est * ORDERING_COST) / H_annual)
    recommended_eoq = int(round(recommended_eoq / LOT_SIZE) * LOT_SIZE)
    recommended_eoq = max(LOT_SIZE, recommended_eoq)

    st.success(f"Recommended EOQ: {recommended_eoq:,}")

    eoq_quantity = st.number_input(
        "EOQ Quantity",
        min_value=LOT_SIZE,
        step=LOT_SIZE,
        value=recommended_eoq
    )

    daily_demand_est = yearly_demand_est / DAYS_IN_YEAR
    recommended_rop = int(daily_demand_est * LEAD_TIME_DAYS)

    reorder_point = st.number_input(
        "Reorder Point",
        min_value=0,
        value=recommended_rop
    )

    initial_raw_inventory = st.number_input(
        "Initial Raw Inventory",
        min_value=0,
        value=50000
    )

    simulate = st.button("🚀 Run Dynamic Simulation")

# =====================================================
# SIMULATION
# =====================================================

with right:

    if simulate:

        # INITIALIZE STATE
        raw_inventory = initial_raw_inventory
        fg_inventory = 0
        pipeline_orders = []

        total_ordering_cost = 0
        total_raw_holding_cost = 0
        total_shortage_cost = 0
        total_revenue = 0

        yearly_demand = BASE_MONTHLY_DEMAND * 12
        daily_demand = yearly_demand / DAYS_IN_YEAR

        # Daily production capacity
        yearly_hours = AVAILABLE_HOURS_MONTH * 12
        base_capacity_year = yearly_hours * UNITS_PER_MACHINE_PER_HOUR

        cap_body = machines_body * base_capacity_year * BODY_FACTOR
        cap_paint = machines_paint * base_capacity_year * PAINT_FACTOR
        cap_engine = machines_engine * base_capacity_year * ENGINE_FACTOR
        cap_final = machines_final * base_capacity_year * FINAL_FACTOR

        yearly_production_capacity = min(cap_body, cap_paint, cap_engine, cap_final)
        daily_production_capacity = yearly_production_capacity / DAYS_IN_YEAR

        total_production = 0
        total_units_sold = 0

        # DAY-BY-DAY SIMULATION
        for day in range(DAYS_IN_YEAR):

            # 1. Receive orders if lead time complete
            arriving_orders = [order for order in pipeline_orders if order["arrival_day"] == day]
            for order in arriving_orders:
                raw_inventory += order["qty"]
            pipeline_orders = [order for order in pipeline_orders if order["arrival_day"] > day]

            # 2. Production
            production_today = min(daily_production_capacity, raw_inventory)
            raw_inventory -= production_today
            fg_inventory += production_today
            total_production += production_today

            # 3. Demand
            demand_today = daily_demand
            units_sold_today = min(demand_today, fg_inventory)
            shortage_today = max(demand_today - fg_inventory, 0)

            fg_inventory -= units_sold_today

            total_units_sold += units_sold_today
            total_shortage_cost += shortage_today * SHORTAGE_COST
            total_revenue += units_sold_today * SELLING_PRICE

            # 4. Holding cost
            total_raw_holding_cost += raw_inventory * HOLDING_COST_RAW_DAILY

            # 5. Reorder decision
            if raw_inventory <= reorder_point:
                pipeline_orders.append({
                    "qty": eoq_quantity,
                    "arrival_day": day + LEAD_TIME_DAYS
                })
                total_ordering_cost += ORDERING_COST

        total_cost = (
            total_raw_holding_cost +
            total_ordering_cost +
            total_shortage_cost
        )

        net_profit = total_revenue - total_cost
        service_level = total_units_sold / yearly_demand

        # =====================================================
        # OUTPUT
        # =====================================================

        k1, k2, k3 = st.columns(3)

        k1.metric("Yearly Production", f"{int(total_production):,}")
        k2.metric("Net Profit", f"₹{net_profit/1e7:.2f} Cr")
        k3.metric("Service Level", f"{service_level*100:.1f}%")

        st.divider()

        results = pd.DataFrame({
            "Metric": [
                "Total Orders Placed",
                "Total Ordering Cost",
                "Total Holding Cost",
                "Total Shortage Cost",
                "Units Sold",
                "Ending Raw Inventory"
            ],
            "Value": [
                len(pipeline_orders),
                int(total_ordering_cost),
                int(total_raw_holding_cost),
                int(total_shortage_cost),
                int(total_units_sold),
                int(raw_inventory)
            ]
        })

        st.dataframe(results, use_container_width=True)
