import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="SmartFlow AI", layout="wide")

st.title("🚗 SmartFlow AI – 5-Year Automobile Production Optimizer")

st.markdown("""
This simulation models a 4-stage automobile manufacturing flow shop 
over a 5-year horizon to minimize cost per unit while meeting demand.
""")

# ===============================
# FIXED SYSTEM PARAMETERS
# ===============================

BASE_DEMAND = 10000  # Monthly demand
BREAKDOWN_PROB = 0.08
SETUP_TIME = 45  # minutes
AVAILABLE_HOURS_MONTH = 160

st.sidebar.header("🔒 Fixed Parameters")
st.sidebar.write(f"Base Monthly Demand: {BASE_DEMAND}")
st.sidebar.write(f"Breakdown Probability: {BREAKDOWN_PROB}")
st.sidebar.write(f"Setup Time (mins): {SETUP_TIME}")
st.sidebar.write(f"Available Hours/Month: {AVAILABLE_HOURS_MONTH}")

# ===============================
# DECISION VARIABLES
# ===============================

st.header("⚙️ Decision Variables")

col1, col2 = st.columns(2)

with col1:
    machines_body = st.number_input("Machines – Body Shop", 1, 20, 3)
    machines_paint = st.number_input("Machines – Paint Shop", 1, 20, 2)
    machines_engine = st.number_input("Machines – Engine Assembly", 1, 20, 3)
    machines_final = st.number_input("Machines – Final Assembly", 1, 20, 4)

with col2:
    overtime = st.number_input("Overtime Hours per Month", 0, 200, 20)
    maintenance_eff = st.slider("Maintenance Efficiency (0–1)", 0.0, 1.0, 0.5)
    annual_demand_growth = st.slider("Annual Demand Growth (%)", 0, 20, 5)
    annual_cost_inflation = st.slider("Annual Cost Inflation (%)", 0, 15, 3)

investment_year = st.selectbox(
    "Add 1 Extra Machine to Bottleneck in Year:",
    [None, 2, 3, 4, 5]
)

# ===============================
# RUN SIMULATION
# ===============================

if st.button("🚀 Run 5-Year Simulation"):

    years = 5
    results = []

    monthly_demand = BASE_DEMAND
    effective_breakdown = BREAKDOWN_PROB * (1 - maintenance_eff)

    total_5yr_cost = 0
    total_5yr_units = 0

    for year in range(1, years + 1):

        # Apply annual demand growth
        yearly_demand = monthly_demand * 12

        # Calculate yearly available hours
        yearly_hours = AVAILABLE_HOURS_MONTH * 12

        # Effective capacity per stage
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

        # Strategic Investment
        if investment_year == year:
            capacities[bottleneck] *= 1.2  # Increase bottleneck capacity by 20%

        throughput = min(capacities.values())

        # Cost Inflation Adjustment
        inflation_multiplier = (1 + annual_cost_inflation / 100) ** (year - 1)

        machine_cost = 400 * sum(capacities.values()) * inflation_multiplier
        labor_cost = 50 * overtime * 12 * inflation_multiplier
        setup_cost = SETUP_TIME * 12 * 10
        penalty_cost = 20000 if throughput < yearly_demand else 0

        total_cost = machine_cost + labor_cost + setup_cost + penalty_cost

        units_produced = min(throughput, yearly_demand)
        cost_per_unit = total_cost / units_produced

        total_5yr_cost += total_cost
        total_5yr_units += units_produced

        results.append([
            year,
            yearly_demand,
            throughput,
            bottleneck,
            total_cost,
            cost_per_unit
        ])

        # Increase demand for next year
        monthly_demand *= (1 + annual_demand_growth / 100)

    df = pd.DataFrame(results, columns=[
        "Year",
        "Demand",
        "Throughput",
        "Bottleneck Stage",
        "Total Cost",
        "Cost per Unit"
    ])

    avg_cost_5yr = total_5yr_cost / total_5yr_units

    # ===============================
    # DISPLAY RESULTS
    # ===============================

    st.subheader("📊 5-Year Simulation Results")
    st.dataframe(df, use_container_width=True)

    colA, colB, colC = st.columns(3)

    colA.metric("Average Cost per Unit (5-Year)", f"₹{avg_cost_5yr:,.2f}")
    colB.metric("Total Units Produced (5-Year)", f"{int(total_5yr_units):,}")
    colC.metric("Total 5-Year Cost", f"₹{int(total_5yr_cost):,}")

    st.subheader("📈 Demand vs Throughput")
    st.line_chart(df.set_index("Year")[["Demand", "Throughput"]])

    st.subheader("💰 Cost per Unit Trend")
    st.line_chart(df.set_index("Year")["Cost per Unit"])

    # ===============================
    # MANAGERIAL INSIGHT
    # ===============================

    st.subheader("🧠 Managerial Insight")

    if avg_cost_5yr > 500:
        st.warning("Cost per unit is high. Consider earlier capacity expansion or improved maintenance strategy.")
    else:
        st.success("Cost structure appears stable. Capacity planning is aligned with demand growth.")

    st.info(f"Primary Bottleneck Across Years: {df['Bottleneck Stage'].mode()[0]}")
