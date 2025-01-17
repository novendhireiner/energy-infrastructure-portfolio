import pypsa
import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st
import plotly.express as px

plt.style.use("bmh")

st.title("Decarbonizing Electricity Supply with PyPSA")

st.markdown("""
## Project Overview
This project models and optimizes Germany’s electricity system using PyPSA (Python for Power System Analysis). 
It allows users to:

✅ Adjust CO₂ emission limits  
✅ Modify transmission expansion costs  
✅ Optimize renewable energy generation & grid capacity  
✅ Analyze energy dispatch & system costs  
✅ Perform sensitivity analysis on CO₂ policies  

The optimization minimizes total system costs while satisfying electricity demand using renewables (solar, wind) and transmission expansion.
""")

st.sidebar.header("Model Settings")

# 1️⃣ User-Controlled CO₂ Limit
co2_limit = st.sidebar.slider("Set CO₂ Emission Limit (MtCO₂)", min_value=0, max_value=200, value=50, step=10) * 1e6  # Convert to tons

# 2️⃣ Modify Transmission Expansion Costs
transmission_cost = st.sidebar.number_input("Transmission Expansion Cost (€/MW-km)", min_value=0, value=500)

st.markdown("""
## Data Overview
This model uses:
- **Technology Costs (from PyPSA technology data, 2030)**
- **Electricity Demand (Germany 2015)**
- **Renewable Generation Time Series**
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
fig = px.line(ts, x=ts.index, y=["onwind", "offwind", "solar"], labels={"value": "Capacity Factor", "index": "Time"})
fig.update_layout(title="Capacity Factors Over Time", xaxis_title="Time", yaxis_title="Capacity Factor", height=400)
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

# Add Storage Units
n.add("StorageUnit", "battery storage", bus="electricity", carrier="battery storage",
      max_hours=6, capital_cost=costs.at["battery inverter", "capital_cost"] + 6 * costs.at["battery storage", "capital_cost"],
      efficiency_store=costs.at["battery inverter", "efficiency"], efficiency_dispatch=costs.at["battery inverter", "efficiency"],
      p_nom_extendable=True, cyclic_state_of_charge=True)

# Add Hydrogen Storage
capital_costs = (costs.at["electrolysis", "capital_cost"] + costs.at["fuel cell", "capital_cost"] + 168 * costs.at["hydrogen storage underground", "capital_cost"])
n.add("StorageUnit", "hydrogen storage underground", bus="electricity", carrier="hydrogen storage underground",
      max_hours=168, capital_cost=capital_costs,
      efficiency_store=costs.at["electrolysis", "efficiency"], efficiency_dispatch=costs.at["fuel cell", "efficiency"],
      p_nom_extendable=True, cyclic_state_of_charge=True)

# Optimize Model
st.sidebar.subheader("Run Optimization")
if st.sidebar.button("Optimize System"):
    n.add("GlobalConstraint", "CO2Limit", carrier_attribute="co2_emissions", sense="<=", constant=co2_limit)
    n.optimize(solver_name="highs")

    # Show Optimization Results
    st.header("Optimized Generator Capacities (MW)")
    st.write(n.generators.p_nom_opt)
    
    st.header("Optimized Storage Capacities (GWh)")
    st.write(n.storage_units.p_nom_opt * n.storage_units.max_hours / 1e3)

    # Show System Cost Breakdown
    def system_cost(n):
        tsc = pd.concat([n.statistics.capex(), n.statistics.opex()], axis=1)
        return tsc.sum(axis=1).droplevel(0).div(1e9).round(2)  # billion €/a

    st.subheader("System Cost Breakdown (in billion €/a)")
    cost_df = system_cost(n)
    fig, ax = plt.subplots()
    cost_df.plot.pie(ax=ax, autopct='%1.1f%%', startangle=90, legend=False)
    ax.set_ylabel("")
    st.pyplot(fig)
  
    # Save Results
    n.export_to_netcdf("network-new.nc")
    st.success("Optimization Completed! Results Saved.")
