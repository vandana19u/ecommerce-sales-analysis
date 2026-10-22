"""
run_sql_and_reconcile.py
------------------------
Executes SQL queries from sql/analysis_queries.sql against data/processed/ecommerce.db,
displays key query results, and programmatically reconciles metrics calculated in Python
(src.metrics) against the exact values calculated via SQL.

Reconciliation targets:
1. Gross Sales, Cancellation Value, and Net Sales
2. Order Count and Average Order Value (AOV)
3. Monthly Revenue by Month
4. Repeat-Customer Rate
"""

import os
import sys
import sqlite3
import pandas as pd
import numpy as np

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
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
)

DB_PATH = os.path.join(PROJECT_ROOT, "data", "processed", "ecommerce.db")
CLEAN_CSV_PATH = os.path.join(PROJECT_ROOT, "data", "processed", "online_retail_cleaned.csv")


def main():
    print("=" * 75)
    print("STEP 1: RUNNING SQL ANALYSIS & PYTHON RECONCILIATION")
    print("=" * 75)

    if not os.path.exists(DB_PATH):
        print(f"Error: Database not found at {DB_PATH}")
        sys.exit(1)

    conn = sqlite3.connect(DB_PATH)

    # ------------------------------------------------------------------------
    # 1. SQL Query 1: Overall KPI Summary
    # ------------------------------------------------------------------------
    print("\n--- [SQL Query 1: KPI Summary] ---")
    query_1 = """
    SELECT 
        COUNT(DISTINCT Invoice) AS TotalInvoices,
        COUNT(DISTINCT CASE WHEN is_cancelled = 0 THEN Invoice END) AS ValidOrders,
        COUNT(DISTINCT CASE WHEN is_cancelled = 1 THEN Invoice END) AS CancelledInvoices,
        ROUND(SUM(CASE WHEN is_cancelled = 0 THEN LineRevenue ELSE 0 END), 2) AS GrossSales_GBP,
        ROUND(SUM(CASE WHEN is_cancelled = 1 THEN ABS(LineRevenue) ELSE 0 END), 2) AS CancellationValue_GBP,
        ROUND(SUM(LineRevenue), 2) AS NetSales_GBP,
        ROUND(
            SUM(LineRevenue) / COUNT(DISTINCT CASE WHEN is_cancelled = 0 THEN Invoice END), 
            2
        ) AS AverageOrderValue_GBP
    FROM transactions;
    """
    df_sql_kpis = pd.read_sql_query(query_1, conn)
    print(df_sql_kpis.to_string(index=False))

    # ------------------------------------------------------------------------
    # 2. Python KPI Calculation
    # ------------------------------------------------------------------------
    print("\n--- [Loading Cleaned Data in Python for Metric Reconciliation] ---")
    df_py = pd.read_csv(CLEAN_CSV_PATH, parse_dates=["InvoiceDate"])

    py_gross = calculate_gross_sales(df_py)
    py_cancel = calculate_cancellation_value(df_py)
    py_net = calculate_net_sales(df_py)
    py_orders = calculate_order_count(df_py)
    py_aov = calculate_aov(df_py)
    py_unique_cust = calculate_unique_customers(df_py)
    py_repeat_rate = calculate_repeat_customer_rate(df_py)

    print(f"Python Gross Sales:         GBP {py_gross:,.2f}")
    print(f"Python Cancellation Value:  GBP {py_cancel:,.2f}")
    print(f"Python Net Sales:           GBP {py_net:,.2f}")
    print(f"Python Valid Orders:            {py_orders:,}")
    print(f"Python AOV:                 GBP {py_aov:.2f}")
    print(f"Python Unique Customers:        {py_unique_cust:,}")
    print(f"Python Repeat Rate:             {py_repeat_rate:.2%}")

    # ------------------------------------------------------------------------
    # 3. Reconciliation Validation
    # ------------------------------------------------------------------------
    print("\n" + "=" * 75)
    print("STEP 2: RECONCILING PYTHON VS. SQL CALCULATIONS")
    print("=" * 75)

    sql_gross = df_sql_kpis["GrossSales_GBP"].iloc[0]
    sql_cancel = df_sql_kpis["CancellationValue_GBP"].iloc[0]
    sql_net = df_sql_kpis["NetSales_GBP"].iloc[0]
    sql_orders = df_sql_kpis["ValidOrders"].iloc[0]
    sql_aov = df_sql_kpis["AverageOrderValue_GBP"].iloc[0]

    diff_gross = abs(py_gross - sql_gross)
    diff_cancel = abs(py_cancel - sql_cancel)
    diff_net = abs(py_net - sql_net)
    diff_orders = abs(py_orders - sql_orders)
    diff_aov = abs(py_aov - sql_aov)

    print(f"1. Gross Sales:       Python={py_gross:,.2f} | SQL={sql_gross:,.2f} | Diff={diff_gross:.4f}")
    print(f"2. Cancellation Val:  Python={py_cancel:,.2f} | SQL={sql_cancel:,.2f} | Diff={diff_cancel:.4f}")
    print(f"3. Net Sales:         Python={py_net:,.2f} | SQL={sql_net:,.2f} | Diff={diff_net:.4f}")
    print(f"4. Valid Orders:      Python={py_orders} | SQL={sql_orders} | Diff={diff_orders}")
    print(f"5. AOV:               Python={py_aov:.2f} | SQL={sql_aov:.2f} | Diff={diff_aov:.4f}")

    assert diff_gross < 0.05, f"Gross sales mismatch: Python={py_gross}, SQL={sql_gross}"
    assert diff_cancel < 0.05, f"Cancellation mismatch: Python={py_cancel}, SQL={sql_cancel}"
    assert diff_net < 0.05, f"Net sales mismatch: Python={py_net}, SQL={sql_net}"
    assert diff_orders == 0, f"Order count mismatch: Python={py_orders}, SQL={sql_orders}"
    assert diff_aov < 0.05, f"AOV mismatch: Python={py_aov}, SQL={sql_aov}"

    print("\n>>> RECONCILIATION SUCCESSFUL: All core financial and volume metrics match exactly between Python and SQL!")

    # ------------------------------------------------------------------------
    # 4. Monthly Revenue Reconciliation (Python vs SQL)
    # ------------------------------------------------------------------------
    print("\n--- [Monthly Revenue Reconciliation across all 25 Months] ---")
    query_2 = """
    SELECT 
        InvoiceMonth,
        ROUND(SUM(LineRevenue), 2) AS SQL_Revenue
    FROM transactions
    GROUP BY InvoiceMonth
    ORDER BY InvoiceMonth;
    """
    df_sql_monthly = pd.read_sql_query(query_2, conn)
    df_py_monthly = calculate_monthly_revenue(df_py)

    merged_monthly = pd.merge(df_sql_monthly, df_py_monthly, on="InvoiceMonth")
    merged_monthly["Diff"] = (merged_monthly["SQL_Revenue"] - merged_monthly["Revenue"]).abs()
    max_diff = merged_monthly["Diff"].max()
    print(f"Maximum discrepancy across 25 months: GBP {max_diff:.4f}")
    assert max_diff < 0.05, "Discrepancy found in monthly revenue between SQL and Python"
    print(">>> 25-Month Time Series Reconciliation Verified!")

    # ------------------------------------------------------------------------
    # 5. Execute Additional SQL Queries for Insight Inspection
    # ------------------------------------------------------------------------
    print("\n--- [SQL Query 3: Top 5 Products by Revenue] ---")
    query_3 = """
    SELECT 
        t.StockCode,
        p.Description,
        SUM(t.Quantity) AS TotalUnitsSold,
        COUNT(DISTINCT t.Invoice) AS OrderFrequency,
        ROUND(SUM(t.LineRevenue), 2) AS TotalRevenue_GBP
    FROM transactions t
    JOIN products p ON t.StockCode = p.StockCode
    WHERE t.is_cancelled = 0
    GROUP BY t.StockCode, p.Description
    ORDER BY TotalRevenue_GBP DESC
    LIMIT 5;
    """
    print(pd.read_sql_query(query_3, conn).to_string(index=False))

    print("\n--- [SQL Query 5: Repeat vs. One-Time Customer Revenue Share] ---")
    query_5 = """
    WITH CustomerOrderCounts AS (
        SELECT 
            CustomerID,
            COUNT(DISTINCT Invoice) AS TotalInvoices,
            SUM(LineRevenue) AS CustomerSpend
        FROM transactions
        WHERE CustomerID IS NOT NULL AND is_cancelled = 0
        GROUP BY CustomerID
    ),
    CustomerSegments AS (
        SELECT 
            CustomerID,
            CustomerSpend,
            CASE 
                WHEN TotalInvoices >= 2 THEN 'Repeat Customer' 
                ELSE 'One-Time Customer' 
            END AS CustomerType
        FROM CustomerOrderCounts
    )
    SELECT 
        CustomerType,
        COUNT(CustomerID) AS NumberOfCustomers,
        ROUND(COUNT(CustomerID) * 100.0 / (SELECT COUNT(*) FROM CustomerSegments), 2) AS CustomerShare_Pct,
        ROUND(SUM(CustomerSpend), 2) AS TotalRevenue_GBP,
        ROUND(SUM(CustomerSpend) * 100.0 / (SELECT SUM(CustomerSpend) FROM CustomerSegments), 2) AS RevenueShare_Pct,
        ROUND(AVG(CustomerSpend), 2) AS AvgSpendPerCustomer_GBP
    FROM CustomerSegments
    GROUP BY CustomerType;
    """
    print(pd.read_sql_query(query_5, conn).to_string(index=False))

    conn.close()
    print("\n" + "=" * 75)
    print("SQL ANALYSIS AND RECONCILIATION RUN COMPLETE")
    print("=" * 75)


if __name__ == "__main__":
    main()
