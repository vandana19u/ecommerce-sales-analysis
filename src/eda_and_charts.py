"""
eda_and_charts.py
-----------------
Generates 7 publication-ready visualizations answering the core business questions
using actual computed figures from the cleaned dataset.

Charts saved to reports/figures/:
1. 01_monthly_revenue_and_growth.png (Q1: Monthly revenue & MoM growth)
2. 02_top_products_revenue.png       (Q2: Top revenue generating products)
3. 03_top_international_markets.png  (Q3: Non-UK international markets)
4. 04_repeat_vs_onetime_revenue.png  (Q4: Repeat customer revenue share)
5. 05_cancellation_trend.png         (Q6: Monthly cancellation rate & loss)
6. 06_hourly_weekly_demand.png       (Operational: Day & hour order heatmap)
7. 07_rfm_customer_segments.png      (Q7: RFM Customer segments value & size)
"""

import os
import sys
import sqlite3
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIGURES_DIR = os.path.join(PROJECT_ROOT, "reports", "figures")
DB_PATH = os.path.join(PROJECT_ROOT, "data", "processed", "ecommerce.db")
CLEAN_CSV = os.path.join(PROJECT_ROOT, "data", "processed", "online_retail_cleaned.csv")

# Set visualization aesthetics
plt.style.use("seaborn-v0_8-whitegrid" if "seaborn-v0_8-whitegrid" in plt.style.available else "default")
plt.rcParams["font.family"] = "sans-serif"
plt.rcParams["font.size"] = 10
plt.rcParams["axes.titlesize"] = 12
plt.rcParams["axes.titleweight"] = "bold"
plt.rcParams["axes.labelsize"] = 10
plt.rcParams["figure.dpi"] = 300


