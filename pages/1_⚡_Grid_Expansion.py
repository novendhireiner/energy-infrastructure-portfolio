import streamlit as st
import pypsa
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(page_title="Germany Energy Grid", layout="wide")

markdown = """
Regional Grid Expansion Model in Germany
"""

st.sidebar.title("About")
st.sidebar.info(markdown)
logo = "data/grid.png"
st.sidebar.image(logo)

# Load Germany time-series data
@st.cache_data
def load_data():
    url = "https://tubcloud.tu-berlin.de/s/pKttFadrbTKSJKF/download/time-series-lecture-2.csv"
    ts = pd.read_csv(url, index_col=0, parse_dates=True)
    ts["load"] *= 1e3  # Convert load from GW to MW
    return ts.resample("4h").mean()

ts = load_data()

# Create PyPSA Network
def create_network(co2_limit, transmission_cost):
    n = pypsa.Network()
    n.set_snapshots(ts.index)

    regions = ["North", "Central", "South"]
    region_shares = {"North": 0.3, "Central": 0.4, "South": 0.3}
    regional_loads = {region: ts["load"] * share for region, share in region_shares.items()}

    for region in regions:
        n.add("Bus", region)
        n.add("Load", f"{region}_load", bus=region, p_set=regional_loads[region])

    regional_profiles = {
        "North": {"onwind": ts["onwind"] * 1.2, "solar": ts["solar"] * 0.8},
        "Central": {"onwind": ts["onwind"] * 0.9, "solar": ts["solar"] * 1.0},
        "South": {"onwind": ts["onwind"] * 0.7, "solar": ts["solar"] * 1.2},
    }

    for region, profiles in regional_profiles.items():
        for tech, profile in profiles.items():
            capital_cost = 500 if tech == "onwind" else 800
            n.add("Generator", f"{region}_{tech}", bus=region, p_nom_extendable=True,
                  capital_cost=capital_cost, marginal_cost=0, efficiency=1.0, p_max_pu=profile)

    distances = {("North", "Central"): 300, ("Central", "South"): 250, ("North", "South"): 500}
    for (region1, region2), distance in distances.items():
        n.add("Link", f"Line_{region1}_{region2}", bus0=region1, bus1=region2,
              p_nom_extendable=True, capital_cost=transmission_cost * distance, marginal_cost=0)

    n.add("GlobalConstraint", "CO2Limit", carrier_attribute="co2_emissions",
          sense="<=", constant=co2_limit * 1e6)

    n.optimize(solver_name="highs")
    return n

# Streamlit Sidebar Inputs
st.sidebar.header("Model Inputs")
co2_limit = st.sidebar.slider("CO₂ Limit (Mt)", min_value=0, max_value=200, value=100, step=10)
transmission_cost = st.sidebar.slider("Transmission Cost (€/MW/km)", min_value=100, max_value=1000, value=400, step=50)

# Solve the model
st.sidebar.text("Running Optimization...")
network = create_network(co2_limit, transmission_cost)
st.sidebar.text("✅ Optimization Complete!")

# Results: Generation & Transmission
st.header("Optimized Energy System Results")

col1, col2 = st.columns(2)

with col1:
    st.subheader("Optimized Generation Capacities (MW)")
    gen_capacities = network.generators.p_nom_opt
    st.dataframe(gen_capacities)

with col2:
    st.subheader("Optimized Transmission Capacities (MW)")
    transmission_capacities = network.links.p_nom_opt
    st.dataframe(transmission_capacities)

# Energy Dispatch Plot
def plot_dispatch(n, time="2015-07"):
    p = (n.statistics.energy_balance(aggregate_time=False)
         .groupby("carrier").sum().div(1e3).drop("-", errors="ignore").T)

    fig, ax = plt.subplots(figsize=(8, 4))

    default_color = "gray"
    color_mapping = n.carriers["color"].to_dict() if "color" in n.carriers else {}

    colors = [color_mapping.get(carrier, default_color) for carrier in p.columns]

    p.where(p > 0).loc[time].plot.area(ax=ax, linewidth=0, color=colors)

    charge = p.where(p < 0).dropna(how="all", axis=1).loc[time]
    if not charge.empty:
        charge.plot.area(ax=ax, linewidth=0, color=colors)

    plt.ylabel("GW")
    plt.title(f"Energy Dispatch for {time}")
    plt.legend(loc="center left", bbox_to_anchor=(1.0, 0.5))
    return fig

st.subheader("Energy Dispatch Visualization")
dispatch_time = st.selectbox("Select Time Period", ts.index.strftime('%Y-%m').unique())
st.pyplot(plot_dispatch(network, time=dispatch_time))

# Sensitivity Analysis: CO2 vs Cost
def sensitivity_analysis():
    results = {}
    for co2 in [0, 50, 100, 150, 200]:
        n = create_network(co2, transmission_cost)
        cost = sum(n.statistics.capex()) + sum(n.statistics.opex())
        results[co2] = cost / 1e9  # Convert to billion euros

    df = pd.DataFrame(results, index=["System Cost"]).T
    return df

st.subheader("Sensitivity Analysis: CO₂ Limit vs System Cost")
if st.button("Run Sensitivity Analysis"):
    sensitivity_results = sensitivity_analysis()
    st.line_chart(sensitivity_results)
