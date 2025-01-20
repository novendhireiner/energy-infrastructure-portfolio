import streamlit as st

st.set_page_config(layout="wide")

# Customize the sidebar
markdown = """
Energy Infrastructure Portfolio
"""

st.sidebar.title("About")
st.sidebar.info(markdown)
logo = "data/grid.png"
st.sidebar.image(logo)

st.title("🚀 Welcome to My Portfolio!")

st.write("""
## 👋 Hi, I'm **Novendhi Reiner Maturbongs**  
A **Data Analyst** with a background in **industrial engineering and energy systems**, I bring a unique blend of **engineering expertise, data analytics, and energy sector knowledge** to help drive sustainable power solutions.  
""")

st.write("""
### 🎓 Education & Background  
I hold an **M.Sc. in Business Administration and Engineering (Energy Systems)** from **Brandenburg Technical University Cottbus-Senftenberg** and have hands-on experience working in:  
- **Power plant operations and data analysis**  
- **Energy storage safety and risk assessments**  
- **Statistical evaluation of operational data**  

Over the years, I’ve transitioned into **data analytics**, leveraging **Python, R, SQL, and BI tools** like **Power BI, Tableau, and Looker Studio** to extract insights and optimize energy systems.  
""")

st.write("""
### 🔍 Current Focus  
I'm currently advancing my skills in **Agile Data Analytics**, with expertise in:  
✅ **Machine learning & data science** (Pandas, NumPy, Scikit-learn, PyTorch)  
✅ **Data visualization & BI tools** (Power BI, Tableau, Looker Studio)  
✅ **Project management & Agile methodologies** (Scrum, Six Sigma)  
""")

st.write("""
### 💡 What You’ll Find Here  
This portfolio showcases **real-world case studies, interactive visualizations, and analytical projects** demonstrating my expertise in:
🚗 **Electromobility & Charging Infrastructure Analysis**  
   - **Berlin's charging station network**: Explore the current EV charging infrastructure.  
   - **Optimal new locations**: Identify potential charging station sites near transportation hubs.  
   - **Interactive data filtering**: Analyze stations by district and charging capacity.  

📊 **Capacity expansion planning** with Renewable integration & power system optimization

st.write("### 📬 Let's Connect!")

st.markdown("""
📨 **Email**: [novendhi.reiner@gmail.com](mailto:novendhi.reiner@gmail.com)  
🔗 **GitHub**: [novendhireiner](https://github.com/novendhireiner)  
💼 **LinkedIn**: [LinkedIn Profile](https://www.linkedin.com/in/nrmaturbongs)
🎓 **Certifications**: [Scrum Master Certification](https://scrum.org/certificates/1089070)  
""")

st.write("Feel free to reach out to discuss data analytics, energy infrastructure, or potential collaborations! 🚀")
""")
