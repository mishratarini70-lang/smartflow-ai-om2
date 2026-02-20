import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="SmartFlow AI", layout="wide")

st.title("🚗 SmartFlow AI – 5-Year Multi-Stage Production Simulator")

st.markdown("""
Multi-stage automobile production with:
• WIP inventory between stages  
• Finished goods inventory  
• Setup cost  
• Bottleneck detection  
• Demand & inflation uncertainty  
""")

# =====================================================
# FIXED PARAMETERS
# =====================================================

BASE_MONTHLY_DEMAND = 10000
BREAKDOWN_PROB = 0.08
AVAILABLE_HOURS_MONTH = 160
UNITS_PER_MACHINE_PER_HOUR = 7

BODY_FACTOR = 5
PAINT_FACTOR = 7
ENGINE_FACTOR = 3
FINAL_FACTOR = 4

# Costs
MACHINE_COST_PER_HOUR = 400
LABOR_COST_PER_HOUR = 50
SETUP_COST_PER_MACHINE = 100000
HOLDING_COST_PER_UNIT = 50
SHORTAGE_COST_PER_UNIT = 200
WIP_HOLDING_COST_PER_UNIT = 30

# =====================================================
# SESSION STATE INIT
# =====================================================

defaults = {
    "year": 1,
    "monthly_demand": BASE_MONTHLY_DEMAND,
    "fg_inventory": 0,
    "wip_body": 0,
    "wip_paint": 0,
    "wip_engine": 0,
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
        overtime = st.number_input("Overtime Hours", 0, 200, 20)
        maintenance_eff = st.slider("Maintenance Efficiency", 0.0, 1.0, 0.5)

    yearly_hours = AVAILABLE_HOURS_MONTH * 12
    total_machines = machines_body + machines_paint + machines_engine + machines_final

    # ==============================
    # COST PREVIEW
    # ==============================

    machine_cost_preview = MACHINE_COST_PER_HOUR * total_machines * yearly_hours
    setup_cost_preview = SETUP_COST_PER_MACHINE * total_machines
    labor_cost_preview = LABOR_COST_PER_HOUR * overtime * 12

    st.subheader("💰 Estimated Base Cost Preview")
    c1, c2, c3 = st.columns(3)
    c1.metric("Machine Cost", f"₹{machine_cost_preview:,.0f}")
    c2.metric("Setup Cost", f"₹{setup_cost_preview:,.0f}")
    c3.metric("Labor Cost", f"₹{labor_cost_preview:,.0f}")

    # =====================================================
    # SIMULATE
    # =====================================================

    if st.button("Simulate This Year"):

        # Demand shock
        demand_growth = np.random.uniform(-0.10, 0.25)
        st.session_state.monthly_demand *= (1 + demand_growth)
        yearly_demand = st.session_state.monthly_demand * 12

        inflation = np.random.uniform(0.06, 0.12)

        effective_breakdown = BREAKDOWN_PROB * (1 - maintenance_eff)
        base_capacity = yearly_hours * UNITS_PER_MACHINE_PER_HOUR * (1 - effective_breakdown)

        # Stage capacities
        cap_body = machines_body * base_capacity * BODY_FACTOR
        cap_paint = machines_paint * base_capacity * PAINT_FACTOR
        cap_engine = machines_engine * base_capacity * ENGINE_FACTOR
        cap_final = machines_final * base_capacity * FINAL_FACTOR

        # =====================================================
        # STAGE FLOW WITH WIP
        # =====================================================

        # Body Stage
        body_output = min(cap_body, cap_body + st.session_state.wip_body)
        st.session_state.wip_body = max(st.session_state.wip_body + cap_body - body_output, 0)

        # Paint Stage
        paint_input = body_output + st.session_state.wip_paint
        paint_output = min(cap_paint, paint_input)
        st.session_state.wip_paint = max(paint_input - paint_output, 0)

        # Engine Stage
        engine_input = paint_output + st.session_state.wip_engine
        engine_output = min(cap_engine, engine_input)
        st.session_state.wip_engine = max(engine_input - engine_output, 0)

        # Final Stage
        final_input = engine_output
        final_output = min(cap_final, final_input)

        production = final_output

        # =====================================================
        # FINISHED GOODS INVENTORY
        # =====================================================

        available_units = production + st.session_state.fg_inventory
        units_sold = min(yearly_demand, available_units)
        ending_inventory = max(available_units - yearly_demand, 0)
        shortage = max(yearly_demand - available_units, 0)

        st.session_state.fg_inventory = ending_inventory

        # =====================================================
        # COSTS
        # =====================================================

        holding_cost_fg = ending_inventory * HOLDING_COST_PER_UNIT
        holding_cost_wip = (
            st.session_state.wip_body +
            st.session_state.wip_paint +
            st.session_state.wip_engine
        ) * WIP_HOLDING_COST_PER_UNIT

        shortage_cost = shortage * SHORTAGE_COST_PER_UNIT

        total_cost = (
            machine_cost_preview +
            setup_cost_preview +
            labor_cost_preview +
            holding_cost_fg +
            holding_cost_wip +
            shortage_cost
        ) * (1 + inflation)

        cost_per_unit = total_cost / max(units_sold, 1)

        # Store results
        st.session_state.results.append({
            "Year": current_year,
            "Demand": round(yearly_demand),
            "Production": round(production),
            "Units Sold": round(units_sold),
            "FG Inventory": round(ending_inventory),
            "WIP Body": round(st.session_state.wip_body),
            "WIP Paint": round(st.session_state.wip_paint),
            "WIP Engine": round(st.session_state.wip_engine),
            "Machine Cost": round(machine_cost_preview),
            "Setup Cost": round(setup_cost_preview),
            "Labor Cost": round(labor_cost_preview),
            "Holding Cost (FG)": round(holding_cost_fg),
            "Holding Cost (WIP)": round(holding_cost_wip),
            "Shortage Cost": round(shortage_cost),
            "Inflation (%)": round(inflation * 100, 2),
            "Total Cost": round(total_cost),
            "Cost per Unit": round(cost_per_unit, 2)
        })

        st.session_state.total_cost += total_cost
        st.session_state.total_units += units_sold
        st.session_state.year += 1

        st.success(f"Year {current_year} simulated.")
        st.rerun()

# =====================================================
# RESULTS DISPLAY
# =====================================================

if len(st.session_state.results) > 0:

    df = pd.DataFrame(st.session_state.results)

    st.subheader("📊 Simulation Results")
    st.dataframe(df, use_container_width=True)

    avg_cost = st.session_state.total_cost / max(st.session_state.total_units, 1)

    c1, c2, c3 = st.columns(3)
    c1.metric("Avg Cost per Unit", f"₹{avg_cost:,.2f}")
    c2.metric("Total Units Sold", f"{int(st.session_state.total_units):,}")
    c3.metric("Finished Goods Inventory", f"{int(st.session_state.fg_inventory):,}")

    st.subheader("📈 Demand vs Production")
    st.line_chart(df.set_index("Year")[["Demand", "Production"]])

    st.subheader("📦 FG Inventory Trend")
    st.line_chart(df.set_index("Year")["FG Inventory"])

# =====================================================
# RESET
# =====================================================

if st.button("🔄 Restart Simulation"):
    st.session_state.clear()
    st.rerun()
