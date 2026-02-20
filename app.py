import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="SmartFlow AI", layout="wide")

st.title("🚗 SmartFlow AI – 5-Year Production & Inventory Simulator")

st.markdown("""
Dynamic rolling production system with stage-level heterogeneity,
inventory carryover, cost breakdown and bottleneck detection.
""")

# =====================================================
# FIXED PARAMETERS
# =====================================================

BASE_MONTHLY_DEMAND = 10000
BREAKDOWN_PROB = 0.08
AVAILABLE_HOURS_MONTH = 160
UNITS_PER_MACHINE_PER_HOUR = 7

# Stage productivity factors
BODY_FACTOR = 5
PAINT_FACTOR = 7
ENGINE_FACTOR = 3
FINAL_FACTOR = 4

# Costs
MACHINE_COST_PER_HOUR = 400
LABOR_COST_PER_HOUR = 50
SETUP_COST_PER_YEAR = 5400
HOLDING_COST_PER_UNIT = 50
SHORTAGE_PENALTY_PER_UNIT = 200

# =====================================================
# SIDEBAR
# =====================================================

st.sidebar.header("🔒 System Assumptions")
st.sidebar.write("Initial Monthly Demand: 10,000")
st.sidebar.write("Demand Growth: Random (-10% to +25%)")
st.sidebar.write("Inflation: Random (6% to 12%)")
st.sidebar.write(f"Units per Machine per Hour: {UNITS_PER_MACHINE_PER_HOUR}")
st.sidebar.write("Stage Productivity Factors:")
st.sidebar.write(f"Body: {BODY_FACTOR}")
st.sidebar.write(f"Paint: {PAINT_FACTOR}")
st.sidebar.write(f"Engine: {ENGINE_FACTOR}")
st.sidebar.write(f"Final: {FINAL_FACTOR}")

# =====================================================
# SESSION STATE SAFE INIT
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

    yearly_hours = AVAILABLE_HOURS_MONTH * 12
    total_machines = machines_body + machines_paint + machines_engine + machines_final

    # =====================================================
    # LIVE COST PREVIEW
    # =====================================================

    machine_cost_preview = MACHINE_COST_PER_HOUR * total_machines * yearly_hours
    labor_cost_preview = LABOR_COST_PER_HOUR * overtime * 12

    st.subheader("💰 Estimated Base Cost Preview")
    c1, c2 = st.columns(2)
    c1.metric("Machine Cost (Est.)", f"₹{machine_cost_preview:,.0f}")
    c2.metric("Labor Cost (Est.)", f"₹{labor_cost_preview:,.0f}")

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

        # Effective Breakdown
        effective_breakdown = BREAKDOWN_PROB * (1 - maintenance_eff)

        base_capacity = yearly_hours * UNITS_PER_MACHINE_PER_HOUR * (1 - effective_breakdown)

        # Stage Capacities
        cap_body = machines_body * base_capacity * BODY_FACTOR
        cap_paint = machines_paint * base_capacity * PAINT_FACTOR
        cap_engine = machines_engine * base_capacity * ENGINE_FACTOR
        cap_final = machines_final * base_capacity * FINAL_FACTOR

        capacities = {
            "Body": cap_body,
            "Paint": cap_paint,
            "Engine": cap_engine,
            "Final": cap_final
        }

        bottleneck_stage = min(capacities, key=capacities.get)
        production = capacities[bottleneck_stage]

        # Inventory Logic
        available_units = production + st.session_state.inventory
        units_sold = min(yearly_demand, available_units)
        ending_inventory = max(available_units - yearly_demand, 0)
        shortage = max(yearly_demand - available_units, 0)

        # Cost Components
        machine_cost = machine_cost_preview
        labor_cost = labor_cost_preview
        setup_cost = SETUP_COST_PER_YEAR
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
            "Bottleneck": bottleneck_stage,
            "Machine Cost": round(machine_cost),
            "Labor Cost": round(labor_cost),
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

        st.success(f"Year {current_year} completed. Bottleneck: {bottleneck_stage}")
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

    st.subheader("📦 Inventory Trend")
    st.line_chart(df.set_index("Year")["Ending Inventory"])

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
