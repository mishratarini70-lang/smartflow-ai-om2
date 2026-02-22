import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="SmartFlow AI", layout="wide")

# =====================================================
# HEADER
# =====================================================

st.markdown("""
# 🚗 SmartFlow AI  
### Multi-Stage Production & Inventory Simulation
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

RAW_LEAD_TIME = 1
RAW_MATERIAL_COST = 500
HOLDING_COST_FG = 50
HOLDING_COST_WIP = 30
SHORTAGE_COST = 200

YEARS = 5

# =====================================================
# SIDEBAR – SYSTEM INFO
# =====================================================

with st.sidebar:
    st.header("⚙️ System Assumptions")

    st.info("Initial Monthly Demand: 10,000")
    st.info("Demand Growth: -10% to +25%")
    st.info("Raw Lead Time: 1 Year")

    st.divider()

    if st.button("🔄 Restart Simulation", key="reset_btn"):
        st.session_state.clear()
        st.rerun()

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
# MAIN TABS
# =====================================================

tab1, tab2, tab3 = st.tabs(["🎯 Decision Panel", "📊 Results Dashboard", "🏭 Inventory Flow"])

# =====================================================
# TAB 1 – DECISION PANEL
# =====================================================

with tab1:

    if current_year <= YEARS:

        st.subheader(f"Year {current_year} Decisions")

        col1, col2 = st.columns(2)

        with col1:
            machines_body = st.number_input("Body Machines", 1, 20, 4, key=f"body_{current_year}")
            machines_paint = st.number_input("Paint Machines", 1, 20, 4, key=f"paint_{current_year}")
            machines_engine = st.number_input("Engine Machines", 1, 20, 4, key=f"engine_{current_year}")
            machines_final = st.number_input("Final Machines", 1, 20, 4, key=f"final_{current_year}")

        with col2:
            raw_order = st.number_input("Raw Material Order", 0, 200000, 20000, key=f"raw_{current_year}")

        st.divider()

        if st.button("🚀 Simulate Year", key=f"simulate_{current_year}"):

            # --- RAW ARRIVAL ---
            if len(st.session_state.raw_pipeline) >= RAW_LEAD_TIME:
                arriving = st.session_state.raw_pipeline.pop(0)
                st.session_state.raw_inventory += arriving

            st.session_state.raw_pipeline.append(raw_order)

            # --- DEMAND ---
            growth = np.random.uniform(-0.10, 0.25)
            st.session_state.monthly_demand *= (1 + growth)
            yearly_demand = st.session_state.monthly_demand * 12

            # --- CAPACITY ---
            yearly_hours = AVAILABLE_HOURS_MONTH * 12
            base_capacity = yearly_hours * UNITS_PER_MACHINE_PER_HOUR

            cap_body = machines_body * base_capacity * BODY_FACTOR
            cap_paint = machines_paint * base_capacity * PAINT_FACTOR
            cap_engine = machines_engine * base_capacity * ENGINE_FACTOR
            cap_final = machines_final * base_capacity * FINAL_FACTOR

            # --- FLOW ---
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

            # --- SALES ---
            units_sold = min(yearly_demand, st.session_state.fg_inventory)
            shortage = max(yearly_demand - st.session_state.fg_inventory, 0)
            st.session_state.fg_inventory -= units_sold

            # --- COST ---
            total_cost = (
                raw_order * RAW_MATERIAL_COST +
                st.session_state.fg_inventory * HOLDING_COST_FG +
                (st.session_state.wip_body +
                 st.session_state.wip_paint +
                 st.session_state.wip_engine) * HOLDING_COST_WIP +
                shortage * SHORTAGE_COST
            )

            cost_per_unit = total_cost / max(units_sold, 1)

            st.session_state.results.append({
                "Year": current_year,
                "Demand": round(yearly_demand),
                "Production": round(production),
                "Units Sold": round(units_sold),
                "FG Inventory": round(st.session_state.fg_inventory),
                "Total Cost": round(total_cost),
                "Cost per Unit": round(cost_per_unit, 2)
            })

            st.session_state.total_cost += total_cost
            st.session_state.total_units += units_sold
            st.session_state.year += 1

            st.success("Simulation Complete")
            st.rerun()

    else:
        st.success("🎯 5-Year Simulation Completed!")

# =====================================================
# TAB 2 – RESULTS DASHBOARD
# =====================================================

with tab2:

    if len(st.session_state.results) > 0:

        df = pd.DataFrame(st.session_state.results)

        avg_cost = st.session_state.total_cost / max(st.session_state.total_units, 1)

        k1, k2, k3 = st.columns(3)
        k1.metric("Avg Cost per Unit", f"₹{avg_cost:,.2f}")
        k2.metric("Total Units Sold", f"{int(st.session_state.total_units):,}")
        k3.metric("Finished Goods", f"{int(st.session_state.fg_inventory):,}")

        st.divider()

        st.line_chart(df.set_index("Year")[["Demand", "Production"]])
        st.line_chart(df.set_index("Year")["Cost per Unit"])

        with st.expander("📄 Detailed Table"):
            st.dataframe(df, use_container_width=True)

    else:
        st.info("Run a simulation to see results.")

# =====================================================
# TAB 3 – INVENTORY FLOW
# =====================================================

with tab3:

    st.metric("Raw Inventory", int(st.session_state.raw_inventory))
    st.metric("WIP Body", int(st.session_state.wip_body))
    st.metric("WIP Paint", int(st.session_state.wip_paint))
    st.metric("WIP Engine", int(st.session_state.wip_engine))
    st.metric("Finished Goods", int(st.session_state.fg_inventory))
