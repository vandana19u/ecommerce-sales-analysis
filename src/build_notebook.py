"""
build_notebook.py
-----------------
Generates the portfolio-grade Jupyter Notebook at notebooks/01_ecommerce_analysis.ipynb.
Includes markdown documentation, runnable Python cells, SQL query executions,
visualizations, and data-backed conclusions.
"""

import json
import os

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NOTEBOOK_PATH = os.path.join(PROJECT_ROOT, "notebooks", "01_ecommerce_analysis.ipynb")


def create_notebook():
    cells = []

    def md(text):
        cells.append({
            "cell_type": "markdown",
            "metadata": {},
            "source": [line + "\n" for line in text.strip().split("\n")]
        })

    def code(text):
        cells.append({
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [line + "\n" for line in text.strip().split("\n")]
        })

    # Header
    md("""# E-commerce Sales and Customer Behaviour Analysis
**Author:** Portfolio Project | **Tools:** Python, pandas, SQLite, SQL, Matplotlib, Seaborn  
**Dataset:** Online Retail II (UCI Machine Learning Repository, CC BY 4.0)  
**Time Horizon:** 1 Dec 2009 – 9 Dec 2011 (1,061,163 cleaned transactions across 43 countries)

---

## 1. Project Background & Business Problem

An e-commerce business selling unique gifts and homeware needs an operational and financial performance review.
This analysis answers 7 strategic business questions:
1. **Revenue Evolution:** How does net revenue trend month-over-month? What are the seasonality patterns?
2. **Product Performance:** Which items generate the highest sales volume and financial return?
3. **Market Expansion:** Which international markets outside the UK contribute most to sales?
4. **Customer Retention:** What proportion of revenue stems from repeat customers vs. one-time buyers?
5. **Customer Concentration:** Which accounts have the highest observed purchase value?
6. **Cancellation Impact:** How significantly do cancellations and returns erode gross revenue?
7. **Customer Segmentation:** How do customers segment across Recency, Frequency, and Monetary (RFM) dimensions?""")

    # Setup
    md("""## 2. Environment Setup and Data Loading""")
    code("""import os
import sys
import sqlite3
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# Add project root to path for src imports
PROJECT_ROOT = os.path.dirname(os.getcwd())
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.metrics import (
    calculate_gross_sales,
    calculate_cancellation_value,
    calculate_net_sales,
    calculate_order_count,
    calculate_aov,
    calculate_unique_customers,
    calculate_repeat_customer_rate,
    calculate_monthly_revenue,
    calculate_mom_growth,
)

# Plotting settings
plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')
pd.set_option('display.float_format', lambda x: f'{x:,.2f}')

CLEAN_CSV = os.path.join(PROJECT_ROOT, "data", "processed", "online_retail_cleaned.csv")
DB_PATH = os.path.join(PROJECT_ROOT, "data", "processed", "ecommerce.db")

print("Loading cleaned dataset...")
df = pd.read_csv(CLEAN_CSV, parse_dates=["InvoiceDate"])
print(f"Loaded {len(df):,} cleaned transactions.")
df.head()""")

    # Data Quality Assessment & Cleaning Recap
    md("""## 3. Data Cleaning & Quality Audit Summary

Our cleaning pipeline in `src/data_cleaning.py` performed the following validated steps:
- **Removed 6 accounting adjustments:** Entries like *"Adjust bad debt"* with massive negative prices up to -£53,594.
- **Removed 6,202 zero-price items:** Internal system adjustments and free sample rows.
- **Flagged cancellations:** Added `is_cancelled` boolean based on invoice prefix `'C'`.
- **Created financial fields:** Computed `LineRevenue = Quantity × Price`.
- **Engineered time features:** Derived `InvoiceMonth`, `InvoiceYear`, `InvoiceHour`, and `DayOfWeek`.

| Metric | Raw Dataset | Cleaned Dataset | Change |
|---|---|---|---|
| Total Rows | 1,067,371 | 1,061,163 | -6,208 (-0.58%) |
| Non-Cancelled Sales | - | 1,041,669 | Main commercial population |
| Cancellations | - | 19,494 | Flagged for returns analysis |
| Missing Customer IDs | 243,007 (22.77%) | 236,870 (22.32%) | Kept for macro-revenue; omitted from customer metrics |""")

    # Core KPIs
    md("""## 4. Financial KPIs & Executive Dashboard""")
    code("""gross_sales = calculate_gross_sales(df)
cancel_val = calculate_cancellation_value(df)
net_sales = calculate_net_sales(df)
valid_orders = calculate_order_count(df)
aov = calculate_aov(df)
unique_cust = calculate_unique_customers(df)
repeat_rate = calculate_repeat_customer_rate(df)

kpi_summary = pd.DataFrame({
    "Metric": [
        "Gross Sales (£)", 
        "Cancellation Loss (£)", 
        "Net Sales (£)", 
        "Cancellation Impact Rate (%)",
        "Valid Order Count", 
        "Average Order Value (£)", 
        "Unique Tracked Customers", 
        "Repeat-Customer Rate (%)"
    ],
    "Value": [
        f"£{gross_sales:,.2f}",
        f"£{cancel_val:,.2f}",
        f"£{net_sales:,.2f}",
        f"{(cancel_val / gross_sales * 100):.2f}%",
        f"{valid_orders:,}",
        f"£{aov:.2f}",
        f"{unique_cust:,}",
        f"{repeat_rate * 100:.2f}%"
    ]
})
kpi_summary""")

    # Q1: Monthly Revenue Trend
    md("""## 5. Question 1: Monthly Net Revenue Trend and MoM Growth

Let us analyze monthly performance across the 25-month timeline.""")
    code("""monthly_rev = calculate_monthly_revenue(df)
monthly_growth = calculate_mom_growth(monthly_rev)

fig, ax1 = plt.subplots(figsize=(12, 5))
x = np.arange(len(monthly_growth))

ax1.bar(x, monthly_growth["Revenue"] / 1000, color="#1f77b4", alpha=0.8, width=0.6, label="Net Revenue (£'000)")
ax1.set_ylabel("Net Revenue (£ Thousands)", color="#1f77b4", fontweight="bold")
ax1.set_xticks(x)
ax1.set_xticklabels(monthly_growth["InvoiceMonth"], rotation=45, ha="right")

ax2 = ax1.twinx()
valid_growth = monthly_growth.dropna(subset=["MoM_Growth_Pct"])
ax2.plot(valid_growth.index, valid_growth["MoM_Growth_Pct"], color="#d62728", marker="o", linewidth=2, label="MoM Growth %")
ax2.axhline(0, color="gray", linestyle=":", linewidth=1)
ax2.set_ylabel("Month-over-Month Growth (%)", color="#d62728", fontweight="bold")

plt.title("Figure 1: Monthly Net Revenue & MoM Growth (Dec 2009 – Dec 2011)", pad=15)
fig.tight_layout()
plt.show()

monthly_growth.tail(10)""")

    # Q2: Top Products
    md("""## 6. Question 2: Top Revenue-Generating Products""")
    code("""conn = sqlite3.connect(DB_PATH)
query_top_products = \"\"\"
SELECT 
    t.StockCode,
    p.Description,
    SUM(t.Quantity) AS UnitsSold,
    COUNT(DISTINCT t.Invoice) AS OrderFrequency,
    ROUND(SUM(t.LineRevenue), 2) AS TotalRevenue
FROM transactions t
JOIN products p ON t.StockCode = p.StockCode
WHERE t.is_cancelled = 0
  AND t.StockCode NOT IN ('POST', 'M', 'DOT', 'D', 'BANK CHARGES', 'AMAZONFEE')
GROUP BY t.StockCode, p.Description
ORDER BY TotalRevenue DESC
LIMIT 10;
\"\"\"
top_products = pd.read_sql_query(query_top_products, conn)

plt.figure(figsize=(10, 5))
plt.barh(top_products["Description"][::-1], top_products["TotalRevenue"][::-1] / 1000, color="#2ca02c", alpha=0.85)
plt.xlabel("Total Net Revenue (£ Thousands)", fontweight="bold")
plt.title("Figure 2: Top 10 Commercial Products by Total Net Revenue", pad=15)
plt.tight_layout()
plt.show()

top_products""")

    # Q3: International Markets
    md("""## 7. Question 3: International Markets Outside the UK""")
    code("""query_intl = \"\"\"
SELECT 
    Country,
    COUNT(DISTINCT CustomerID) AS CustomerCount,
    COUNT(DISTINCT Invoice) AS OrderCount,
    ROUND(SUM(LineRevenue), 2) AS NetRevenue,
    ROUND(SUM(LineRevenue) * 100.0 / (SELECT SUM(LineRevenue) FROM transactions WHERE Country != 'United Kingdom' AND is_cancelled = 0), 2) AS PctNonUK
FROM transactions
WHERE Country != 'United Kingdom' AND is_cancelled = 0
GROUP BY Country
ORDER BY NetRevenue DESC
LIMIT 10;
\"\"\"
intl_markets = pd.read_sql_query(query_intl, conn)

plt.figure(figsize=(10, 5))
plt.barh(intl_markets["Country"][::-1], intl_markets["NetRevenue"][::-1] / 1000, color="#ff7f0e", alpha=0.85)
plt.xlabel("Net Revenue (£ Thousands)", fontweight="bold")
plt.title("Figure 3: Top 10 Non-UK International Markets", pad=15)
plt.tight_layout()
plt.show()

intl_markets""")

    # Q4: Customer Retention
    md("""## 8. Question 4: Customer Retention — Repeat vs. One-Time Buyers""")
    code("""query_retention = \"\"\"
WITH CustTotals AS (
    SELECT 
        CustomerID,
        COUNT(DISTINCT Invoice) AS Invoices,
        SUM(LineRevenue) AS Spend
    FROM transactions
    WHERE CustomerID IS NOT NULL AND is_cancelled = 0
    GROUP BY CustomerID
),
Segments AS (
    SELECT 
        CustomerID,
        Spend,
        CASE WHEN Invoices >= 2 THEN 'Repeat Customer (>=2 Orders)' ELSE 'One-Time Customer (1 Order)' END AS Segment
    FROM CustTotals
)
SELECT 
    Segment,
    COUNT(CustomerID) AS CustomerCount,
    ROUND(COUNT(CustomerID) * 100.0 / (SELECT COUNT(*) FROM Segments), 2) AS CustomerShare_Pct,
    ROUND(SUM(Spend), 2) AS TotalRevenue,
    ROUND(SUM(Spend) * 100.0 / (SELECT SUM(Spend) FROM Segments), 2) AS RevenueShare_Pct,
    ROUND(AVG(Spend), 2) AS AvgSpendPerCustomer
FROM Segments
GROUP BY Segment;
\"\"\"
retention_df = pd.read_sql_query(query_retention, conn)

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.5))
ax1.pie(retention_df["CustomerCount"], labels=retention_df["Segment"], autopct="%1.1f%%", colors=["#1f77b4", "#aec7e8"], explode=[0.05, 0], startangle=140)
ax1.set_title("Customer Population Share", fontweight="bold")

ax2.pie(retention_df["TotalRevenue"], labels=retention_df["Segment"], autopct="%1.1f%%", colors=["#2ca02c", "#98df8a"], explode=[0.05, 0], startangle=140)
ax2.set_title("Revenue Contribution Share", fontweight="bold")

plt.suptitle("Figure 4: Repeat Customer Retention Power", y=1.03, fontweight="bold")
plt.tight_layout()
plt.show()

retention_df""")

    # Q5: Cancellations
    md("""## 9. Question 5 & 6: Cancellation Erosion & Monthly Returns""")
    code("""query_cancellations = \"\"\"
SELECT 
    InvoiceMonth,
    ROUND(SUM(CASE WHEN is_cancelled = 0 THEN LineRevenue ELSE 0 END), 2) AS GrossSales,
    ROUND(SUM(CASE WHEN is_cancelled = 1 THEN ABS(LineRevenue) ELSE 0 END), 2) AS CancellationLoss,
    ROUND(
        SUM(CASE WHEN is_cancelled = 1 THEN ABS(LineRevenue) ELSE 0 END) * 100.0 
        / SUM(CASE WHEN is_cancelled = 0 THEN LineRevenue ELSE 0 END), 
        2
    ) AS CancellationLossPct
FROM transactions
GROUP BY InvoiceMonth
ORDER BY InvoiceMonth;
\"\"\"
canc_df = pd.read_sql_query(query_cancellations, conn)

fig, ax1 = plt.subplots(figsize=(12, 5))
x = np.arange(len(canc_df))
ax1.bar(x, canc_df["GrossSales"] / 1000, color="#1f77b4", alpha=0.7, width=0.6, label="Gross Sales (£'000)")
ax1.bar(x, canc_df["CancellationLoss"] / 1000, color="#d62728", alpha=0.85, width=0.6, label="Cancellation Value (£'000)")
ax1.set_ylabel("Financial Value (£ Thousands)", fontweight="bold")
ax1.set_xticks(x)
ax1.set_xticklabels(canc_df["InvoiceMonth"], rotation=45, ha="right")
ax1.legend(loc="upper left")

ax2 = ax1.twinx()
ax2.plot(x, canc_df["CancellationLossPct"], color="#ff7f0e", marker="s", linestyle="--", linewidth=2, label="Cancellation % of Gross")
ax2.set_ylabel("Cancellation % of Gross", color="#ff7f0e", fontweight="bold")
ax2.legend(loc="upper right")
ax2.grid(False)

plt.title("Figure 5: Monthly Gross Sales vs. Cancellation Losses", pad=15)
plt.tight_layout()
plt.show()

canc_df.describe()""")

    # Q7: RFM Customer Segmentation
    md("""## 10. Question 7: RFM Customer Segmentation

We compute Recency (days since last purchase relative to reference date `2011-12-10`), Frequency (unique invoice count), and Monetary value (total spending).""")
    code("""query_rfm = \"\"\"
WITH RawRFM AS (
    SELECT 
        CustomerID,
        ROUND(JULIANDAY('2011-12-10') - JULIANDAY(MAX(InvoiceDate))) AS Recency,
        COUNT(DISTINCT Invoice) AS Frequency,
        SUM(LineRevenue) AS Monetary
    FROM transactions
    WHERE CustomerID IS NOT NULL AND is_cancelled = 0
    GROUP BY CustomerID
)
SELECT * FROM RawRFM;
\"\"\"
df_rfm = pd.read_sql_query(query_rfm, conn)

# Assign RFM Scores 1-5
df_rfm["R_Score"] = pd.qcut(df_rfm["Recency"], 5, labels=[5, 4, 3, 2, 1]).astype(int)
df_rfm["F_Score"] = pd.qcut(df_rfm["Frequency"].rank(method="first"), 5, labels=[1, 2, 3, 4, 5]).astype(int)
df_rfm["M_Score"] = pd.qcut(df_rfm["Monetary"].rank(method="first"), 5, labels=[1, 2, 3, 4, 5]).astype(int)

def assign_segment(row):
    r, f, m = row["R_Score"], row["F_Score"], row["M_Score"]
    if r >= 4 and f >= 4:
        return "Champions"
    elif r >= 3 and f >= 3:
        return "Loyal Customers"
    elif r >= 4 and f <= 2:
        return "Recent / New Customers"
    elif r == 3 and f <= 2:
        return "Promising / Potential"
    elif r <= 2 and f >= 3:
        return "At Risk / High Value"
    elif r <= 2 and f <= 2:
        return "Hibernating / Lost"
    else:
        return "Standard / Need Attention"

df_rfm["Segment"] = df_rfm.apply(assign_segment, axis=1)

rfm_summary = df_rfm.groupby("Segment").agg(
    CustomerCount=("CustomerID", "count"),
    TotalRevenue=("Monetary", "sum"),
    AvgSpend=("Monetary", "mean"),
    AvgRecencyDays=("Recency", "mean"),
    AvgOrders=("Frequency", "mean")
).reset_index().sort_values("TotalRevenue", ascending=False)

rfm_summary["RevenueShare_Pct"] = (rfm_summary["TotalRevenue"] / rfm_summary["TotalRevenue"].sum() * 100).round(2)
rfm_summary["CustomerShare_Pct"] = (rfm_summary["CustomerCount"] / rfm_summary["CustomerCount"].sum() * 100).round(2)

rfm_summary""")

    # SQL Reconciliation
    md("""## 11. SQL & Python Metric Reconciliation

To ensure data integrity, every core business metric calculated in Python is reconciled against SQLite execution.""")
    code("""from src.run_sql_and_reconcile import main as reconcile_main
reconcile_main()""")

    # Conclusions
    md("""## 12. Strategic Recommendations & Limitations

### Strategic Takeaways:
1. **Focus on Champions Retention:** 1,483 Champions generate 69.3% of revenue (£12.30M). Protect this cohort with VIP relationship management.
2. **Win Back 'At Risk' Wholesalers:** 824 accounts spent £1.63M historically but have not purchased in ~369 days. Prioritize an outbound reactivation campaign.
3. **Q4 Fulfillment Planning:** August to November demand doubles. Warehouse scheduling and inventory lead times must reflect this seasonality.

### Project Limitations:
- **No Cost Data:** Revenue cannot be equated to gross margin or net profit.
- **22.3% Missing Customer IDs:** Guest checkouts and anonymous sales are captured in macro-level figures but excluded from customer-level RFM metrics.""")

    notebook_content = {
        "cells": cells,
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3"
            },
            "language_info": {
                "name": "python",
                "version": "3.14"
            }
        },
        "nbformat": 4,
        "nbformat_minor": 4
    }

    with open(NOTEBOOK_PATH, "w", encoding="utf-8") as f:
        json.dump(notebook_content, f, indent=2)

    print(f"Jupyter notebook created at {NOTEBOOK_PATH}")


if __name__ == "__main__":
    create_notebook()