def main():
    os.makedirs(FIGURES_DIR, exist_ok=True)
    print("=" * 70)
    print("GENERATING PUBLICATION-READY CHARTS (7 BUSINESS QUESTIONS)")
    print("=" * 70)

    conn = sqlite3.connect(DB_PATH)

    # ------------------------------------------------------------------------
    # CHART 1: Monthly Net Revenue Trend and MoM Growth (Q1)
    # ------------------------------------------------------------------------
    print("Generating Chart 1: Monthly Revenue & MoM Growth...")
    q1 = """
    WITH Monthly AS (
        SELECT 
            InvoiceMonth,
            ROUND(SUM(LineRevenue), 2) AS Revenue
        FROM transactions
        GROUP BY InvoiceMonth
    )
    SELECT 
        InvoiceMonth,
        Revenue,
        LAG(Revenue) OVER (ORDER BY InvoiceMonth) AS PrevRevenue,
        ROUND((Revenue - LAG(Revenue) OVER (ORDER BY InvoiceMonth)) * 100.0 / LAG(Revenue) OVER (ORDER BY InvoiceMonth), 2) AS MoM_Growth
    FROM Monthly
    ORDER BY InvoiceMonth;
    """
    df_m = pd.read_sql_query(q1, conn)

    fig, ax1 = plt.subplots(figsize=(12, 6))

    # Bar chart for revenue
    x_indices = np.arange(len(df_m))
    bars = ax1.bar(x_indices, df_m["Revenue"] / 1000, color="#1f77b4", alpha=0.85, width=0.6, label="Net Revenue (£'000)")
    ax1.set_ylabel("Monthly Net Revenue (£ Thousands)", color="#1f77b4", fontweight="bold")
    ax1.set_xticks(x_indices)
    ax1.set_xticklabels(df_m["InvoiceMonth"], rotation=45, ha="right")
    ax1.grid(axis="y", linestyle="--", alpha=0.5)

    # Line chart for MoM Growth on twin axis
    ax2 = ax1.twinx()
    valid_mom = df_m.dropna(subset=["MoM_Growth"])
    ax2.plot(valid_mom.index, valid_mom["MoM_Growth"], color="#d62728", marker="o", linewidth=2, label="MoM Growth Rate (%)")
    ax2.axhline(0, color="gray", linestyle=":", linewidth=1)
    ax2.set_ylabel("Month-over-Month Growth (%)", color="#d62728", fontweight="bold")
    ax2.grid(False)

    plt.title("Figure 1: Monthly Net Revenue Trend & MoM Growth Rate (Dec 2009 – Dec 2011)", pad=15)
    fig.tight_layout()
    chart1_path = os.path.join(FIGURES_DIR, "01_monthly_revenue_and_growth.png")
    fig.savefig(chart1_path)
    plt.close(fig)
    print(f"  [OK] Saved {chart1_path}")

    # ------------------------------------------------------------------------
    # CHART 2: Top 10 Revenue-Generating Products (Q2)
    # ------------------------------------------------------------------------
    print("Generating Chart 2: Top Products by Revenue...")
    q2 = """
    SELECT 
        t.StockCode,
        p.Description,
        SUM(t.Quantity) AS UnitsSold,
        ROUND(SUM(t.LineRevenue), 2) AS TotalRevenue
    FROM transactions t
    JOIN products p ON t.StockCode = p.StockCode
    WHERE t.is_cancelled = 0
      AND t.StockCode NOT IN ('POST', 'M', 'DOT', 'D', 'BANK CHARGES', 'AMAZONFEE')
    GROUP BY t.StockCode, p.Description
    ORDER BY TotalRevenue DESC
    LIMIT 10;
    """
    df_prod = pd.read_sql_query(q2, conn)
    df_prod = df_prod.sort_values("TotalRevenue", ascending=True)

    fig, ax = plt.subplots(figsize=(10, 6))
    bars = ax.barh(df_prod["Description"], df_prod["TotalRevenue"] / 1000, color="#2ca02c", alpha=0.85, height=0.65)
    ax.set_xlabel("Total Net Revenue (£ Thousands)", fontweight="bold")
    ax.set_title("Figure 2: Top 10 Commercial Merchandise Products by Total Revenue", pad=15)
    ax.grid(axis="x", linestyle="--", alpha=0.5)

    # Add data labels
    for bar in bars:
        w = bar.get_width()
        ax.annotate(f"£{w:,.1f}k",
                    xy=(w, bar.get_y() + bar.get_height() / 2),
                    xytext=(5, 0), textcoords="offset points",
                    ha="left", va="center", fontsize=9, fontweight="bold")

    ax.set_xlim(0, df_prod["TotalRevenue"].max() / 1000 * 1.15)
    fig.tight_layout()
    chart2_path = os.path.join(FIGURES_DIR, "02_top_products_revenue.png")
    fig.savefig(chart2_path)
    plt.close(fig)
    print(f"  [OK] Saved {chart2_path}")

    # ------------------------------------------------------------------------
    # CHART 3: Top International Markets outside UK (Q3)
    # ------------------------------------------------------------------------
    print("Generating Chart 3: International Markets...")
    q3 = """
    SELECT 
        Country,
        COUNT(DISTINCT CustomerID) AS Customers,
        ROUND(SUM(LineRevenue), 2) AS NetRevenue
    FROM transactions
    WHERE Country != 'United Kingdom' AND is_cancelled = 0
    GROUP BY Country
    ORDER BY NetRevenue DESC
    LIMIT 10;
    """
    df_cntry = pd.read_sql_query(q3, conn).sort_values("NetRevenue", ascending=True)

    fig, ax = plt.subplots(figsize=(10, 6))
    bars = ax.barh(df_cntry["Country"], df_cntry["NetRevenue"] / 1000, color="#ff7f0e", alpha=0.85, height=0.65)
    ax.set_xlabel("Total Net Revenue (£ Thousands)", fontweight="bold")
    ax.set_title("Figure 3: Top 10 International Revenue-Generating Countries (Excl. UK)", pad=15)
    ax.grid(axis="x", linestyle="--", alpha=0.5)

    for bar in bars:
        w = bar.get_width()
        ax.annotate(f"£{w:,.1f}k",
                    xy=(w, bar.get_y() + bar.get_height() / 2),
                    xytext=(5, 0), textcoords="offset points",
                    ha="left", va="center", fontsize=9, fontweight="bold")

    ax.set_xlim(0, df_cntry["NetRevenue"].max() / 1000 * 1.15)
    fig.tight_layout()
    chart3_path = os.path.join(FIGURES_DIR, "03_top_international_markets.png")
    fig.savefig(chart3_path)
    plt.close(fig)
    print(f"  [OK] Saved {chart3_path}")

    # ------------------------------------------------------------------------
    # CHART 4: Repeat vs. One-Time Customers Revenue & Count (Q4)
    # ------------------------------------------------------------------------
    print("Generating Chart 4: Repeat vs. One-Time Customers...")
    q4 = """
    WITH CustTotals AS (
        SELECT 
            CustomerID,
            COUNT(DISTINCT Invoice) AS Invoices,
            SUM(LineRevenue) AS Spend
        FROM transactions
        WHERE CustomerID IS NOT NULL AND is_cancelled = 0
        GROUP BY CustomerID
    )
    SELECT 
        CASE WHEN Invoices >= 2 THEN 'Repeat Customer (>=2 Orders)' ELSE 'One-Time Customer (1 Order)' END AS Segment,
        COUNT(CustomerID) AS CustomerCount,
        ROUND(SUM(Spend), 2) AS TotalRevenue
    FROM CustTotals
    GROUP BY Segment;
    """
    df_rep = pd.read_sql_query(q4, conn)

    fig, (ax_left, ax_right) = plt.subplots(1, 2, figsize=(11, 5))

    # Pie 1: Customer Count Share
    colors = ["#1f77b4", "#aec7e8"]
    ax_left.pie(
        df_rep["CustomerCount"], 
        labels=df_rep["Segment"], 
        autopct="%1.1f%%", 
        startangle=140, 
        colors=colors,
        explode=[0.05, 0],
        textprops={"fontsize": 10, "weight": "bold"}
    )
    ax_left.set_title("Customer Population Share\n(Total: 5,878 Customers)", fontweight="bold")

    # Pie 2: Revenue Share
    colors_rev = ["#2ca02c", "#98df8a"]
    ax_right.pie(
        df_rep["TotalRevenue"], 
        labels=df_rep["Segment"], 
        autopct="%1.1f%%", 
        startangle=140, 
        colors=colors_rev,
        explode=[0.05, 0],
        textprops={"fontsize": 10, "weight": "bold"}
    )
    ax_right.set_title("Revenue Contribution Share\n(Total: £17.74M Tracked Revenue)", fontweight="bold")

    plt.suptitle("Figure 4: Repeat Customers vs. One-Time Buyers — The Retention Engine", fontsize=13, weight="bold", y=1.02)
    fig.tight_layout()
    chart4_path = os.path.join(FIGURES_DIR, "04_repeat_vs_onetime_revenue.png")
    fig.savefig(chart4_path)
    plt.close(fig)
    print(f"  [OK] Saved {chart4_path}")

    # ------------------------------------------------------------------------
    # CHART 5: Monthly Cancellations Financial Impact (Q6)
    # ------------------------------------------------------------------------
    print("Generating Chart 5: Cancellation Rate & Value...")
    q5 = """
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
    """
    df_canc = pd.read_sql_query(q5, conn)

    fig, ax1 = plt.subplots(figsize=(12, 6))
    x = np.arange(len(df_canc))

    # Stacked / paired view
    ax1.bar(x, df_canc["GrossSales"] / 1000, color="#1f77b4", alpha=0.7, width=0.6, label="Gross Sales (£'000)")
    ax1.bar(x, df_canc["CancellationLoss"] / 1000, color="#d62728", alpha=0.85, width=0.6, label="Cancellation Loss (£'000)")
    ax1.set_ylabel("Financial Volume (£ Thousands)", fontweight="bold")
    ax1.set_xticks(x)
    ax1.set_xticklabels(df_canc["InvoiceMonth"], rotation=45, ha="right")
    ax1.legend(loc="upper left")

    ax2 = ax1.twinx()
    ax2.plot(x, df_canc["CancellationLossPct"], color="#ff7f0e", marker="s", linewidth=2, linestyle="--", label="Loss % of Gross")
    ax2.set_ylabel("Cancellations as % of Gross Sales", color="#ff7f0e", fontweight="bold")
    ax2.set_ylim(0, max(df_canc["CancellationLossPct"]) * 1.3)
    ax2.legend(loc="upper right")
    ax2.grid(False)

    plt.title("Figure 5: Monthly Cancellation Volume and Financial Loss Rate (Dec 2009 – Dec 2011)", pad=15)
    fig.tight_layout()
    chart5_path = os.path.join(FIGURES_DIR, "05_cancellation_trend.png")
    fig.savefig(chart5_path)
    plt.close(fig)
    print(f"  [OK] Saved {chart5_path}")

    # ------------------------------------------------------------------------
    # CHART 6: Hourly and Weekly Demand Heatmap (Operational)
    # ------------------------------------------------------------------------
    print("Generating Chart 6: Order Demand Heatmap...")
    q6 = """
    SELECT 
        DayOfWeek,
        InvoiceHour,
        COUNT(DISTINCT Invoice) AS OrderCount
    FROM transactions
    WHERE is_cancelled = 0
    GROUP BY DayOfWeek, InvoiceHour;
    """
    df_heat = pd.read_sql_query(q6, conn)
    days_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Sunday"]
    pivot_heat = df_heat.pivot(index="DayOfWeek", columns="InvoiceHour", values="OrderCount").reindex(days_order).fillna(0)

    fig, ax = plt.subplots(figsize=(12, 5))
    sns.heatmap(pivot_heat, cmap="YlGnBu", annot=True, fmt=".0f", cbar_kws={"label": "Order Count"}, ax=ax)
    ax.set_title("Figure 6: Transaction Volume Heatmap by Day of Week & Hour of Day", pad=15)
    ax.set_xlabel("Hour of Day (24h Clock)", fontweight="bold")
    ax.set_ylabel("Day of Week", fontweight="bold")
    fig.tight_layout()
    chart6_path = os.path.join(FIGURES_DIR, "06_hourly_weekly_demand.png")
    fig.savefig(chart6_path)
    plt.close(fig)
    print(f"  [OK] Saved {chart6_path}")

    # ------------------------------------------------------------------------
    # CHART 7: RFM Customer Segmentation (Q7)
    # ------------------------------------------------------------------------
    print("Generating Chart 7: RFM Customer Segments...")
    # Reference date is 2011-12-10 (1 day after max date 2011-12-09)
    q7 = """
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
    """
    df_rfm = pd.read_sql_query(q7, conn)

    # Calculate RFM Quintiles (1-5) using pd.qcut with rank method to handle ties safely
    df_rfm["R_Score"] = pd.qcut(df_rfm["Recency"], 5, labels=[5, 4, 3, 2, 1]).astype(int)
    df_rfm["F_Score"] = pd.qcut(df_rfm["Frequency"].rank(method="first"), 5, labels=[1, 2, 3, 4, 5]).astype(int)
    df_rfm["M_Score"] = pd.qcut(df_rfm["Monetary"].rank(method="first"), 5, labels=[1, 2, 3, 4, 5]).astype(int)

    # Segment mapping based on R_Score and F_Score
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

    # Aggregate by Segment
    seg_summary = df_rfm.groupby("Segment").agg(
        CustomerCount=("CustomerID", "count"),
        TotalRevenue=("Monetary", "sum"),
        AvgSpend=("Monetary", "mean"),
        AvgRecencyDays=("Recency", "mean"),
        AvgOrders=("Frequency", "mean")
    ).reset_index().sort_values("TotalRevenue", ascending=False)

    print("\nRFM Segment Summary Table:")
    print(seg_summary.to_string(index=False))

    fig, ax1 = plt.subplots(figsize=(11, 6))
    x = np.arange(len(seg_summary))
    width = 0.38

    bars1 = ax1.bar(x - width/2, seg_summary["CustomerCount"], width=width, color="#4c72b0", label="Customer Count")
    ax1.set_ylabel("Number of Customers", color="#4c72b0", fontweight="bold")
    ax1.set_xticks(x)
    ax1.set_xticklabels(seg_summary["Segment"], rotation=30, ha="right", fontweight="bold")
    ax1.grid(axis="y", linestyle="--", alpha=0.5)

    ax2 = ax1.twinx()
    bars2 = ax2.bar(x + width/2, seg_summary["TotalRevenue"] / 1000, width=width, color="#55a868", label="Total Revenue (£'000)")
    ax2.set_ylabel("Total Revenue (£ Thousands)", color="#55a868", fontweight="bold")
    ax2.grid(False)

    # Combine legends
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc="upper right")

    plt.title("Figure 7: RFM Customer Segments — Customer Count vs. Total Revenue (£'000)", pad=15)
    fig.tight_layout()
    chart7_path = os.path.join(FIGURES_DIR, "07_rfm_customer_segments.png")
    fig.savefig(chart7_path)
    plt.close(fig)
    print(f"  [OK] Saved {chart7_path}")

    conn.close()
    print("\n" + "=" * 70)
    print("ALL 7 CHARTS CREATED SUCCESSFULLY IN reports/figures/")
    print("=" * 70)


if __name__ == "__main__":
    main()
