import pypsa
import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

plt.style.use("bmh")

st.title("Decarbonizing Germany’s Electricity Supply: A Capacity Expansion Planning Model with PyPSA")

st.markdown("""
    <style>
        .justified-text {
            text-align: justify;
        }
    </style>
    <div class="justified-text">  
        As the world accelerates toward a carbon-neutral future, planning the transformation of electricity systems becomes critical.  
        This project leverages <b>PyPSA (Python for Power System Analysis)</b> to model and optimize Germany’s electricity network,  
        balancing <b>renewable energy expansion, system costs, and carbon constraints</b>. By allowing users to adjust <b>CO₂ emission limits</b>,  
        the model demonstrates how different policies impact the deployment of <b>solar, wind, gas, and storage technologies</b>,  
        helping policymakers and researchers explore pathways to a cleaner energy system. 
        
    </div>
    <div class="justified-text"> 
        The code integrates <b>real-world technology cost data</b>, <b>historical electricity demand</b>, and <b>renewable energy availability</b>  
        to build an interactive simulation. It enables users to experiment with <b>generation capacities, storage technologies, and CO₂ restrictions</b>,  
        optimizing the system to <b>minimize costs</b> while ensuring electricity demand is met. Through interactive visualizations,  
        the project provides insights into <b>energy dispatch</b>, <b>system costs</b>, and <b>the impact of decarbonization policies</b>,  
        making it a powerful tool for energy system planning.  
    </div>
""", unsafe_allow_html=True)

st.markdown("""
## **How to Use the App**  

### 1. Adjust Model Settings  
- Use the **sidebar slider** to set a CO₂ emission limit (in MtCO₂).  
- This determines how much carbon can be emitted by the electricity system.  

### 2. Explore the Data  
- Check the **technology cost table** to see capital and operational expenses.  
- View the **electricity demand time series** to understand the system’s energy needs.  
- Examine the **wind and solar capacity factors** to analyze renewable availability over time.  

### 3. Run the Optimization  
- Click the **"Optimize System"** button in the sidebar.  
- The model will compute the least-cost generation and storage mix under the given CO₂ constraint.  
- Results include:  
  - **Optimized generation and storage capacities**  
  - **System cost breakdown (capital vs operational expenses)**  
  - **Energy dispatch visualization over time**  

### 4. Perform Sensitivity Analysis  
- The app automatically runs **a sensitivity analysis on different CO₂ limits**.  
- View how system costs change with stricter or looser emission constraints.  

This interactive tool provides a hands-on way to explore **capacity expansion planning**,  
making it easier to understand the economic and technical trade-offs in the transition to a low-carbon electricity system.  
""")

st.sidebar.header("Model Settings")

# User-Controlled CO₂ Limit
co2_limit = st.sidebar.slider("Set CO₂ Emission Limit (MtCO₂)", min_value=0, max_value=200, value=50, step=10) * 1e6  # Convert to tons

st.markdown("""
## Data Overview
This model uses:
- **Technology Costs (from PyPSA technology data, 2030)**
- **Electricity Demand and Renewable Generation Time Series (Germany 2015)**
""")

# Load and Visualize Data
year = 2030
url = f"https://raw.githubusercontent.com/PyPSA/technology-data/master/outputs/costs_{year}.csv"
costs = pd.read_csv(url, index_col=[0, 1])

costs.loc[costs.unit.str.contains("/kW"), "value"] *= 1e3
costs.unit = costs.unit.str.replace("/kW", "/MW")

defaults = {
    "FOM": 0,
    "VOM": 0,
    "efficiency": 1,
    "fuel": 0,
    "investment": 0,
    "lifetime": 25,
    "CO2 intensity": 0,
    "discount rate": 0.07,
}
costs = costs.value.unstack().fillna(defaults)

costs.at["OCGT", "fuel"] = costs.at["gas", "fuel"]
costs.at["CCGT", "fuel"] = costs.at["gas", "fuel"]
costs.at["OCGT", "CO2 intensity"] = costs.at["gas", "CO2 intensity"]
costs.at["CCGT", "CO2 intensity"] = costs.at["gas", "CO2 intensity"]

def annuity(r, n):
    return r / (1.0 - 1.0 / (1.0 + r) ** n)

costs["marginal_cost"] = costs["VOM"] + costs["fuel"] / costs["efficiency"]
annuity_values = costs.apply(lambda x: annuity(x["discount rate"], x["lifetime"]), axis=1)
costs["capital_cost"] = (annuity_values + costs["FOM"] / 100) * costs["investment"]

