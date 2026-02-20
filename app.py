if st.button("🚀 Run 5-Year Simulation"):

    years = 5
    results = []

    monthly_demand = BASE_MONTHLY_DEMAND
    effective_breakdown = BREAKDOWN_PROB * (1 - maintenance_eff)

    total_5yr_cost = 0
    total_5yr_units = 0

    for year in range(1, years + 1):

        # ===============================
        # RANDOM DEMAND GROWTH (-10% to +25%)
        # ===============================

        demand_growth = np.random.uniform(-0.10, 0.25)

        monthly_demand *= (1 + demand_growth)
        yearly_demand = monthly_demand * 12

        # ===============================
        # RANDOM INFLATION (6% to 12%)
        # ===============================

        actual_inflation = np.random.uniform(0.06, 0.12)

        # ===============================
        # CAPACITY CALCULATION
        # ===============================

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

        # Strategic investment
        if investment_year == year:
            capacities[bottleneck] *= 1.2

        throughput = min(capacities.values())

        # ===============================
        # COST CALCULATION
        # ===============================

        machine_cost = 400 * sum(capacities.values())
        labor_cost = 50 * overtime * 12
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

    st.subheader("📉 Demand Growth Volatility")
    st.line_chart(df.set_index("Year")["Demand Growth (%)"])

    st.subheader("📊 Inflation Variability")
    st.line_chart(df.set_index("Year")["Inflation (%)"])

    st.subheader("🧠 Managerial Insight")

    if df["Demand Growth (%)"].min() < 0:
        st.warning("Negative demand growth observed. Capacity flexibility becomes critical.")
    else:
        st.success("Stable demand environment observed during simulation.")

    st.info(f"Most Frequent Bottleneck Stage: {df['Bottleneck Stage'].mode()[0]}")
