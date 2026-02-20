import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="SmartFlow AI", layout="wide")

st.title("🚗 SmartFlow AI – Rolling 5-Year Production Simulator")

st.markdown("""
Each year you make decisions. The system responds with demand volatility and inflation shocks.
Strategy evolves year by year.
""")

# ===============================
# FIXED PARAMETERS
# ===============================

BASE_MONTHLY_DEMAND = 10000
BREAKDOWN_PROB = 0.08
SETUP_TIME = 45
AVAILABLE_HOURS_MONTH = 160

st.sidebar.header("🔒 System Assumptions")
st.sidebar.write("Initial Monthly Demand: 10,000")
st.sidebar.write("Demand Growth: Random (-10% to +25%)")
st.sidebar.write("Inflation: Random (6% to 12%)")

# ===============================
# SESSION STATE INITIALIZATION
# ===============================

if "year" not in st.session_state:
    st.session_state.year = 1
    st.session_state.monthly_demand = BASE_MONTHLY_DEMAND
    st.session_state.results = []
    st.session_state.total_cost = 0
    st.session_state.total_units = 0

# ===============================
# CURRENT YEAR DISPLAY
# ===============================

current_year = st.session_state.year

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

    if st.button("Simulate This Year"):

        # ===============================
        # DEMAND SHOCK
        # ===============================

        demand_growth = np.random.uniform(-0.10, 0.25)
        st.session_state.monthly_demand *= (1 + demand_growth)
        yearly_demand = st.session_state.monthly_demand * 12

        # ===============================
        # INFLATION SHOCK
        # ===============================

        inflation = np.random.uniform(0.06, 0.12)

        # ===============================
        # CAPACITY
        # ===============================

        effective_breakdown = BREAKDOWN_PROB * (1 - maintenance_eff)
        yearly_hours = AVAILABLE_HOURS_MONTH * 12

        cap_body = machines_body * yearly_hours * (1 - effective_breakdown)
        cap_paint = machines_paint * yearly_hours * (1 - effective_breakdown)
        cap_engine = machines_engine * yearly_hours * (1 - effective_breakdown)
        cap_final = machines_final * yearly_hours * (1 - effective_breakdown)

        capacities = {
            "Body Shop": cap_body,
            "Paint Shop": cap_paint,
            "Engine Assembly": cap_engine,
            "Final Assembly": cap_final
        }

        bottleneck = min(capacities, key=capacities.get)
        throughput = min(capacities.values())

        # ===============================
        # COST
        # ===============================

        machine_cost = 400 * sum(capacities.values())
        labor_cost = 50 * overtime * 12
        setup_cost = SETUP_TIME * 12 * 10
        penalty_cost = 20000 if throughput < yearly_demand else 0

        total_cost = (machine_cost + labor_cost + setup_cost + penalty_cost) * (1 + inflation)
        units_produced = min(throughput, yearly_demand)
        cost_per_unit = total_cost / units_produced

        # ===============================
        # STORE RESULTS
        # ===============================

        st.session_state.total_cost += total_cost
        st.session_state.total_units += units_produced

        st.session_state.results.append([
            current_year,
            demand_growth * 100,
            yearly_demand,
            inflation * 100,
            throughput,
            bottleneck,
            total_cost,
            cost_per_unit
        ])

        st.session_state.year += 1

        st.success(f"Year {current_year} simulated successfully!")

        st.rerun()

# ===============================
# DISPLAY FINAL RESULTS
# ===============================

if st.session_state.year > 1:

    df = pd.DataFrame(st.session_state.results, columns=[
        "Year",
        "Demand Growth (%)",
        "Demand",
        "Inflation (%)",
        "Throughput",
        "Bottleneck",
        "Total Cost",
        "Cost per Unit"
    ])

    st.subheader("📊 Simulation Progress")
    st.dataframe(df, use_container_width=True)

    avg_cost = st.session_state.total_cost / st.session_state.total_units

    colA, colB, colC = st.columns(3)
    colA.metric("Cumulative Avg Cost per Unit", f"₹{avg_cost:,.2f}")
    colB.metric("Total Units Produced", f"{int(st.session_state.total_units):,}")
    colC.metric("Total Cost So Far", f"₹{int(st.session_state.total_cost):,}")

    st.subheader("📈 Demand vs Throughput")
    st.line_chart(df.set_index("Year")[["Demand", "Throughput"]])

    st.subheader("💰 Cost Trend")
    st.line_chart(df.set_index("Year")["Cost per Unit"])

    if st.session_state.year > 5:
        st.success("5-Year Simulation Completed!")

# ===============================
# RESET BUTTON
# ===============================

if st.button("🔄 Restart Simulation"):
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()
