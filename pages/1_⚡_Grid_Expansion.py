import pypsa
import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st

plt.style.use("bmh")

st.title("Decarbonizing Electricity Supply with Sector Coupling")

# Load Cost Data
year = 2030
url = f"https://raw.githubusercontent.com/PyPSA/technology-data/master/outputs/costs_{year}.csv"
costs = pd.read_csv(url, index_col=[0, 1])

# Convert kW-based costs to MW
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

# Define annuity function
def annuity(r, n):
    return r / (1.0 - 1.0 / (1.0 + r) ** n)

costs["marginal_cost"] = costs["VOM"] + costs["fuel"] / costs["efficiency"]
costs["capital_cost"] = costs.apply(lambda x: annuity(x["discount rate"], x["lifetime"]), axis=1) * costs["investment"]

# Load Time-Series Data
url = "https://tubcloud.tu-berlin.de/s/pKttFadrbTKSJKF/download/time-series-lecture-2.csv"
ts = pd.read_csv(url, index_col=0, parse_dates=True)
ts.load *= 1e3  # Convert load to MW
resolution = 4
ts = ts.resample(f"{resolution}h").first()

# Initialize Network
n = pypsa.Network()
n.add("Bus", "electricity")
n.add("Bus", "hydrogen")
n.add("Bus", "heat")

n.set_snapshots(ts.index)
n.snapshot_weightings.loc[:, :] = resolution

# Add Generators and Technologies
def add_components(n):
    carriers = ["onwind", "offwind", "solar", "OCGT", "hydrogen storage", "battery storage", "heat pump"]
    n.add("Carrier", carriers, co2_emissions=[costs.at[c, "CO2 intensity"] for c in carriers])
    n.add("Load", "electricity_demand", bus="electricity", p_set=ts.load)
    n.add("Load", "heat_demand", bus="heat", p_set=ts.load * 0.5)
    for tech in ["onwind", "offwind", "solar"]:
        n.add("Generator", tech, bus="electricity", carrier=tech, p_max_pu=ts[tech],
              capital_cost=costs.at[tech, "capital_cost"], marginal_cost=costs.at[tech, "marginal_cost"],
              efficiency=costs.at[tech, "efficiency"], p_nom_extendable=True)
    n.add("Generator", "OCGT", bus="electricity", carrier="OCGT",
          capital_cost=costs.at["OCGT", "capital_cost"], marginal_cost=costs.at["OCGT", "marginal_cost"],
          efficiency=costs.at["OCGT", "efficiency"], p_nom_extendable=True)
    n.add("Link", "heat_pump", bus0="electricity", bus1="heat", carrier="heat pump",
          efficiency=3, capital_cost=costs.at["heat pump", "capital_cost"], p_nom_extendable=True)
    n.add("Link", "electrolyzer", bus0="electricity", bus1="hydrogen", carrier="electrolyzer",
          efficiency=costs.at["electrolysis", "efficiency"], capital_cost=costs.at["electrolysis", "capital_cost"], p_nom_extendable=True)
    n.add("StorageUnit", "battery", bus="electricity", carrier="battery storage",
          max_hours=6, capital_cost=costs.at["battery inverter", "capital_cost"] + 6 * costs.at["battery storage", "capital_cost"],
          efficiency_store=costs.at["battery inverter", "efficiency"], efficiency_dispatch=costs.at["battery inverter", "efficiency"],
          p_nom_extendable=True, cyclic_state_of_charge=True)

add_components(n)
n.optimize(solver_name="highs")

# Display results
st.header("Optimized Generator Capacities")
st.write(n.generators.p_nom_opt)
st.header("Optimized Storage Capacities")
st.write(n.storage_units.p_nom_opt)

# Plot System Cost Breakdown
def system_cost(n):
    return (n.statistics.capex() + n.statistics.opex()).sum(axis=1).droplevel(0).div(1e9)

fig, ax = plt.subplots()
system_cost(n).plot.pie(ax=ax, figsize=(4, 4))
st.pyplot(fig)
