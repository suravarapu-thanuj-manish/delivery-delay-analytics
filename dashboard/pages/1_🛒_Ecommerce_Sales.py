import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

st.set_page_config(page_title="E-commerce Sales & Customer Insights", page_icon="🛒", layout="wide")

# --- USER DATA UPLOADER ---
st.sidebar.title("📁 Upload Dataset")
uploaded_file = st.sidebar.file_uploader(
    "Upload E-commerce Sales (CSV / Excel)",
    type=["csv", "xlsx", "xls"],
    help="Upload your transactions, sales, or order data"
)

def generate_default_sales() -> pd.DataFrame:
    np.random.seed(42)
    n = 2500
    dates = pd.date_range("2025-01-01", periods=180, freq="D")
    categories = ["Electronics", "Fashion", "Home & Garden", "Books", "Beauty"]
    regions = ["North", "South", "East", "West"]

    df = pd.DataFrame({
        "order_id": [f"ORD-{1000 + i}" for i in range(n)],
        "customer_id": np.random.choice([f"CUST-{j}" for j in range(500)], n),
        "order_date": np.random.choice(dates, n),
        "category": np.random.choice(categories, n, p=[0.3, 0.25, 0.2, 0.15, 0.1]),
        "region": np.random.choice(regions, n),
        "order_value": np.random.gamma(shape=2.5, scale=45, size=n).round(2),
        "profit_margin": np.random.uniform(0.1, 0.35, size=n).round(2)
    })
    return df

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
        raw_df = generate_default_sales()
else:
    st.sidebar.info("Awaiting user file. Using demo sales dataset.")
    raw_df = generate_default_sales()

# --- AUTO-DETECT SCHEMA & CLEANING ---
df = raw_df.copy()
lookup = {c.strip().lower(): c for c in df.columns}

# 1. Order ID & Customer ID
order_col = next((lookup[k] for k in ["order_id", "order id", "invoice", "transaction_id"] if k in lookup), None)
df["order_id"] = df[order_col].astype(str) if order_col else [f"ORD-{i}" for i in range(len(df))]

cust_col = next((lookup[k] for k in ["customer_id", "customer id", "customer", "client_id"] if k in lookup), None)
df["customer_id"] = df[cust_col].astype(str) if cust_col else [f"CUST-{i%400}" for i in range(len(df))]

# 2. Revenue / Order Value
val_col = next((lookup[k] for k in ["order_value", "sales", "revenue", "amount", "total_price"] if k in lookup), None)
if val_col:
    df["order_value"] = pd.to_numeric(df[val_col], errors="coerce").fillna(50.0)
else:
    df["order_value"] = np.random.gamma(shape=2.5, scale=40, size=len(df)).round(2)

# 3. Category & Region
cat_col = next((lookup[k] for k in ["category", "product_category", "category name", "department"] if k in lookup), None)
df["category"] = df[cat_col].astype(str) if cat_col else "General Merchandise"

reg_col = next((lookup[k] for k in ["region", "country", "state", "city", "location"] if k in lookup), None)
df["region"] = df[reg_col].astype(str) if reg_col else "National"

# 4. Dates
date_col = next((lookup[k] for k in ["order_date", "date", "order date", "timestamp"] if k in lookup), None)
if date_col:
    df["order_date"] = pd.to_datetime(df[date_col], errors="coerce")
    df = df.dropna(subset=["order_date"])
else:
    df["order_date"] = pd.date_range("2025-01-01", periods=len(df), freq="H")

# --- FILTERS ---
categories = sorted(df["category"].dropna().unique().tolist())
regions = sorted(df["region"].dropna().unique().tolist())

sel_cat = st.sidebar.multiselect("Filter Category", categories, default=categories)
sel_reg = st.sidebar.multiselect("Filter Region", regions, default=regions)

f_df = df[(df["category"].isin(sel_cat)) & (df["region"].isin(sel_reg))]

# --- DASHBOARD UI ---
st.title("🛒 E-commerce Sales & Customer Insights Dashboard")
st.caption("Analyze revenue trends, regional performance, and repeat customer retention patterns.")

if f_df.empty:
    st.warning("No data matches the selected filters.")
    st.stop()

# KPIs
tot_rev = f_df["order_value"].sum()
tot_orders = len(f_df)
aov = tot_rev / tot_orders if tot_orders > 0 else 0.0

# Customer Repeat Rate
cust_counts = f_df.groupby("customer_id")["order_id"].nunique()
repeat_cust_rate = ((cust_counts > 1).sum() / len(cust_counts) * 100) if len(cust_counts) > 0 else 0.0

k1, k2, k3, k4 = st.columns(4)
k1.metric("Gross Revenue", f"${tot_rev:,.2f}")
k2.metric("Orders Completed", f"{tot_orders:,}")
k3.metric("Average Order Value (AOV)", f"${aov:.2f}")
k4.metric("Repeat Customer Rate", f"{repeat_cust_rate:.1f}%")

st.markdown("---")

c1, c2 = st.columns(2)
with c1:
    st.subheader("Monthly Revenue Trajectory")
    monthly_rev = f_df.set_index("order_date").resample("ME")["order_value"].sum().reset_index()
    fig_line = px.line(
        monthly_rev,
        x="order_date",
        y="order_value",
        markers=True,
        labels={"order_date": "Month", "order_value": "Sales ($)"}
    )
    st.plotly_chart(fig_line, use_container_width=True)

with c2:
    st.subheader("Sales by Category & Geography")
    fig_cat = px.bar(
        f_df,
        x="category",
        y="order_value",
        color="region",
        barmode="stack",
        labels={"category": "Product Category", "order_value": "Revenue ($)", "region": "Region"}
    )
    st.plotly_chart(fig_cat, use_container_width=True)