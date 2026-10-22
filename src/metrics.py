"""
metrics.py
==========
Functions to calculate business metrics from cleaned e-commerce data.

All metric definitions match the project proposal documentation.
Each function takes a cleaned DataFrame and returns a single value or a
DataFrame/Series of results.

Usage:
    from src.metrics import calculate_gross_sales, calculate_aov
"""

import pandas as pd
import numpy as np


# ---------------------------------------------------------------------------
# Core revenue metrics
# ---------------------------------------------------------------------------

def calculate_gross_sales(df: pd.DataFrame) -> float:
    """
    Gross Sales = SUM(LineRevenue) for all non-cancelled rows.

    Population: Rows where is_cancelled == False
    Exclusions: Cancelled invoices
    """
    sales = df[~df["is_cancelled"]]
    return sales["LineRevenue"].sum()


def calculate_cancellation_value(df: pd.DataFrame) -> float:
    """
    Cancellation Value = SUM(ABS(LineRevenue)) for cancelled rows.

    Returns a positive number representing the total value of cancellations.
    """
    cancellations = df[df["is_cancelled"]]
    return cancellations["LineRevenue"].abs().sum()


def calculate_net_sales(df: pd.DataFrame) -> float:
    """
    Net Sales = Gross Sales - Cancellation Value.

    Equivalently: SUM(LineRevenue) across all rows, since cancellations
    have negative LineRevenue.
    """
    return df["LineRevenue"].sum()


# ---------------------------------------------------------------------------
# Order metrics
# ---------------------------------------------------------------------------

def calculate_order_count(df: pd.DataFrame) -> int:
    """
    Order Count = COUNT(DISTINCT Invoice) for non-cancelled invoices.
    """
    sales = df[~df["is_cancelled"]]
    return sales["Invoice"].nunique()


def calculate_aov(df: pd.DataFrame) -> float:
    """
    Average Order Value = Net Sales / Order Count.

    Uses non-cancelled invoices for order count.
    Net sales uses all rows (sales minus cancellations).
    """
    net = calculate_net_sales(df)
    orders = calculate_order_count(df)
    if orders == 0:
        return 0.0
    return net / orders


# ---------------------------------------------------------------------------
# Customer metrics
# ---------------------------------------------------------------------------

def calculate_unique_customers(df: pd.DataFrame) -> int:
    """
    Unique Purchasing Customers = COUNT(DISTINCT Customer ID)
    for non-cancelled rows with non-null Customer ID.
    """
    sales = df[(~df["is_cancelled"]) & (df["Customer ID"].notna())]
    return sales["Customer ID"].nunique()


def calculate_repeat_customer_rate(df: pd.DataFrame) -> float:
    """
    Repeat-Customer Rate = Customers with >= 2 distinct invoices /
                           Total unique customers.

    Population: Non-cancelled rows with non-null Customer ID.
    Returns: Float between 0 and 1 (proportion, not percentage).
    """
    sales = df[(~df["is_cancelled"]) & (df["Customer ID"].notna())]
    invoices_per_customer = sales.groupby("Customer ID")["Invoice"].nunique()

    total_customers = len(invoices_per_customer)
    repeat_customers = (invoices_per_customer >= 2).sum()

    if total_customers == 0:
        return 0.0
    return repeat_customers / total_customers


# ---------------------------------------------------------------------------
# Time-series metrics
# ---------------------------------------------------------------------------

def calculate_monthly_revenue(df: pd.DataFrame) -> pd.DataFrame:
    """
    Monthly revenue = SUM(LineRevenue) grouped by InvoiceMonth.

    Returns a DataFrame with columns: InvoiceMonth, Revenue
    Sorted by month.
    """
    monthly = (
        df.groupby("InvoiceMonth")["LineRevenue"]
        .sum()
        .reset_index()
        .rename(columns={"LineRevenue": "Revenue"})
        .sort_values("InvoiceMonth")
        .reset_index(drop=True)
    )
    return monthly


def calculate_mom_growth(monthly_revenue: pd.DataFrame) -> pd.DataFrame:
    """
    Month-over-Month Revenue Growth (%).

    Formula: (Current - Previous) / Previous * 100

    Takes the output of calculate_monthly_revenue() as input.
    First month will have NaN growth.
    """
    result = monthly_revenue.copy()
    result["PrevRevenue"] = result["Revenue"].shift(1)
    result["MoM_Growth_Pct"] = (
        (result["Revenue"] - result["PrevRevenue"]) / result["PrevRevenue"] * 100
    ).round(2)
    result = result.drop(columns=["PrevRevenue"])
    return result


# ---------------------------------------------------------------------------
# Summary function
# ---------------------------------------------------------------------------

def print_kpi_summary(df: pd.DataFrame) -> dict:
    """
    Calculate and print all key metrics. Returns a dict of results.
    """
    results = {
        "gross_sales": calculate_gross_sales(df),
        "cancellation_value": calculate_cancellation_value(df),
        "net_sales": calculate_net_sales(df),
        "order_count": calculate_order_count(df),
        "aov": calculate_aov(df),
        "unique_customers": calculate_unique_customers(df),
        "repeat_customer_rate": calculate_repeat_customer_rate(df),
    }

    print("=" * 55)
    print("KEY PERFORMANCE INDICATORS")
    print("=" * 55)
    print(f"  Gross Sales:           GBP {results['gross_sales']:>14,.2f}")
    print(f"  Cancellation Value:    GBP {results['cancellation_value']:>14,.2f}")
    print(f"  Net Sales:             GBP {results['net_sales']:>14,.2f}")
    print(f"  Order Count:               {results['order_count']:>14,}")
    print(f"  Average Order Value:   GBP {results['aov']:>14,.2f}")
    print(f"  Unique Customers:          {results['unique_customers']:>14,}")
    print(f"  Repeat-Customer Rate:      {results['repeat_customer_rate']:>13.1%}")
    print("=" * 55)

    return results
