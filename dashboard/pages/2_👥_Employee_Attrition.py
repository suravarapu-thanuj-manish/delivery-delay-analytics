import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

st.set_page_config(page_title="Employee Attrition Analytics", page_icon="👥", layout="wide")

# --- USER DATA UPLOADER ---
st.sidebar.title("📁 Upload Dataset")
uploaded_file = st.sidebar.file_uploader(
    "Upload HR Records (CSV / Excel)",
    type=["csv", "xlsx", "xls"],
    help="Upload your workforce / attrition dataset"
)

def generate_default_attrition() -> pd.DataFrame:
    np.random.seed(42)
    n = 1400
    departments = ["Sales", "R&D", "Human Resources", "Engineering", "Marketing"]
    roles = ["Junior Associate", "Senior Specialist", "Manager", "Team Lead"]
    salary_bands = ["Low ($30k-$50k)", "Medium ($50k-$90k)", "High ($90k+)"]

    tenure = np.random.exponential(scale=3.2, size=n).round(1).clip(0.3, 15)
    dept = np.random.choice(departments, n)
    band = np.random.choice(salary_bands, n, p=[0.45, 0.40, 0.15])
    
    prob = 0.10 + (band == "Low ($30k-$50k)") * 0.15 + (tenure < 1.5) * 0.22
    attrition = (np.random.rand(n) < prob).astype(int)

    return pd.DataFrame({
        "employee_id": [f"EMP-{1000 + i}" for i in range(n)],
        "department": dept,
        "role": np.random.choice(roles, n),
        "tenure_years": tenure,
        "salary_band": band,
        "attrition": attrition
    })

# Ingest data
if uploaded_file is not None:
    try:
        if uploaded_file.name.endswith(".csv"):
            try:
                raw_df = pd.read_csv(uploaded_file, encoding="utf-8")
            except UnicodeDecodeError:
                raw_df = pd.read_csv(uploaded_file, encoding="ISO-8859-1")
        else:
            raw_df = pd.read_excel(uploaded_file)
        st.sidebar.success(f"✓ Loaded {len(raw_df):,} records from {uploaded_file.name}")
    except Exception as e:
        st.sidebar.error(f"Error loading file: {e}")
        raw_df = generate_default_attrition()
else:
    st.sidebar.info("Awaiting user file. Using demo HR dataset.")
    raw_df = generate_default_attrition()

# --- AUTO-DETECT SCHEMA & CLEANING ---
df = raw_df.copy()
lookup = {c.strip().lower(): c for c in df.columns}

# Department
dept_col = next((lookup[k] for k in ["department", "dept", "business_unit", "team"] if k in lookup), None)
df["department"] = df[dept_col].astype(str) if dept_col else "General Operations"

# Role
role_col = next((lookup[k] for k in ["role", "jobrole", "job_role", "designation", "position"] if k in lookup), None)
df["role"] = df[role_col].astype(str) if role_col else "Staff"

# Tenure
tenure_col = next((lookup[k] for k in ["tenure_years", "tenure", "yearsatcompany", "experience_years"] if k in lookup), None)
if tenure_col:
    df["tenure_years"] = pd.to_numeric(df[tenure_col], errors="coerce").fillna(2.0)
else:
    df["tenure_years"] = np.random.exponential(scale=3.0, size=len(df)).round(1)

# Compensation
salary_col = next((lookup[k] for k in ["salary_band", "monthlyincome", "salary", "compensation_band"] if k in lookup), None)
if salary_col:
    if pd.api.types.is_numeric_dtype(df[salary_col]):
        df["salary_band"] = pd.qcut(df[salary_col], q=3, labels=["Low Tier", "Medium Tier", "High Tier"])
    else:
        df["salary_band"] = df[salary_col].astype(str)
else:
    df["salary_band"] = "Standard Compensation"

# Attrition Status (0 or 1)
att_col = next((lookup[k] for k in ["attrition", "left", "turnover", "exit_status", "status"] if k in lookup), None)
if att_col:
    df["attrition"] = df[att_col].astype(str).str.contains("Yes|1|True|Exit|Left", case=False).astype(int)
else:
    df["attrition"] = np.random.choice([0, 1], size=len(df), p=[0.82, 0.18])

# Derive Tenure Bands
df["tenure_band"] = pd.cut(
    df["tenure_years"],
    bins=[0, 1.5, 3.0, 5.0, 50.0],
    labels=["<1.5 Yrs", "1.5-3 Yrs", "3-5 Yrs", "5+ Yrs"]
)

# --- FILTERS ---
departments = sorted(df["department"].dropna().unique().tolist())
sel_dept = st.sidebar.multiselect("Filter Department", departments, default=departments)
f_df = df[df["department"].isin(sel_dept)]

# --- DASHBOARD UI ---
st.title("👥 Employee Attrition Analytics")
st.caption("Uncover retention bottlenecks, evaluate compensation impacts, and measure early-tenure exits.")

if f_df.empty:
    st.warning("No records found matching filters.")
    st.stop()

tot_headcount = len(f_df)
tot_exits = int(f_df["attrition"].sum())
att_rate = (tot_exits / tot_headcount * 100) if tot_headcount > 0 else 0.0

early_exits = f_df[(f_df["tenure_years"] < 1.5) & (f_df["attrition"] == 1)]
early_rate = (len(early_exits) / tot_exits * 100) if tot_exits > 0 else 0.0

k1, k2, k3, k4 = st.columns(4)
k1.metric("Total Workforce Tracked", f"{tot_headcount:,}")
k2.metric("Total Exits Recorded", f"{tot_exits:,}")
k3.metric("Overall Attrition Rate", f"{att_rate:.1f}%")
k4.metric("Early-Tenure Turnover (<1.5 yrs)", f"{early_rate:.1f}%")

st.markdown("---")

col1, col2 = st.columns(2)
with col1:
    st.subheader("Departmental Turnover Risk")
    dept_stats = f_df.groupby("department")["attrition"].agg(Total="count", Exits="sum").reset_index()
    dept_stats["Rate"] = (dept_stats["Exits"] / dept_stats["Total"] * 100).round(1)

    fig_dept = px.bar(
        dept_stats.sort_values(by="Rate", ascending=False),
        x="department",
        y="Rate",
        text=dept_stats["Rate"].apply(lambda v: f"{v:.1f}%"),
        color="Rate",
        color_continuous_scale="Reds",
        labels={"Rate": "Turnover Rate (%)", "department": "Department"}
    )
    st.plotly_chart(fig_dept, use_container_width=True)

with col2:
    st.subheader("Attrition Rate by Salary Band & Tenure")
    band_stats = f_df.groupby(["salary_band", "tenure_band"])["attrition"].mean().mul(100).round(1).reset_index(name="Rate")
    fig_band = px.bar(
        band_stats,
        x="salary_band",
        y="Rate",
        color="tenure_band",
        barmode="group",
        labels={"Rate": "Turnover Rate (%)", "salary_band": "Salary Band"}
    )
    st.plotly_chart(fig_band, use_container_width=True)