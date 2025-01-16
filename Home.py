import streamlit as st

st.set_page_config(layout="wide")

# Customize the sidebar
markdown = """
Regional Grid Expansion Model in Germany
"""

st.sidebar.title("About")
st.sidebar.info(markdown)
logo = "https://github.com/novendhireiner/regional-grid-expansion-model/blob/main/data/powerplant.png"
st.sidebar.image(logo)

# Customize page title
st.title("🇩🇪 Germany Energy Grid Optimization with PyPSA & Streamlit")

st.markdown(
    """
    📢 **Author:** Novendhi Reiner Maturbongs 
    📅 **Date:** _January 2025_  
    🔧 **Technologies:** PyPSA, Python, Streamlit, Pandas, Matplotlib  
    """
)

st.header("🌍 Project Overview")
st.markdown(
    """
    This project models and optimizes **Germany’s electricity system** using **PyPSA** (Python for Power System Analysis). It allows users to:
    
    ✅ Adjust **CO₂ emission limits**  
    ✅ Modify **transmission expansion costs**  
    ✅ Optimize **renewable energy generation & grid capacity**  
    ✅ Analyze **energy dispatch & system costs**  
    ✅ Perform **sensitivity analysis on CO₂ policies**  
    
    The optimization **minimizes total system costs** while satisfying electricity demand using renewables (solar, wind) and transmission expansion.
    
    """
)

st.header("🎛️ How to Use the Streamlit App ")
st.markdown(
    """
    1. **Set Inputs in Sidebar**  
       - Adjust **CO₂ emission limit** (0-200 Mt).  
       - Modify **transmission expansion costs** (€ / MW/km).  
    2. **Optimize the Energy System**  
       - The model **solves for least-cost generation & transmission**.  
    3. **Analyze the Results**  
       - View **optimized renewable & grid capacities**.  
       - Explore **energy dispatch over time**.  
    4. **Run Sensitivity Analysis**  
       - See how **CO₂ limits affect system cost**.  
    """
)

st.header("📊 Model Features")
st.markdown(
    """
    1. Load Real-World Germany Energy Data  
        ✅ Uses **demand & renewable time-series** from [Germany 2015 dataset](https://tubcloud.tu-berlin.de/s/pKttFadrbTKSJKF/download).  
        ✅ **Resampled to 4-hour intervals** to reduce computation time.  

    2. Divide Germany into 3 Energy Regions  

        | Region  | % of Demand | Renewable Strength |
        |---------|------------|--------------------|
        | **North**  | 30%  | Strong **wind** |
        | **Central** | 40%  | Balanced |
        | **South**  | 30%  | Strong **solar** |

    3. Optimize Generation & Grid Expansion  
        ✅ **Renewables:** Wind & solar can **scale** dynamically.  
        ✅ **Grid Transmission:** Optimized **transmission expansion** costs.  
        ✅ **CO₂ Constraints:** Users can **limit emissions** to meet climate targets.  

    4. Visualize Energy Dispatch  
        📊 **Stacked area plots** show how **each technology supplies demand** over time.  

    5. Sensitivity Analysis  
        📈 Users can **test different CO₂ limits** and analyze system costs.  
    """
)