# Filter only selected technologies and remove rows with NaN values
selected_techs = ["onwind", "offwind", "solar", "OCGT", "hydrogen storage underground", "battery storage", "battery inverter", "electrolysis", "fuel cell"]
costs = costs.loc[selected_techs]

color_mapping = {
        "onwind": "dodgerblue", "offwind": "aquamarine", "solar": "gold",
        "OCGT": "indianred", "hydrogen storage underground": "magenta",
        "battery storage": "yellowgreen"
}

if not costs.empty:
    st.subheader("Technology Costs Overview")
    st.write(costs.dropna(how='all', axis=0).dropna(how='all', axis=1))

# Load Time-Series Data
url = "https://tubcloud.tu-berlin.de/s/pKttFadrbTKSJKF/download/time-series-lecture-2.csv"
ts = pd.read_csv(url, index_col=0, parse_dates=True)
ts.load *= 1e3  # Convert load to MW
resolution = 4
ts = ts.resample(f"{resolution}h").first()

# Show Demand Time-Series
st.subheader("Electricity Demand Time Series")
fig = px.line(ts, x=ts.index, y="load", labels={"load": "Electricity Demand (MW)", "index": "Time"})
fig.update_layout(title="Electricity Demand Over Time", xaxis_title="Time", yaxis_title="MW", height=400)
st.plotly_chart(fig, use_container_width=True)

# Show Wind and Solar Capacity Factors 
st.subheader("Wind and Solar Capacity Factors")
ts_filtered = ts[["onwind", "offwind", "solar"]].reset_index()
ts_melted = ts_filtered.melt(id_vars="index", var_name="Technology", value_name="Capacity Factor")

fig = px.line(ts_melted, x="index", y="Capacity Factor", color="Technology",
              labels={"index": "Time", "Capacity Factor": "Capacity Factor"},
              title="Wind and Solar Capacity Factors Over Time",
              color_discrete_map=color_mapping)
fig.update_layout(xaxis_title="Time", yaxis_title="Capacity Factor", height=400)
st.plotly_chart(fig, use_container_width=True)

# Initialize Network
n = pypsa.Network()
n.add("Bus", "electricity")
n.set_snapshots(ts.index)
n.snapshot_weightings.loc[:, :] = resolution

# Add Technologies
n.add("Carrier", selected_techs, co2_emissions=[costs.at[c, "CO2 intensity"] for c in selected_techs])

# Add Loads
n.add("Load", "demand", bus="electricity", p_set=ts.load)

# Add Generators
for tech in selected_techs[:3]:  # Only onwind, offwind, solar
    n.add("Generator", tech, bus="electricity", carrier=tech, p_max_pu=ts[tech],
          capital_cost=costs.at[tech, "capital_cost"], marginal_cost=costs.at[tech, "marginal_cost"],
          efficiency=costs.at[tech, "efficiency"], p_nom_extendable=True)

n.add("Generator", "OCGT", bus="electricity", carrier="OCGT",
      capital_cost=costs.at["OCGT", "capital_cost"], marginal_cost=costs.at["OCGT", "marginal_cost"],
      efficiency=costs.at["OCGT", "efficiency"], p_nom_extendable=True)

# Add Storage Units with energy-to-power ratio of 6 h
n.add("StorageUnit", "battery storage", bus="electricity", carrier="battery storage",
      max_hours=6, capital_cost=costs.at["battery inverter", "capital_cost"] + 6 * costs.at["battery storage", "capital_cost"],
      efficiency_store=costs.at["battery inverter", "efficiency"], efficiency_dispatch=costs.at["battery inverter", "efficiency"],
      p_nom_extendable=True, cyclic_state_of_charge=True)

# Add Hydrogen Storage with energy-to-power ratio of 168 h 
capital_costs = (costs.at["electrolysis", "capital_cost"] + costs.at["fuel cell", "capital_cost"] + 168 * costs.at["hydrogen storage underground", "capital_cost"])
n.add("StorageUnit", "hydrogen storage underground", bus="electricity", carrier="hydrogen storage underground",
      max_hours=168, capital_cost=capital_costs,
      efficiency_store=costs.at["electrolysis", "efficiency"], efficiency_dispatch=costs.at["fuel cell", "efficiency"],
      p_nom_extendable=True, cyclic_state_of_charge=True)
    
