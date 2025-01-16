# 🇩🇪 Germany Energy Grid Optimization with PyPSA & Streamlit

📢 **Author:** _Your Name_  
📅 **Date:** _January 2025_  
🔧 **Technologies:** PyPSA, Python, Streamlit, Pandas, Matplotlib  

---

## 🌍 Project Overview  
This project models and optimizes **Germany’s electricity system** using **PyPSA** (Python for Power System Analysis). It allows users to:

✅ Adjust **CO₂ emission limits**  
✅ Modify **transmission expansion costs**  
✅ Optimize **renewable energy generation & grid capacity**  
✅ Analyze **energy dispatch & system costs**  
✅ Perform **sensitivity analysis on CO₂ policies**  

The optimization **minimizes total system costs** while satisfying electricity demand using renewables (solar, wind) and transmission expansion.

---

## 📺 Live Streamlit App  
🚀 Run the **interactive energy system model** in your browser!  
🌐 **[Coming Soon: Streamlit Cloud Deployment](#)**  

---

## ⚡ How the Model Works  
1. **Germany’s power demand & renewable profiles** are loaded from real-world data.  
2. The country is **divided into 3 regions**: **North, Central, South Germany**.  
3. **Renewable energy sources (solar & wind)** are distributed based on regional characteristics.  
4. **Power transmission lines** allow energy exchange between regions.  
5. **CO₂ emissions & costs** are optimized using **linear programming**.  
6. **Energy dispatch** is visualized to show how power is generated & consumed.  


---

## 🎛️ How to Use the Streamlit App  

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

---

## 🛠 Key Technologies & Tools  

| Technology  | Purpose |
|-------------|---------|
| **PyPSA**  | Power system modeling & optimization |
| **Pandas** | Time-series data processing |
| **Matplotlib** | Data visualization |
| **Streamlit** | Web dashboard for interactive analysis |

---

## 📊 Model Features  

### 🔹 1. Load Real-World Germany Energy Data  
✅ Uses **demand & renewable time-series** from [Germany 2015 dataset](https://tubcloud.tu-berlin.de/s/pKttFadrbTKSJKF/download).  
✅ **Resampled to 4-hour intervals** to reduce computation time.  

### 🔹 2. Divide Germany into 3 Energy Regions  

| Region  | % of Demand | Renewable Strength |
|---------|------------|--------------------|
| **North**  | 30%  | Strong **wind** |
| **Central** | 40%  | Balanced |
| **South**  | 30%  | Strong **solar** |

### 🔹 3. Optimize Generation & Grid Expansion  
✅ **Renewables:** Wind & solar can **scale** dynamically.  
✅ **Grid Transmission:** Optimized **transmission expansion** costs.  
✅ **CO₂ Constraints:** Users can **limit emissions** to meet climate targets.  

### 🔹 4. Visualize Energy Dispatch  
📊 **Stacked area plots** show how **each technology supplies demand** over time.  

### 🔹 5. Sensitivity Analysis  
📈 Users can **test different CO₂ limits** and analyze system costs.  

---

## 📷 Screenshots  

### 🔍 Interactive Dashboard  
![Streamlit Dashboard](images/streamlit_dashboard.png)  

### 📊 Optimized Generation & Grid Expansion  
![Optimized Grid](images/grid_expansion.png)  

---

## 📈 Example Results  

| CO₂ Limit (Mt) | System Cost (€ Billion) | Wind Capacity (GW) | Solar Capacity (GW) |
|---------------|-----------------|----------------|----------------|
| 200 Mt       | 50 B €           | 80 GW         | 60 GW         |
| 100 Mt       | 70 B €           | 120 GW        | 90 GW         |
| 50 Mt        | 90 B €           | 150 GW        | 120 GW        |

💡 **Observation:** Stricter CO₂ limits **increase system costs** but promote **more renewables**.

---

## 🎯 Contributions & Contact  

🤝 **Contributions Welcome!** Fork the repo and submit a PR.  

💬 **Questions? Contact Me:**  
📧 Email: **novendhi.reiner@gmail.com.com**  


---

## 📜 License  

📄 **MIT License** – Free to use & modify.  

---

## ⭐ Support the Project  
If you find this useful, give a ⭐ on **GitHub**! 🚀  
