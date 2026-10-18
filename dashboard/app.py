import streamlit as st

st.set_page_config(
    page_title="Data Science Portfolio Hub",
    page_icon="🧭",
    layout="wide",
)

st.title("💼 Enterprise Analytics & Data Science Hub")
st.subheader("A Unified Suite of Practical Data Science Solutions")
st.write(
    "Welcome to the multi-project intelligence portal. Select any module from the sidebar or the action cards below to launch the dedicated analytics dashboard:"
)

st.markdown("---")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("### 🛒 Project 1")
    st.markdown("**E-commerce Sales & Customer Insights**")
    st.caption(
        "Analyze revenue drivers, customer cohort retention, order values, and category performance."
    )
    st.markdown(
        """
    - **KPIs**: Revenue, AOV, Margin, Repeat Rate
    - **Methods**: Customer Segmentation, Cohort Analysis
    - **Tech**: Pandas, Plotly Express
    """
    )

with col2:
    st.markdown("### 👥 Project 2")
    st.markdown("**Employee Attrition Analytics**")
    st.caption(
        "Evaluate workforce turnover patterns across departments, tenure bands, and compensation tiers."
    )
    st.markdown(
        """
    - **KPIs**: Early-Tenure Attrition, Departmental Turnover
    - **Methods**: Statistical Inference, Logistic Regression
    - **Tech**: Scikit-Learn, Pandas
    """
    )

with col3:
    st.markdown("### 🚚 Project 3")
    st.markdown("**Delivery Delay & Operations Analytics**")
    st.caption(
        "Quantify shipping bottlenecks, analyze carrier SLA compliance, and evaluate real-time delay risks."
    )
    st.markdown(
        """
    - **KPIs**: On-Time Delivery (OTD %), Avg Delay Days
    - **Methods**: Decision Tree Classifier, Heatmap Hotspots
    - **Tech**: Scikit-Learn, Plotly, Streamlit
    """
    )

st.markdown("---")
st.info(
    "👈 Use the left sidebar to navigate directly into each full interactive project."
)