# Optimize Model
st.sidebar.subheader("Run Optimization")
if st.sidebar.button("Optimize System"):
    sensitivity = {}  # Reset sensitivity on each run
    for co2 in all_co2_values:
        # Remove old CO2 constraint
        if "CO2Limit" in n.global_constraints.index:
            n.global_constraints.drop("CO2Limit", inplace=True)

    n.add("GlobalConstraint", "CO2Limit", carrier_attribute="co2_emissions", sense="<=", constant=0)
    n.optimize(solver_name="highs")

    # Show Optimization Results
    st.header("Optimized Generator Capacities (MW)")
    st.write(n.generators.p_nom_opt)
    
    st.header("Optimized Storage Capacities (GWh)")
    st.write(n.storage_units.p_nom_opt * n.storage_units.max_hours / 1e3)

    # Show System Cost Breakdown with Stackable Bar Chart
    def system_cost(n):
        tsc = pd.concat([n.statistics.capex(), n.statistics.opex()], axis=1)
        return tsc.sum(axis=1).droplevel(0).div(1e9).round(2)  # billion €/a
    
    st.subheader("System Cost Breakdown (in billion €/a)")
    cost_df = system_cost(n)

    fig = px.bar(cost_df, x=cost_df.index, y=cost_df.values, labels={"x": "Technology", "y": "Cost (bn €/a)"},
                 title="System Cost Breakdown", text=cost_df.values,
                 color=cost_df.index, color_discrete_map=color_mapping)
    fig.update_layout(barmode='stack', xaxis_title="Technology", yaxis_title="Cost (billion €/a)")
    st.plotly_chart(fig, use_container_width=True)

    # Show Energy Dispatch Chart
    def plot_dispatch(n):
    # Prepare energy balance data
        p = (
            n.statistics.energy_balance(aggregate_time=False)
            .groupby("carrier")
            .sum()
            .div(1e3)
            .drop("-")
            .T
        )

        # Create figure using Plotly
        fig = go.Figure()

        # Plot positive values (generation)
        for carrier in p.columns:
            generation = p[carrier][p[carrier] > 0]
            if not generation.empty:
                fig.add_trace(go.Scatter(
                    x=generation.index,
                    y=generation.values,
                    fill='tonexty',
                    mode='none',
                    name=carrier,
                    fillcolor=color_mapping.get(carrier, 'gray'),  # Use the color mapping
                ))

        # Plot negative values (charge/discharge)
        for carrier in p.columns:
            charge = p[carrier][p[carrier] < 0]
            if not charge.empty:
                fig.add_trace(go.Scatter(
                    x=charge.index,
                    y=charge.values,
                    fill='tonexty',
                    mode='none',
                    name=carrier,
                    fillcolor=color_mapping.get(carrier, 'gray'),  # Use the color mapping
                    showlegend=False  # Don't include charge in legend if you don't want it
                ))

        # Plot total load (as black line)
        total_load = n.loads_t.p_set.sum(axis=1) / 1e3  # In GW
        fig.add_trace(go.Scatter(
            x=total_load.index,
            y=total_load.values,
            mode='lines',
            name="Load",
            line=dict(color='black', width=2)
        ))

        # Customize layout
        fig.update_layout(
            title="Energy Dispatch Over Time",
            xaxis_title="Time",
            yaxis_title="Energy (GW)",
            showlegend=True,
            height=500
        )
    
        st.plotly_chart(fig, use_container_width=True)
        
    plot_dispatch(n)
    
    # Run Sensitivity Analysis 
    all_co2_values = [0, 25, 50, 100, 150, 200]
    
    # Sensitivity Analysis
    sensitivity = {}
    for co2 in all_co2_values:
        n.global_constraints.loc["CO2Limit", "constant"] = co2 * 1e6
        n.optimize(solver_name="highs")
        sensitivity[co2] = system_cost(n)
    
    df = pd.DataFrame(sensitivity).T  # Convert to DataFrame

    fig = px.area(df, x=df.index, y=df.columns, title="System Cost vs CO₂ Emissions",
                  labels={"index": "CO₂ Emissions (MtCO₂)", "value": "System Cost (bn€/a)"},
                  color_discrete_map=color_mapping)
    fig.update_xaxes(range=[0, 150], title="CO₂ Emissions (MtCO₂)")
    fig.update_yaxes(range=[0, 100], title="System Cost (bn€/a)")
    
    st.plotly_chart(fig, use_container_width=True)
