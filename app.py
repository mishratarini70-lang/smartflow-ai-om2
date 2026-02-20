import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="SmartFlow AI", layout="wide")

st.title("🚗 SmartFlow AI – Rolling 5-Year Production & Inventory Simulator")

st.markdown("""
Dynamic 5-year automobile production planning under demand and inflation uncertainty.
Managers make decisions each year. Inventory carries forward.
""")

# =====================================================
# FIXED SYSTEM PARAMETERS
# =====================================================

BASE_MONTHLY_DEMAND = 10000
BREAKDOWN_PROB = 0.08
SETUP_TIME = 45
AVAILABLE_HOURS_MONTH = 160

HOLDING_COST_PER_UNIT = 50
SHORTAGE_PENALTY_PER_UNIT = 200

st.sidebar.header("🔒 System Assumptions")
st.sidebar.write("Initial Monthly Demand: 10,000")
st.sidebar.write("Demand Growth: Random (-10% to +25%)")
st.sidebar.write("Inflation: Random (6% to 12%)")
st.sidebar.write("Holding Cost: ₹50 per unit")
st.sidebar.write("Shortage Penalty: ₹200 per unit")

# =====================================================
# SESSION STATE INITIALIZATION
# =====================================================

if "year" not in st.session_state:
    st.session_state.year = 1
    st.session_state.monthly_demand = BASE_MONTHLY_DEMAND
    st.session_state.inventory = 0
    st.session_state.results = []
    st.session_state.total_cost = 0
    st.session_state.total_units = 0

current_year = st.session_state.year

# =====================================================
# YEARLY DECISION INPUT
# =====================================================

if current_year <= 5:

    st.header(f"⚙️ Year {current_year} Decision")

    col1, col2 = st.columns(2)

    with col1:
        machines_body = st.number_input("Body Machines", 1, 20, 3)
        machines_paint = st.number_input("Paint Machines", 1, 20, 2)
        machines_engine = st.number_input("Engine Machines", 1, 20, 3)
        machines_final = st.number_input("Final Machines", 1, 20, 4)

    with col2:
        overtime = st.number_input("Overtime Hours", 0, 200, 20)
        maintenance_eff = st.slider("Maintenance Efficiency", 0.0, 1.0, 0.5)

    st.write(f"📦 Starting Inventory: {int(st.session_state.inventory)} units")

    if st.button("Simulate This Year"):

        # ----------------------------
        # DEMAND SHOCK
        # ----------------------------

        demand_growth = np.random.uniform(-0.10, 0.25)
        st.session_state.monthly_demand *= (1 + demand_growth)
        yearly_demand = st.session_state.monthly_demand * 12

        # ----------------------------
        # INFLATION SHOCK
        # ----------------------------

        inflation = np.random.uniform(0.06, 0.12)

        # ----------------------------
        # CAPACITY CALCULATION
        # ----------------------------

        effective_breakdown = BREAKDOWN_PROB * (1 - maintenance_eff)
        yearly_hours = AVAILABLE_HOURS_MONTH * 12

        cap_body = machines_body * yearly_hours * (1 - effective_breakdown)
        cap_paint = machines_paint * yearly_hours * (1 - effective_breakdown)
        cap_engine = machines_engine * yearly_hours * (1 - effective_breakdown)
        cap_final = machines_final * yearly_hours * (1 - effective_breakdown)

        throughput = min(cap_body, cap_paint, cap_engine, cap_final)

        # ----------------------------
        # INVENTORY LOGIC
        # ----------------------------

        available_units = throughput + st.session_state.inventory

        if available_units >= yearly_demand:
            units_sold = yearly_demand
            ending_inventory = available_units - yearly_demand
            shortage = 0
        else:
            units_sold = available_units
            ending_inventory = 0
            shortage = yearly_demand - available_units

        # ----------------------------
        # COST CALCULATION
        # ----------------------------

        machine_cost = 400 * (cap_body + cap_paint + cap_engine + cap_final)
        labor_cost = 50 * overtime * 12
        setup_cost = SETUP_TIME * 12 * 10
        holding_cost = ending_inventory * HOLDING_COST_PER_UNIT
        shortage_cost = shortage * SHORTAGE_PENALTY_PER_UNIT

        total_cost = (machine_cost + labor_cost + setup_cost +
                      holding_cost + shortage_cost) * (1 + inflation)

        cost_per_unit = total_cost / max(units_sold, 1)

        # ----------------------------
        # STORE RESULTS
        # ----------------------------

        st.session_state.inventory = ending_inventory
        st.session_state.total_cost += total_cost
        st.session_state.total_units += units_sold

        st.session_state.results.append({
            "Year": current_year,
            "Demand Growth (%)": demand_growth * 100,
            "Demand": yearly_demand,
            "Production": throughput,
            "Units Sold": units_sold,
            "Ending Inventory": ending_inventory,
            "Shortage": shortage,
            "Inflation (%)": inflation * 100,
            "Total Cost": total_cost,
            "Cost per Unit": cost_per_unit
        })

        st.session_state.year += 1

        st.success(f"Year {current_year} simulated successfully.")
        st.rerun()

# =====================================================
# DISPLAY RESULTS
# =====================================================

if len(st.session_state.results) > 0:

    df = pd.DataFrame(st.session_state.results)

    st.subheader("📊 Simulation Progress")
    st.dataframe(df, use_container_width=True)

    avg_cost = st.session_state.total_cost / max(st.session_state.total_units, 1)

    colA, colB, colC = st.columns(3)
    colA.metric("Cumulative Avg Cost per Unit", f"₹{avg_cost:,.2f}")
    colB.metric("Total Units Sold", f"{int(st.session_state.total_units):,}")
    colC.metric("Ending Inventory", f"{int(st.session_state.inventory):,}")

    st.subheader("📈 Demand vs Production")
    st.line_chart(df.set_index("Year")[["Demand", "Production"]])

    st.subheader("📦 Inventory Trend")
    st.line_chart(df.set_index("Year")["Ending Inventory"])

    st.subheader("💰 Cost per Unit Trend")
    st.line_chart(df.set_index("Year")["Cost per Unit"])

    if st.session_state.year > 5:
        st.success("🎯 5-Year Simulation Completed!")

# =====================================================
# RESET BUTTON
# =====================================================

if st.button("🔄 Restart Simulation"):
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()
