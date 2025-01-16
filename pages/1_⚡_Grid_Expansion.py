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

# Load Time-Series Data
url = "https://tubcloud.tu-berlin.de/s/pKttFadrbTKSJKF/download/time-series-lecture-2.csv"
ts = pd.read_csv(url, index_col=0, parse_dates=True)
ts.load *= 1e3  # Convert load to MW
resolution = 4
ts = ts.resample(f"{resolution}h").first()

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

# Add Generators
for tech in ["onwind", "offwind", "solar"]:
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

capital_costs = (costs.at["electrolysis", "capital_cost"] + costs.at["fuel cell", "capital_cost"] + 168 * costs.at["hydrogen storage underground", "capital_cost"])
n.add("StorageUnit", "hydrogen storage underground", bus="electricity", carrier="hydrogen storage underground",
      max_hours=168, capital_cost=capital_costs,
      efficiency_store=costs.at["electrolysis", "efficiency"], efficiency_dispatch=costs.at["fuel cell", "efficiency"],
      p_nom_extendable=True, cyclic_state_of_charge=True)

# Add Emission Constraint
n.add("GlobalConstraint", "CO2Limit", carrier_attribute="co2_emissions", sense="<=", constant=0)

# Optimize Model
n.optimize(solver_name="highs")

# Display results in Streamlit
st.header("Optimized Generator Capacities")
st.write(n.generators.p_nom_opt)
st.header("Optimized Storage Capacities")
st.write(n.storage_units.p_nom_opt)

st.markdown("""
## Results Analysis
- **Optimal Generator Capacities**: This section presents the installed capacity of different generators.
- **Storage Capacities**: Displays how much storage is deployed.
- **Cost Analysis**: Pie chart below shows cost distribution.
""")

# Plot System Cost Breakdown
def system_cost(n):
    tsc = pd.concat([n.statistics.capex(), n.statistics.opex()], axis=1)
    return tsc.sum(axis=1).droplevel(0).div(1e9).round(2)  # billion €/a

fig, ax = plt.subplots()
system_cost(n).plot.pie(ax=ax, figsize=(4, 4))
st.pyplot(fig)
