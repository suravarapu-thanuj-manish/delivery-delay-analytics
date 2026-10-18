# 💼 Enterprise Data Science & Analytics Suite

A comprehensive data intelligence portal housing three practical, medium-level data science solutions built with Python, Scikit-learn, and Streamlit[cite: 1, 2].

---

## 📌 Projects Included

### 1. 🛒 E-commerce Sales & Customer Insights Dashboard

- **Objective**: Analyze sales transactions, customer retention, product lines, and regional drivers.
- **Core KPIs**: Total Gross Revenue, Orders Completed, Average Order Value (AOV), Repeat Customer Rate[cite: 1].
- **Features**: Dynamic CSV/Excel ingestion, monthly revenue trends, category-geography revenue breakdowns[cite: 1].

### 2. 👥 Employee Attrition Analytics

- **Objective**: Evaluate workforce records to understand retention vulnerabilities and departmental patterns[cite: 1].
- **Core KPIs**: Total Headcount, Turnover Rate (%), Early-Tenure Attrition (<1.5 years)[cite: 1].
- **Features**: Dynamic CSV/Excel ingestion, department-level risk bar charts, compensation band vs. tenure matrix[cite: 1].

### 3. 🚚 Delivery Delay & Operations Analytics

- **Objective**: Quantify supply chain bottlenecks, diagnose SLA breaches, and estimate dispatch risks[cite: 1, 2].
- **Core KPIs**: On-Time Delivery (OTD %), Delayed Shipments, Average Delay Duration (days).
- **Machine Learning**: Decision Tree classification estimating pre-dispatch delay probabilities with an interactive gauge.
- **Features**: Dynamic CSV/Excel ingestion, carrier performance charts, warehouse-product hotspot heatmaps.

---

## 🛠️ Technology Stack

- **Language**: Python
- **Analytics & Modeling**: Pandas, NumPy, Scikit-learn
- **Data Visualization**: Plotly Express, Plotly Graph Objects
- **Deployment & UI**: Streamlit Multi-Page Framework[cite: 2]
- **Version Control**: Git & GitHub[cite: 2]

---

## 📂 Repository Structure

```text
delivery_delay_analytics/
│
├── dashboard/
│   ├── app.py                              # Central Portfolio Landing Hub
│   └── pages/
│       ├── 1_🛒_Ecommerce_Sales.py         # Project 1: Sales & Customer Analytics
│       ├── 2_👥_Employee_Attrition.py      # Project 2: Workforce & Retention Analytics
│       └── 3_🚚_Delivery_Operations.py     # Project 3: Operations & ML Delay Risk
│
├── data/
│   ├── raw/                                # Raw input datasets
│   └── processed/                          # Preprocessed data records
│
├── src/
│   ├── data_pipeline.py                    # Schema normalization & metric computation
│   └── model.py                            # Decision Tree training & artifact serialization
│
├── models/
│   ├── delay_classifier.pkl                # Trained model artifact
│   └── model_metadata.json                 # Model performance report & top features
│
├── requirements.txt                        # Python dependencies
├── .gitignore                              # Git exclusion rules
└── README.md                               # Project documentation
```
