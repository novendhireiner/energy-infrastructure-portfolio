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


costs.at["OCGT", "fuel"] = costs.at["gas", "fuel"]
costs.at["CCGT", "fuel"] = costs.at["gas", "fuel"]
costs.at["OCGT", "CO2 intensity"] = costs.at["gas", "CO2 intensity"]
costs.at["CCGT", "CO2 intensity"] = costs.at["gas", "CO2 intensity"]

def annuity(r, n):
    return r / (1.0 - 1.0 / (1.0 + r) ** n)

costs["marginal_cost"] = costs["VOM"] + costs["fuel"] / costs["efficiency"]
annuity_values = costs.apply(lambda x: annuity(x["discount rate"], x["lifetime"]), axis=1)
costs["capital_cost"] = (annuity_values + costs["FOM"] / 100) * costs["investment"]

# Load & Shows Time-Series Data
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
n.loads_t.p_set.plot(figsize=(6, 2), ylabel="MW")


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

# Add Emission Constraint
n.add("GlobalConstraint", "CO2Limit", carrier_attribute="co2_emissions", sense="<=", constant=0)

n.optimize(solver_name="highs")
n.generators.p_nom_opt  # MW
n.storage_units.p_nom_opt  # MW
n.storage_units.p_nom_opt.div(1e3) * n.storage_units.max_hours  # GWh

# Plot System Cost Breakdown
def system_cost(n):
    tsc = pd.concat([n.statistics.capex(), n.statistics.opex()], axis=1)
    return tsc.sum(axis=1).droplevel(0).div(1e9).round(2)  # billion €/a

system_cost(n).plot.pie(figsize=(4, 4))
plt.show()

# Export to NetCDF
n.export_to_netcdf("network-new.nc")
