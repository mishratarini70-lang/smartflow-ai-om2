import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="SmartFlow AI", layout="wide")

st.title("🚗 SmartFlow AI – Rolling 5-Year Production & Inventory Simulator")

st.markdown("""
Dynamic 5-year automobile production planning under demand and inflation uncertainty.
Managers decide year by year. Inventory carries forward.
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
# SAFE SESSION STATE INITIALIZATION
# =====================================================

defaults = {
    "year": 1,
    "monthly_demand": BASE_MONTHLY_DEMAND,
    "inventory": 0,
    "results": [],
    "total_cost": 0,
    "total_units": 0
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value

current_year = st.session_state.year

# =====================================================
# YEARLY DECISION SECTION
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

        # DEMAND SHOCK
        demand_growth = np.random.uniform(-0.10, 0.25)
        st.session_state.monthly_demand *= (1 + demand_growth)
        yearly_demand = st.session_state.monthly_demand * 12

        # INFLATION SHOCK
        inflation = np.random.uniform(0.06, 0.12)

        # CAPACITY
        effective_breakdown = BREAKDOWN_PROB * (1 - maintenance_eff)
        yearly_hours = AVAILABLE_HOURS_MONTH * 12

        cap_body = machines_body * yearly_hours * (1 - effective_breakdown)
        cap_paint = machines_paint * yearly_hours * (1 - effective_breakdown)
        cap_engine = machines_engine * yearly_hours * (1 - effective_breakdown)
        cap_final = machines_final * yearly_hours * (1 - effective_breakdown)

        production = min(cap_body, cap_paint, cap_engine, cap_final)

        # INVENTORY FLOW
       available_units = production + st.session_state.inventory

        # Core inventory equation
        units_sold = min(yearly_demand, available_units)
        
        ending_inventory = max(available_units - yearly_demand, 0)
        
        shortage = max(yearly_demand - available_units, 0)


        # COST
        machine_cost = 400 * (cap_body + cap_paint + cap_engine + cap_final)
        labor_cost = 50 * overtime * 12
        setup_cost = SETUP_TIME * 12 * 10
        holding_cost = ending_inventory * HOLDING_COST_PER_UNIT
        shortage_cost = shortage * SHORTAGE_PENALTY_PER_UNIT

        total_cost = (machine_cost + labor_cost + setup_cost +
                      holding_cost + shortage_cost) * (1 + inflation)

        cost_per_unit = total_cost / max(units_sold, 1)

        # STORE RESULTS (CONSISTENT STRUCTURE)
        row = {
            "Year": current_year,
            "Demand Growth (%)": round(demand_growth * 100, 2),
            "Demand": round(yearly_demand, 0),
            "Production": round(production, 0),
            "Units Sold": round(units_sold, 0),
            "Ending Inventory": round(ending_inventory, 0),
            "Shortage": round(shortage, 0),
            "Inflation (%)": round(inflation * 100, 2),
            "Total Cost": round(total_cost, 0),
            "Cost per Unit": round(cost_per_unit, 2)
        }

        st.session_state.results.append(row)

        st.session_state.inventory = ending_inventory
        st.session_state.total_cost += total_cost
        st.session_state.total_units += units_sold
        st.session_state.year += 1

        st.success(f"Year {current_year} completed.")
        st.rerun()

# =====================================================
# DISPLAY SECTION (DEFENSIVE)
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

    # Only plot if required columns exist
    if "Year" in df.columns:

        if {"Demand", "Production"}.issubset(df.columns):
            st.subheader("📈 Demand vs Production")
            st.line_chart(df.set_index("Year")[["Demand", "Production"]])

        if "Ending Inventory" in df.columns:
            st.subheader("📦 Inventory Trend")
            st.line_chart(df.set_index("Year")["Ending Inventory"])

        if "Cost per Unit" in df.columns:
            st.subheader("💰 Cost per Unit Trend")
            st.line_chart(df.set_index("Year")["Cost per Unit"])

    if st.session_state.year > 5:
        st.success("🎯 5-Year Simulation Completed!")

# =====================================================
# RESET
# =====================================================

if st.button("🔄 Restart Simulation"):
    st.session_state.clear()
    st.rerun()
