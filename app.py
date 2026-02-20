import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="SmartFlow AI", layout="wide")

st.title("🚗 SmartFlow AI – 5-Year Dynamic Production Simulator")

st.markdown("""
Dynamic 5-year automobile production optimization under demand 
and inflation uncertainty. Managers can adjust decisions yearly.
""")

# ===============================
# FIXED PARAMETERS
# ===============================

BASE_MONTHLY_DEMAND = 10000
BREAKDOWN_PROB = 0.08
SETUP_TIME = 45
AVAILABLE_HOURS_MONTH = 160

st.sidebar.header("🔒 Fixed System Parameters")
st.sidebar.write("Starting Monthly Demand (Year 0): 10,000")
st.sidebar.write("Demand Growth Random: -10% to +25%")
st.sidebar.write("Inflation Random: 6% to 12%")

# ===============================
# YEARLY DECISION INPUTS
# ===============================

st.header("⚙️ Yearly Decision Inputs")

years = 5
yearly_inputs = []

for year in range(1, years + 1):

    st.subheader(f"Year {year} Decisions")

    col1, col2 = st.columns(2)

    with col1:
        machines_body = st.number_input(f"Body Machines Y{year}", 1, 20, 3, key=f"body{year}")
        machines_paint = st.number_input(f"Paint Machines Y{year}", 1, 20, 2, key=f"paint{year}")
        machines_engine = st.number_input(f"Engine Machines Y{year}", 1, 20, 3, key=f"engine{year}")
        machines_final = st.number_input(f"Final Machines Y{year}", 1, 20, 4, key=f"final{year}")

    with col2:
        overtime = st.number_input(f"Overtime Hours Y{year}", 0, 200, 20, key=f"ot{year}")
        maintenance_eff = st.slider(f"Maintenance Efficiency Y{year}", 0.0, 1.0, 0.5, key=f"maint{year}")

    yearly_inputs.append({
        "machines_body": machines_body,
        "machines_paint": machines_paint,
        "machines_engine": machines_engine,
        "machines_final": machines_final,
        "overtime": overtime,
        "maintenance_eff": maintenance_eff
    })

# ===============================
# RUN SIMULATION
# ===============================

if st.button("🚀 Run 5-Year Dynamic Simulation"):

    monthly_demand = BASE_MONTHLY_DEMAND
    total_5yr_cost = 0
    total_5yr_units = 0
    results = []

    for year in range(1, years + 1):

        inputs = yearly_inputs[year - 1]

        # ===============================
        # RANDOM DEMAND GROWTH
        # ===============================
        demand_growth = np.random.uniform(-0.10, 0.25)
        monthly_demand *= (1 + demand_growth)
        yearly_demand = monthly_demand * 12

        # ===============================
        # RANDOM INFLATION
        # ===============================
        actual_inflation = np.random.uniform(0.06, 0.12)

        # ===============================
        # CAPACITY
        # ===============================
        effective_breakdown = BREAKDOWN_PROB * (1 - inputs["maintenance_eff"])
        yearly_hours = AVAILABLE_HOURS_MONTH * 12

        cap_body = inputs["machines_body"] * yearly_hours * (1 - effective_breakdown)
        cap_paint = inputs["machines_paint"] * yearly_hours * (1 - effective_breakdown)
        cap_engine = inputs["machines_engine"] * yearly_hours * (1 - effective_breakdown)
        cap_final = inputs["machines_final"] * yearly_hours * (1 - effective_breakdown)

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
        labor_cost = 50 * inputs["overtime"] * 12
        setup_cost = SETUP_TIME * 12 * 10
        penalty_cost = 20000 if throughput < yearly_demand else 0

        total_cost = (machine_cost + labor_cost + setup_cost + penalty_cost) * (1 + actual_inflation)

        units_produced = min(throughput, yearly_demand)
        cost_per_unit = total_cost / units_produced

        total_5yr_cost += total_cost
        total_5yr_units += units_produced

        results.append([
            year,
            demand_growth * 100,
            yearly_demand,
            actual_inflation * 100,
            throughput,
            bottleneck,
            total_cost,
            cost_per_unit
        ])

    df = pd.DataFrame(results, columns=[
        "Year",
        "Demand Growth (%)",
        "Demand",
        "Inflation (%)",
        "Throughput",
        "Bottleneck Stage",
        "Total Cost",
        "Cost per Unit"
    ])

    avg_cost_5yr = total_5yr_cost / total_5yr_units

    # ===============================
    # DISPLAY
    # ===============================

    st.subheader("📊 5-Year Results")
    st.dataframe(df, use_container_width=True)

    colA, colB, colC = st.columns(3)
    colA.metric("Average Cost per Unit (5-Year)", f"₹{avg_cost_5yr:,.2f}")
    colB.metric("Total Units Produced", f"{int(total_5yr_units):,}")
    colC.metric("Total 5-Year Cost", f"₹{int(total_5yr_cost):,}")

    st.subheader("📈 Demand vs Throughput")
    st.line_chart(df.set_index("Year")[["Demand", "Throughput"]])

    st.subheader("💰 Cost per Unit Trend")
    st.line_chart(df.set_index("Year")["Cost per Unit"])

    st.subheader("📉 Demand Volatility")
    st.line_chart(df.set_index("Year")["Demand Growth (%)"])

    st.subheader("📊 Inflation Volatility")
    st.line_chart(df.set_index("Year")["Inflation (%)"])

    st.subheader("🧠 Managerial Insight")

    if df["Demand Growth (%)"].min() < 0:
        st.warning("Demand contraction observed. Flexible capacity strategy is critical.")
    else:
        st.success("Demand growth remained positive during simulation.")

    st.info(f"Most Frequent Bottleneck: {df['Bottleneck Stage'].mode()[0]}")
