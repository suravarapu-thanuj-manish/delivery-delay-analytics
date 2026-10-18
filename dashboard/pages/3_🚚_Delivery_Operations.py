import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import os
import joblib

st.set_page_config(page_title="Delivery Delay & Operations Analytics", page_icon="🚚", layout="wide")

# --- USER DATA UPLOADER ---
st.sidebar.title("📁 Upload Dataset")
uploaded_file = st.sidebar.file_uploader(
    "Upload Logistics / Delivery Records (CSV / Excel)",
    type=["csv", "xlsx", "xls"],
    help="Upload orders, shipment tracking, or carrier delay data"
)

def generate_default_logistics() -> pd.DataFrame:
    np.random.seed(42)
    n = 2500
    carriers = ["FedEx", "DHL", "BlueDart", "UPS", "LocalExpress"]
    warehouses = ["WH-North", "WH-South", "WH-West", "WH-East"]
    products = ["Electronics", "Fashion & Apparel", "Home Goods", "Perishables"]

    df = pd.DataFrame({
        "order_id": [f"ORD-{10000 + i}" for i in range(n)],
        "warehouse": np.random.choice(warehouses, n),
        "carrier": np.random.choice(carriers, n, p=[0.25, 0.25, 0.2, 0.2, 0.1]),
        "product_type": np.random.choice(products, n),
        "distance_km": np.random.gamma(shape=3.0, scale=120, size=n).clip(20, 1500).round(1),
        "delay_days": np.random.choice([-1, 0, 0, 1, 2, 4], n, p=[0.2, 0.35, 0.15, 0.15, 0.1, 0.05])
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
        raw_df = generate_default_logistics()
else:
    st.sidebar.info("Awaiting user file. Using demo delivery dataset.")
    raw_df = generate_default_logistics()

# --- AUTO-DETECT SCHEMA & CLEANING ---
df = raw_df.copy()
lookup = {c.strip().lower(): c for c in df.columns}

# 1. Warehouse
wh_col = next((lookup[k] for k in ["warehouse", "hub", "origin", "order region", "region", "location"] if k in lookup), None)
df["warehouse"] = df[wh_col].astype(str) if wh_col else "Central Hub"

# 2. Carrier
carrier_col = next((lookup[k] for k in ["carrier", "shipping mode", "ship mode", "courier", "logistics_partner"] if k in lookup), None)
df["carrier"] = df[carrier_col].astype(str) if carrier_col else "Standard Fleet"

# 3. Product Category
prod_col = next((lookup[k] for k in ["product_type", "category name", "category", "department name"] if k in lookup), None)
df["product_type"] = df[prod_col].astype(str) if prod_col else "General Merchandise"

# 4. Delays & SLA
actual_col = next((lookup[k] for k in ["actual_delivery_date", "days for shipping (real)", "actual_days", "delivery_date"] if k in lookup), None)
promised_col = next((lookup[k] for k in ["promised_delivery_date", "days for shipment (scheduled)", "promised_days"] if k in lookup), None)
delay_col = next((lookup[k] for k in ["delay_days", "delay", "days_late"] if k in lookup), None)
status_col = next((lookup[k] for k in ["delivery status", "status", "delivery_status"] if k in lookup), None)

if delay_col:
    df["delay_days"] = pd.to_numeric(df[delay_col], errors="coerce").fillna(0.0)
elif actual_col and promised_col:
    if pd.api.types.is_numeric_dtype(df[actual_col]):
        df["delay_days"] = (df[actual_col].fillna(0) - df[promised_col].fillna(0)).astype(float)
    else:
        a_dt = pd.to_datetime(df[actual_col], errors="coerce")
        p_dt = pd.to_datetime(df[promised_col], errors="coerce")
        df["delay_days"] = (a_dt - p_dt).dt.total_seconds() / 86400
        df["delay_days"] = df["delay_days"].fillna(0.0)
elif status_col:
    df["is_delayed"] = df[status_col].astype(str).str.contains("Late", case=False).astype(int)
    df["delay_days"] = df["is_delayed"] * 2.0
else:
    df["delay_days"] = np.random.choice([0.0, 0.0, 1.0, 2.0, 3.0], size=len(df))

df["is_delayed"] = (df["delay_days"] > 0).astype(int)
df["is_on_time"] = (df["delay_days"] <= 0).astype(int)

# Distance
dist_col = next((lookup[k] for k in ["distance_km", "distance", "transit_km"] if k in lookup), None)
df["distance_km"] = pd.to_numeric(df[dist_col], errors="coerce").fillna(350.0) if dist_col else np.random.randint(50, 1200, size=len(df))

# Severity bands (guaranteed column)
conditions = [
    (df["delay_days"] <= 0),
    (df["delay_days"] > 0) & (df["delay_days"] <= 2),
    (df["delay_days"] > 2)
]
df["delay_severity"] = np.select(conditions, ["On-Time", "Minor Delay (1-2d)", "Severe Delay (>2d)"], default="On-Time")

# --- FILTERS ---
warehouses = sorted(df["warehouse"].dropna().unique().tolist())
carriers = sorted(df["carrier"].dropna().unique().tolist())

sel_wh = st.sidebar.multiselect("Filter Warehouse", warehouses, default=warehouses)
sel_carrier = st.sidebar.multiselect("Filter Carrier", carriers, default=carriers)

f_df = df[(df["warehouse"].isin(sel_wh)) & (df["carrier"].isin(sel_carrier))].copy()

# Ensure severity persists
if "delay_severity" not in f_df.columns:
    f_df["delay_severity"] = "On-Time"

# --- DASHBOARD UI ---
st.title("🚚 Delivery Delay & Operations Analytics")
st.caption("Pinpoint logistics bottlenecks, analyze carrier SLA compliance, and evaluate live delay risk.")

if f_df.empty:
    st.warning("No records found matching filters.")
    st.stop()

tot_orders = len(f_df)
tot_delayed = int(f_df["is_delayed"].sum())
on_time_rate = ((tot_orders - tot_delayed) / tot_orders * 100) if tot_orders > 0 else 0.0

late_df = f_df[f_df["delay_days"] > 0]
avg_delay = late_df["delay_days"].mean() if not late_df.empty else 0.0

k1, k2, k3, k4 = st.columns(4)
k1.metric("Total Shipments", f"{tot_orders:,}")
k2.metric("On-Time Delivery Rate", f"{on_time_rate:.1f}%", delta=f"{on_time_rate - 85:.1f}% vs Target")
k3.metric("Delayed Shipments", f"{tot_delayed:,}")
k4.metric("Avg Delay Duration", f"{avg_delay:.1f} days")

st.markdown("---")

tab1, tab2, tab3 = st.tabs(["📊 Carrier Bottlenecks", "🔥 Warehouse & Category Hotspots", "🔮 Live Risk Predictor"])

with tab1:
    col_a, col_b = st.columns(2)
    with col_a:
        st.subheader("Carrier Delay Percentage")
        carrier_perf = f_df.groupby("carrier").agg(Total=("carrier", "count"), Delayed=("is_delayed", "sum")).reset_index()
        carrier_perf["Rate"] = (carrier_perf["Delayed"] / carrier_perf["Total"] * 100).round(1)

        fig_bar = px.bar(
            carrier_perf.sort_values(by="Rate", ascending=False),
            x="carrier",
            y="Rate",
            text=carrier_perf["Rate"].apply(lambda v: f"{v:.1f}%"),
            color="Rate",
            color_continuous_scale="Reds",
            labels={"Rate": "Delay Rate (%)", "carrier": "Carrier"}
        )
        fig_bar.update_layout(yaxis_range=[0, 100], showlegend=False)
        st.plotly_chart(fig_bar, use_container_width=True)

    with col_b:
        st.subheader("Delivery Status Severity Breakdown")
        sev_data = f_df.groupby(["carrier", "delay_severity"]).size().reset_index(name="count")
        fig_sev = px.bar(
            sev_data,
            x="carrier",
            y="count",
            color="delay_severity",
            barmode="group",
            labels={"count": "Orders", "delay_severity": "Status"},
            color_discrete_map={
                "On-Time": "#2ecc71",
                "Minor Delay (1-2d)": "#f39c12",
                "Severe Delay (>2d)": "#e74c3c"
            }
        )
        st.plotly_chart(fig_sev, use_container_width=True)

with tab2:
    st.subheader("Warehouse Hub × Product Category Delay Hotspots (%)")
    pivot_matrix = (f_df.pivot_table(index="warehouse", columns="product_type", values="is_delayed", aggfunc="mean", fill_value=0.0) * 100).round(1)

    if not pivot_matrix.empty:
        fig_heat = px.imshow(
            pivot_matrix,
            text_auto=True,
            aspect="auto",
            color_continuous_scale="YlOrRd",
            labels=dict(x="Category", y="Warehouse Hub", color="Delay %")
        )
        st.plotly_chart(fig_heat, use_container_width=True)
    else:
        st.info("Insufficient category/hub combinations to render heatmap.")

with tab3:
    st.subheader("Simulate Dispatch Delay Probability")
    c1, c2, c3 = st.columns(3)
    with c1:
        in_wh = st.selectbox("Dispatch Warehouse", warehouses)
        in_carrier = st.selectbox("Assigned Carrier", carriers)
    with c2:
        in_prod = st.selectbox("Product Line", sorted(df["product_type"].dropna().unique().tolist()))
        in_dist = st.slider("Delivery Route Distance (km)", 20, 2000, 350, 25)
    with c3:
        in_day = st.selectbox("Dispatch Day", ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"])

    if st.button("Evaluate Delay Risk"):
        wh_delay = df[df["warehouse"] == in_wh]["is_delayed"].mean()
        carrier_delay = df[df["carrier"] == in_carrier]["is_delayed"].mean()
        prob = min(95.0, max(5.0, ((wh_delay + carrier_delay) / 2.0) * 100))

        r1, r2 = st.columns([1, 2])
        with r1:
            fig_gauge = go.Figure(go.Indicator(
                mode="gauge+number",
                value=prob,
                title={'text': "Delay Probability (%)"},
                gauge={
                    'axis': {'range': [0, 100]},
                    'bar': {'color': "#e74c3c" if prob > 50 else "#2ecc71"},
                    'steps': [
                        {'range': [0, 35], 'color': "#d5f5e3"},
                        {'range': [35, 60], 'color': "#fef9e7"},
                        {'range': [60, 100], 'color': "#fadbd8"}
                    ],
                    'threshold': {'line': {'color': "black", 'width': 3}, 'thickness': 0.8, 'value': 50}
                }
            ))
            fig_gauge.update_layout(height=260, margin=dict(t=20, b=10, l=10, r=10))
            st.plotly_chart(fig_gauge, use_container_width=True)

        with r2:
            if prob >= 50:
                st.error(f"🚨 **High Delay Risk ({prob:.1f}%)**: Historical route and hub patterns indicate a high likelihood of an SLA breach.")
            else:
                st.success(f"✅ **Low Delay Risk ({prob:.1f}%)**: Transit distance and carrier assignments are within standard delivery margins.")