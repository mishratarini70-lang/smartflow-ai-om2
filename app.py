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
    annual_co_
