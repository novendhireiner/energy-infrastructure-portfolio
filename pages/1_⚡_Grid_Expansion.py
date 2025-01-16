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

# Ensure CO2 intensity column exists
if "CO2 intensity" not in costs.columns:
    costs["CO2 intensity"] = 0  # Default to zero emissions if missing

# Ensure necessary technologies exist in costs DataFrame
def tech_exists(tech_name, default_capital_cost=1000000):
    if tech_name not in costs.index:
        costs.loc[tech_name, "capital_cost"] = default_capital_cost
        costs.loc[tech_name, "efficiency"] = 1
        print(f"Warning: {tech_name} missing from dataset. Using default values.")

# Ensure necessary technologies are present
tech_exists("onwind", 1200000)
tech_exists("offwind", 1500000)
tech_exists("solar", 900000)
tech_exists("OCGT", 800000)
tech_exists("hydrogen storage underground", 700000)
tech_exists("battery storage", 500000)

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

n.set_snapshots(ts.index)
n.snapshot_weightings.loc[:, :] = resolution

# Add Generators and Technologies
def add_components(n):
    carriers = ["onwind", "offwind", "solar", "OCGT", "hydrogen storage underground", "battery storage"]
    
    # Debugging information
    print("Available carriers in costs dataset:", costs.index.tolist())
    print("Available columns in costs dataset:", costs.columns.tolist())
    
    n.add("Carrier", carriers, co2_emissions=[
        costs.loc[c, "CO2 intensity"] if c in costs.index else 0 for c in carriers
    ])
    
    n.add("Load", "electricity_demand", bus="electricity", p_set=ts.load)
    for tech in ["onwind", "offwind", "solar"]:
        n.add("Generator", tech, bus="electricity", carrier=tech, p_max_pu=ts[tech],
              capital_cost=costs.at[tech, "capital_cost"], marginal_cost=costs.at[tech, "marginal_cost"],
              efficiency=costs.at[tech, "efficiency"], p_nom_extendable=True)
    n.add("Generator", "OCGT", bus="electricity", carrier="OCGT",
          capital_cost=costs.at["OCGT", "capital_cost"], marginal_cost=costs.at["OCGT", "marginal_cost"],
          efficiency=costs.at["OCGT", "efficiency"], p_nom_extendable=True)
    n.add("StorageUnit", "battery storage", bus="electricity", carrier="battery storage",
          max_hours=6, capital_cost=costs.loc["battery storage", "capital_cost"],
          efficiency_store=0.9, efficiency_dispatch=0.9, p_nom_extendable=True, cyclic_state_of_charge=True)
    n.add("StorageUnit", "hydrogen storage underground", bus="hydrogen", carrier="hydrogen storage underground",
          max_hours=168, capital_cost=costs.loc["hydrogen storage underground", "capital_cost"],
          efficiency_store=0.8, efficiency_dispatch=0.8, p_nom_extendable=True, cyclic_state_of_charge=True)

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
