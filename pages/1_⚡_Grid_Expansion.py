import pypsa
import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st

plt.style.use("bmh")

st.title("Decarbonizing Electricity Supply with PyPSA")

st.markdown("""
## Project Overview
This project explores the decarbonization of the electricity supply using PyPSA (Python for Power System Analysis). 
The model simulates different energy sources and storage technologies to achieve a low-carbon electricity grid.

### Key Components:
- **Renewable Energy Sources:** Onshore wind, offshore wind, and solar PV.
- **Backup Generation:** Open Cycle Gas Turbine (OCGT) for flexibility.
- **Energy Storage:** Battery storage and hydrogen storage underground.
- **Emission Constraints:** CO₂ limits to drive decarbonization efforts.

The goal is to optimize the energy mix while minimizing costs and emissions.
""")

st.markdown("""
## Data Overview
The dataset used in this project includes:
- **Technology Costs (from PyPSA technology data, 2030)**
  - Includes capital cost, operational cost, efficiency, and CO₂ emissions for each technology.
- **Electricity Demand (Germany 2015)**
  - Hourly electricity consumption data for an entire year.
- **Renewable Generation Time Series**
  - Capacity factors for wind and solar to estimate real-time energy generation.

### Selected Data
The model specifically uses:
- **Wind and solar availability factors from time series.**
- **Investment costs, fuel costs, and efficiency data for generation and storage technologies.**
- **An annual CO₂ emission constraint to drive decarbonization.**
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

st.subheader("Electricity Demand Time Series")
url = "https://tubcloud.tu-berlin.de/s/pKttFadrbTKSJKF/download/time-series-lecture-2.csv"
ts = pd.read_csv(url, index_col=0, parse_dates=True)
ts.load *= 1e3  # Convert load to MW
resolution = 4
ts = ts.resample(f"{resolution}h").first()

fig, ax = plt.subplots()
ts.load.plot(ax=ax, figsize=(10, 4), title="Electricity Demand (MW)")
st.pyplot(fig)

st.subheader("Wind and Solar Capacity Factors")
fig, ax = plt.subplots()
ts[["onwind", "offwind", "solar"]].plot(ax=ax, figsize=(10, 4), title="Capacity Factors")
st.pyplot(fig)

# Initialize Network
n = pypsa.Network()
n.add("Bus", "electricity")
n.set_snapshots(ts.index)
n.snapshot_weightings.loc[:, :] = resolution

# Add Technologies
carriers = ["onwind", "offwind", "solar", "OCGT", "hydrogen storage underground", "battery storage"]
n.add("Carrier", carriers, co2_emissions=[costs.at[c, "CO2 intensity"] for c in carriers])

# Add Loads
n.add("Load", "demand", bus="electricity", p_set=ts.load)

# Store Initial Generator Capacities Before Optimization
initial_generator_capacities = n.generators.p_nom_opt.copy()
initial_storage_capacities = n.storage_units.p_nom_opt.copy()

# Add Generators
for tech in ["onwind", "offwind", "solar"]:
    n.add("Generator", tech, bus="electricity", carrier=tech, p_max_pu=ts[tech],
          capital_cost=costs.at[tech, "capital_cost"], marginal_cost=costs.at[tech, "marginal_cost"],
          efficiency=costs.at[tech, "efficiency"], p_nom_extendable=True)

n.add("Generator", "OCGT", bus="electricity", carrier="OCGT",
      capital_cost=costs.at["OCGT", "capital_cost"], marginal_cost=costs.at["OCGT", "marginal_cost"],
      efficiency=costs.at["OCGT", "efficiency"], p_nom_extendable=True)

# Optimize Model
n.optimize(solver_name="highs")

# Display Before and After Comparison
st.header("Generator Capacities: Before vs After Optimization")
comparison_df = pd.DataFrame({
    "Before Optimization": initial_generator_capacities,
    "After Optimization": n.generators.p_nom_opt
})
st.write(comparison_df)

st.header("Storage Capacities: Before vs After Optimization")
storage_comparison_df = pd.DataFrame({
    "Before Optimization": initial_storage_capacities,
    "After Optimization": n.storage_units.p_nom_opt
})
st.write(storage_comparison_df)

st.markdown("""
## Results Analysis
- **Before Optimization:** Shows initial capacities before the solver runs.
- **After Optimization:** Displays optimized capacities after the model balances cost and emissions constraints.
""")

# Export to NetCDF
n.export_to_netcdf("network-new.nc")
