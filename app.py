import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

st.title("🚗 SmartFlow AI - Automobile Production Optimizer")

st.markdown("Optimize cost per unit while meeting fixed demand.")

# -----------------------
# FIXED PARAMETERS
# -----------------------

DEMAND = 10000
BREAKDOWN_PROB = 0.08
SETUP_TIME = 45

st.sidebar.header("Fixed Parameters")
st.sidebar.write(f"Monthly Demand: {DEMAND}")
st.sidebar.write(f"Breakdown Probability: {BREAKDOWN_PROB}")
st.sidebar.write(f"Setup Time (mins): {SETUP_TIME}")

# -----------------------
# DECISION VARIABLES
# -----------------------

st.header("Decision Variables")

batch_size = st.number_input("Batch Size", 100, 5000, 1000)
machines_body = st.number_input("Machines - Body Shop", 1, 10, 3)
machines_paint = st.number_input("Machines - Paint Shop", 1, 10, 2)
machines_engine = st.number_input("Machines - Engine Assembly", 1, 10, 3)
machines_final = st.number_input("Machines - Final Assembly", 1, 10, 4)

buffer = st.number_input("Buffer Capacity", 100, 5000, 1000)
overtime = st.number_input("Overtime Hours", 0, 200, 20)
maintenance_factor = st.slider("Maintenance Efficiency (0-1)", 0.0, 1.0, 0.5)

if st.button("Run Simulation"):

    available_time = 160  # monthly hours
    effective_breakdown = BREAKDOWN_PROB * (1 - maintenance_factor)

    capacity_body = machines_body * available_time * (1 - effective_breakdown)
    capacity_paint = machines_paint * available_time * (1 - effective_breakdown)
    capacity_engine = machines_engine * available_time * (1 - effective_breakdown)
    capacity_final = machines_final * available_time * (1 - effective_breakdown)

    capacities = {
        "Body": capacity_body,
        "Paint": capacity_paint,
        "Engine": capacity_engine,
        "Final": capacity_final
    }

    bottleneck = min(capacities, key=capacities.get)
    throughput = capacities[bottleneck]

    cycle_time = 10  # assumed average hours
    wip = throughput * cycle_time

    machine_cost = 500 * sum(capacities.values())
    labor_cost = 50 * overtime
    setup_cost = SETUP_TIME * 10
    penalty_cost = 1000 if throughput < DEMAND else 0

    total_cost = machine_cost + labor_cost + setup_cost + penalty_cost
    units_produced = min(throughput, DEMAND)
    cost_per_unit = total_cost / units_produced

    st.subheader("Results")
    st.write(f"Bottleneck Stage: {bottleneck}")
    st.write(f"Throughput: {throughput:.2f}")
    st.write(f"Units Produced: {units_produced:.2f}")
    st.write(f"Cost per Unit: ₹{cost_per_unit:.2f}")
    st.write(f"WIP: {wip:.2f}")

    st.bar_chart(capacities)

