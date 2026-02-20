import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="SmartFlow AI", layout="wide")

st.title("🚗 SmartFlow AI – 5-Year Production & Cost Simulator")

st.markdown("""
Rolling 5-year automobile production planning under demand uncertainty.
Cost breakdown visible during decision selection and in yearly results.
""")

# =====================================================
# FIXED SYSTEM PARAMETERS
# =====================================================

BASE_MONTHLY_DEMAND = 10000
BREAKDOWN_PROB = 0.08
SETUP_TIME = 45
AVAILABLE_HOURS_MONTH = 160
UNITS_PER_MACHINE_PER_HOUR = 7

HOLDING_COST_PER_UNIT = 50
SHORTAGE_PENALTY_PER_UNIT = 200
MACHINE_COST_PER_HOUR = 400
LABOR_COST_PER_HOUR = 50

st.sidebar.header("🔒 System Assumptions")
st.sidebar.write("Initial Monthly Demand: 10,000")
st.sidebar.write("Demand Growth: Random (-10% to +25%)")
st.sidebar.write("Inflation: Random (6% to 12%)")
st.sidebar.write(f"Units per Machine per Hour: {UNITS_PER_MACHINE_PER_HOUR}")
st.sidebar.write("Holding Cost: ₹50 per unit")
st.sidebar.write("Shortage Penalty: ₹200 per unit")

# =====================================================
# SAFE SESSION STATE
# =====================================================

defaults = {
    "year": 1,
    "monthly_demand": BASE_MONTHLY_DEMAND,
    "inventory": 0,
    "results": [],
    "total_cost": 0,
    "total_units": 0
}

for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

current_year = st.session_state.year

# =====================================================
# YEARLY DECISION INPUT
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
        overtime = st.number_input("Overtime Hours", 0, 200, 20)
        maintenance_eff = st.slider("Maintenance Efficiency", 0.0, 1.0, 0.5)

    total_machines = machines_body + machines_paint + machines_engine + machines_final

    # =====================================================
    # LIVE COST PREVIEW (NO DEMAND SHOCK YET)
    # =====================================================

    yearly_hours = AVAILABLE_HOURS_MONTH * 12
    machine_cost_preview = MACHINE_COST_PER_HOUR * total_machines * yearly_hours
    labor_cost_preview = LABOR_COST_PER_HOUR * overtime * 12
    setup_cost_preview = SETUP_TIME * 12 * 10

    st.subheader("💰 Estimated Cost Preview (Before Demand & Inventory Effects)")
    c1, c2, c3 = st.columns(3)
    c1.metric("Machine Cost (Est.)", f"₹{machine_cost_preview:,.0f}")
    c2.metric("Labor Cost (Est.)", f"₹{labor_cost_preview:,.0f}")
    c3.metric("Setup Cost (Est.)", f"₹{setup_cost_preview:,.0f}")

    st.write(f"📦 Starting Inventory: {int(st.session_state.inventory)} units")

    # =====================================================
    # SIMULATE YEAR
    # =====================================================

    if st.button("Simulate This Year"):

        # Demand Shock
        demand_growth = np.random.uniform(-0.10, 0.25)
        st.session_state.monthly_demand *= (1 + demand_growth)
        yearly_demand = st.session_state.monthly_demand * 12

        # Inflation Shock
        inflation = np.random.uniform(0.06, 0.12)

        # Production Capacity
        effective_breakdown = BREAKDOWN_PROB * (1 - maintenance_eff)

        cap_body = machines_body * yearly_hours * UNITS_PER_MACHINE_PER_HOUR * (1 - effective_breakdown)
        cap_paint = machines_paint * yearly_hours * UNITS_PER_MACHINE_PER_HOUR * (1 - effective_breakdown)
        cap_engine = machines_engine * yearly_hours * UNITS_PER_MACHINE_PER_HOUR * (1 - effective_breakdown)
        cap_final = machines_final * yearly_hours * UNITS_PER_MACHINE_PER_HOUR * (1 - effective_breakdown)

        production = min(cap_body, cap_paint, cap_engine, cap_final)

        # Inventory Logic
        available_units = production + st.session_state.inventory
        units_sold = min(yearly_demand, available_units)
        ending_inventory = max(available_units - yearly_demand, 0)
        shortage = max(yearly_demand - available_units, 0)

        # Cost Components
        machine_cost = machine_cost_preview
        labor_cost = labor_cost_preview
        setup_cost = setup_cost_preview
        holding_cost = ending_inventory * HOLDING_COST_PER_UNIT
        shortage_cost = shortage * SHORTAGE_PENALTY_PER_UNIT

        total_cost = (machine_cost + labor_cost + setup_cost +
                      holding_cost + shortage_cost) * (1 + inflation)

        cost_per_unit = total_cost / max(units_sold, 1)

        # Store Results
        st.session_state.results.append({
            "Year": current_year,
            "Demand": round(yearly_demand),
            "Production": round(production),
            "Units Sold": round(units_sold),
            "Ending Inventory": round(ending_inventory),
            "Shortage": round(shortage),
            "Machine Cost": round(machine_cost),
            "Labor Cost": round(labor_cost),
            "Setup Cost": round(setup_cost),
            "Holding Cost": round(holding_cost),
            "Shortage Cost": round(shortage_cost),
            "Inflation (%)": round(inflation * 100, 2),
            "Total Cost": round(total_cost),
            "Cost per Unit": round(cost_per_unit, 2)
        })

        st.session_state.inventory = ending_inventory
        st.session_state.total_cost += total_cost
        st.session_state.total_units += units_sold
        st.session_state.year += 1

        st.success(f"Year {current_year} completed.")
        st.rerun()

# =====================================================
# DISPLAY RESULTS
# =====================================================

if len(st.session_state.results) > 0:

    df = pd.DataFrame(st.session_state.results)

    st.subheader("📊 Simulation Results")
    st.dataframe(df, use_container_width=True)

    avg_cost = st.session_state.total_cost / max(st.session_state.total_units, 1)

    c1, c2, c3 = st.columns(3)
    c1.metric("Cumulative Avg Cost per Unit", f"₹{avg_cost:,.2f}")
    c2.metric("Total Units Sold", f"{int(st.session_state.total_units):,}")
    c3.metric("Ending Inventory", f"{int(st.session_state.inventory):,}")

    st.subheader("📈 Demand vs Production")
    st.line_chart(df.set_index("Year")[["Demand", "Production"]])

    st.subheader("💰 Cost per Unit Trend")
    st.line_chart(df.set_index("Year")["Cost per Unit"])

    st.subheader("📦 Inventory Trend")
    st.line_chart(df.set_index("Year")["Ending Inventory"])

    if st.session_state.year > 5:
        st.success("🎯 5-Year Simulation Completed!")

# =====================================================
# RESET
# =====================================================

if st.button("🔄 Restart Simulation"):
    st.session_state.clear()
    st.rerun()
