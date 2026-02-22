import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="SmartFlow AI", layout="wide")

st.title("🚗 SmartFlow AI – Multi-Stage Factory Simulation")

st.markdown("""
Multi-stage factory with:
• Raw material ordering  
• Lead time  
• True stage-wise WIP buffers  
• Finished goods inventory  
• Demand & inflation uncertainty  
""")

# =====================================================
# PARAMETERS
# =====================================================

BASE_MONTHLY_DEMAND = 10000
BREAKDOWN_PROB = 0.08
AVAILABLE_HOURS_MONTH = 160
UNITS_PER_MACHINE_PER_HOUR = 7

BODY_FACTOR = 5
PAINT_FACTOR = 7
ENGINE_FACTOR = 3
FINAL_FACTOR = 4

RAW_LEAD_TIME = 1  # years
RAW_MATERIAL_COST = 500
HOLDING_COST_FG = 50
HOLDING_COST_WIP = 30
SHORTAGE_COST = 200

# =====================================================
# SESSION STATE INIT
# =====================================================

defaults = {
    "year": 1,
    "monthly_demand": BASE_MONTHLY_DEMAND,
    "raw_inventory": 50000,
    "raw_pipeline": [],
    "wip_body": 0,
    "wip_paint": 0,
    "wip_engine": 0,
    "fg_inventory": 0,
    "results": [],
    "total_cost": 0,
    "total_units": 0
}

for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

current_year = st.session_state.year

# =====================================================
# YEARLY DECISION
# =====================================================

if current_year <= 5:

    st.header(f"⚙️ Year {current_year} Decision")

    col1, col2 = st.columns(2)

    with col1:
        machines_body = st.number_input("Body Machines", 1, 20, 4)
        machines_paint = st.number_input("Paint Machines", 1, 20, 4)
        machines_engine = st.number_input("Engine Machines", 1, 20, 4)
        machines_final = st.number_input("Final Machines", 1, 20, 4)

    with col2:
        raw_order = st.number_input("Raw Material Order Quantity", 0, 200000, 20000)

    # =====================================================
    # PROCESS RAW MATERIAL ARRIVAL
    # =====================================================

    if len(st.session_state.raw_pipeline) >= RAW_LEAD_TIME:
        arriving = st.session_state.raw_pipeline.pop(0)
        st.session_state.raw_inventory += arriving

    st.session_state.raw_pipeline.append(raw_order)

    # =====================================================
    # DEMAND SHOCK
    # =====================================================
    if st.button("Simulate Year"):

        # Demand shock (ONLY ONCE PER YEAR)
        demand_growth = np.random.uniform(-0.10, 0.25)
        st.session_state.monthly_demand *= (1 + demand_growth)
        yearly_demand = st.session_state.monthly_demand * 12    

    yearly_hours = AVAILABLE_HOURS_MONTH * 12
    base_capacity = yearly_hours * UNITS_PER_MACHINE_PER_HOUR

    cap_body = machines_body * base_capacity * BODY_FACTOR
    cap_paint = machines_paint * base_capacity * PAINT_FACTOR
    cap_engine = machines_engine * base_capacity * ENGINE_FACTOR
    cap_final = machines_final * base_capacity * FINAL_FACTOR

    if st.button("Simulate Year"):

        # =====================================================
        # STAGE 1: BODY (Consumes Raw Material)
        # =====================================================

        body_input = min(cap_body, st.session_state.raw_inventory)
        st.session_state.raw_inventory -= body_input

        body_output = body_input  # completed body units
        st.session_state.wip_body += body_output

        # =====================================================
        # STAGE 2: PAINT
        # =====================================================

        paint_input = min(cap_paint, st.session_state.wip_body)
        st.session_state.wip_body -= paint_input
        st.session_state.wip_paint += paint_input

        # =====================================================
        # STAGE 3: ENGINE
        # =====================================================

        engine_input = min(cap_engine, st.session_state.wip_paint)
        st.session_state.wip_paint -= engine_input
        st.session_state.wip_engine += engine_input

        # =====================================================
        # STAGE 4: FINAL
        # =====================================================

        final_input = min(cap_final, st.session_state.wip_engine)
        st.session_state.wip_engine -= final_input

        production = final_input
        st.session_state.fg_inventory += production

        # =====================================================
        # SALES
        # =====================================================

        units_sold = min(yearly_demand, st.session_state.fg_inventory)
        shortage = max(yearly_demand - st.session_state.fg_inventory, 0)
        st.session_state.fg_inventory -= units_sold

        # =====================================================
        # COSTS
        # =====================================================

        raw_material_cost = raw_order * RAW_MATERIAL_COST
        holding_cost_fg = st.session_state.fg_inventory * HOLDING_COST_FG
        holding_cost_wip = (
            st.session_state.wip_body +
            st.session_state.wip_paint +
            st.session_state.wip_engine
        ) * HOLDING_COST_WIP
        shortage_cost = shortage * SHORTAGE_COST

        total_cost = raw_material_cost + holding_cost_fg + holding_cost_wip + shortage_cost
        cost_per_unit = total_cost / max(units_sold, 1)

        # =====================================================
        # STORE RESULTS
        # =====================================================

        st.session_state.results.append({
            "Year": current_year,
            "Demand": round(yearly_demand),
            "Production": round(production),
            "Units Sold": round(units_sold),
            "Raw Inventory": round(st.session_state.raw_inventory),
            "WIP Body": round(st.session_state.wip_body),
            "WIP Paint": round(st.session_state.wip_paint),
            "WIP Engine": round(st.session_state.wip_engine),
            "FG Inventory": round(st.session_state.fg_inventory),
            "Shortage": round(shortage),
            "Total Cost": round(total_cost),
            "Cost per Unit": round(cost_per_unit, 2)
        })

        st.session_state.total_cost += total_cost
        st.session_state.total_units += units_sold
        st.session_state.year += 1

        st.success(f"Year {current_year} simulated.")
        st.rerun()

# =====================================================
# RESULTS
# =====================================================

if len(st.session_state.results) > 0:

    df = pd.DataFrame(st.session_state.results)

    st.subheader("📊 Simulation Results")
    st.dataframe(df, use_container_width=True)

    st.subheader("📈 Demand vs Production")
    st.line_chart(df.set_index("Year")[["Demand", "Production"]])

    st.subheader("📦 Finished Goods Inventory")
    st.line_chart(df.set_index("Year")["FG Inventory"])

    st.subheader("🏭 WIP Inventory")
    st.line_chart(df.set_index("Year")[["WIP Body", "WIP Paint", "WIP Engine"]])

if st.button("🔄 Restart Simulation"):
    st.session_state.clear()
    st.rerun()
