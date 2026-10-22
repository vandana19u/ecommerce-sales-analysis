"""
data_cleaning.py
================
Functions to clean and validate the Online Retail II dataset.

Design decisions:
    - Keep all cleaning logic in testable functions (not in the notebook).
    - Each function does one thing and returns a new DataFrame (no in-place mutation).
    - The main clean_data() function calls them in order and logs every step.

Usage:
    from src.data_cleaning import clean_data
    df_clean = clean_data(df_raw)
"""

import pandas as pd
import numpy as np


# ---------------------------------------------------------------------------
# Individual cleaning steps
# ---------------------------------------------------------------------------

def add_cancellation_flag(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add a boolean column 'is_cancelled' based on Invoice prefix.

    Why: Cancelled orders have Invoice starting with 'C'. We flag them
    rather than immediately deleting, so we can analyse cancellation
    patterns separately.
    """
    df = df.copy()
    df["Invoice"] = df["Invoice"].astype(str)
    df["is_cancelled"] = df["Invoice"].str.startswith("C")
    return df


def remove_accounting_adjustments(df: pd.DataFrame) -> pd.DataFrame:
    """
    Remove non-transaction rows like 'Adjust bad debt'.

    Why: These 5 rows are accounting entries with enormous negative prices
    (up to -£53,594). They are not customer transactions and would badly
    distort revenue calculations.

    How we identify them: Invoice starts with 'A' (not a digit, not 'C').
    """
    mask = df["Invoice"].str.match(r"^[0-9C]")
    removed = df[~mask]
    if len(removed) > 0:
        print(f"  Removed {len(removed)} accounting adjustment rows:")
        print(f"    Descriptions: {removed['Description'].unique().tolist()}")
        print(f"    Price range: {removed['Price'].min():.2f} to {removed['Price'].max():.2f}")
    return df[mask].reset_index(drop=True)


def remove_zero_price_rows(df: pd.DataFrame) -> pd.DataFrame:
    """
    Remove rows where Price == 0.

    Why: Zero-price rows are typically internal adjustments, free samples,
    or data entry corrections. They contribute £0 to revenue but add noise
    to order counts and product statistics.

    Of the 6,202 zero-price rows, most have no Customer ID and descriptions
    like stock adjustments. We remove them entirely.
    """
    before = len(df)
    df_clean = df[df["Price"] != 0].reset_index(drop=True)
    removed = before - len(df_clean)
    print(f"  Removed {removed:,} zero-price rows")
    return df_clean


def remove_negative_price_non_cancellations(df: pd.DataFrame) -> pd.DataFrame:
    """
    Remove rows with negative price that are NOT cancellations.

    Why: After removing accounting adjustments (Invoice prefix 'A'),
    any remaining negative-price non-cancellation rows are data errors.
    Cancellations already have negative quantities; negative prices on
    non-cancellations don't make business sense.
    """
    mask = (df["Price"] < 0) & (~df["is_cancelled"])
    removed = mask.sum()
    if removed > 0:
        print(f"  Removed {removed} negative-price non-cancellation rows")
    return df[~mask].reset_index(drop=True)


def add_line_revenue(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add 'LineRevenue' = Quantity * Price.

    For normal sales: positive Quantity * positive Price = positive revenue.
    For cancellations: negative Quantity * positive Price = negative revenue.
    This lets us compute net sales by simply summing LineRevenue.
    """
    df = df.copy()
    df["LineRevenue"] = df["Quantity"] * df["Price"]
    return df


def add_time_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add useful time-based columns for grouping and analysis.

    Columns added:
        - InvoiceMonth: Year-Month string (e.g., '2010-01') for grouping
        - InvoiceYear:  Year as integer
        - InvoiceHour:  Hour of day (0-23) for time-of-day patterns
        - DayOfWeek:    Day name (Monday, Tuesday, etc.)
    """
    df = df.copy()
    df["InvoiceMonth"] = df["InvoiceDate"].dt.to_period("M").astype(str)
    df["InvoiceYear"] = df["InvoiceDate"].dt.year
    df["InvoiceHour"] = df["InvoiceDate"].dt.hour
    df["DayOfWeek"] = df["InvoiceDate"].dt.day_name()
    return df


def validate_cleaned_data(df: pd.DataFrame) -> None:
    """
    Run validation checks on the cleaned DataFrame.
    Raises AssertionError if any check fails.
    """
    # Required columns exist
    required = ["Invoice", "StockCode", "Quantity", "InvoiceDate",
                "Price", "Country", "is_cancelled", "LineRevenue"]
    for col in required:
        assert col in df.columns, f"Missing required column: {col}"

    # No zero prices
    assert (df["Price"] != 0).all(), "Zero-price rows still present"

    # Invoice should be string or object
    assert pd.api.types.is_string_dtype(df["Invoice"]) or df["Invoice"].dtype == object, \
        f"Invoice should be string-compatible, got {df['Invoice'].dtype}"

    # InvoiceDate should be datetime
    assert pd.api.types.is_datetime64_any_dtype(df["InvoiceDate"]), \
        "InvoiceDate should be datetime"

    # is_cancelled should be boolean
    assert df["is_cancelled"].dtype == bool, \
        f"is_cancelled should be bool, got {df['is_cancelled'].dtype}"

    print("  All validation checks passed")


# ---------------------------------------------------------------------------
# Main cleaning pipeline
# ---------------------------------------------------------------------------

def clean_data(df_raw: pd.DataFrame) -> pd.DataFrame:
    """
    Run the full cleaning pipeline on raw data.

    Steps:
        1. Add cancellation flag
        2. Remove accounting adjustments (Invoice prefix 'A')
        3. Remove zero-price rows
        4. Remove negative-price non-cancellation rows
        5. Add LineRevenue
        6. Add time features
        7. Validate

    Returns the cleaned DataFrame and prints a before/after summary.
    """
    print("\n" + "=" * 70)
    print("DATA CLEANING PIPELINE")
    print("=" * 70)

    # Record 'before' stats
    rows_before = len(df_raw)

    print(f"\n  Starting rows: {rows_before:,}")
    print()

    # Step 1: Flag cancellations
    print("Step 1: Adding cancellation flag ...")
    df = add_cancellation_flag(df_raw)

    # Step 2: Remove accounting adjustments
    print("Step 2: Removing accounting adjustments ...")
    df = remove_accounting_adjustments(df)

    # Step 3: Remove zero-price rows
    print("Step 3: Removing zero-price rows ...")
    df = remove_zero_price_rows(df)

    # Step 4: Remove negative-price non-cancellations
    print("Step 4: Removing negative-price non-cancellation rows ...")
    df = remove_negative_price_non_cancellations(df)

    # Step 5: Add LineRevenue
    print("Step 5: Adding LineRevenue column ...")
    df = add_line_revenue(df)

    # Step 6: Add time features
    print("Step 6: Adding time features ...")
    df = add_time_features(df)

    # Step 7: Validate
    print("Step 7: Validating cleaned data ...")
    validate_cleaned_data(df)

    # --------------- Before / After summary ---------------
    rows_after = len(df)
    rows_removed = rows_before - rows_after

    # Revenue comparison (using non-cancelled rows only)
    sales_rows = df[~df["is_cancelled"]]
    gross_sales = sales_rows["LineRevenue"].sum()

    cancel_rows = df[df["is_cancelled"]]
    cancellation_value = cancel_rows["LineRevenue"].sum()  # will be negative
    net_sales = df["LineRevenue"].sum()

    missing_cust = df["Customer ID"].isna().sum()
    missing_cust_pct = missing_cust / len(df) * 100

    print(f"\n{'=' * 70}")
    print("CLEANING SUMMARY")
    print(f"{'=' * 70}")
    print(f"  Rows before cleaning:     {rows_before:>12,}")
    print(f"  Rows removed:             {rows_removed:>12,} ({rows_removed/rows_before*100:.2f}%)")
    print(f"  Rows after cleaning:      {rows_after:>12,}")
    print(f"")
    print(f"  Non-cancelled rows:       {len(sales_rows):>12,}")
    print(f"  Cancellation rows:        {len(cancel_rows):>12,}")
    print(f"")
    print(f"  Gross Sales:           GBP {gross_sales:>14,.2f}")
    print(f"  Cancellation Value:    GBP {cancellation_value:>14,.2f}")
    print(f"  Net Sales:             GBP {net_sales:>14,.2f}")
    print(f"")
    print(f"  Unique invoices:          {df['Invoice'].nunique():>12,}")
    print(f"  Unique customers:         {df['Customer ID'].nunique():>12,}")
    print(f"  Missing Customer ID:      {missing_cust:>12,} ({missing_cust_pct:.1f}%)")
    print(f"  Countries:                {df['Country'].nunique():>12,}")
    print(f"{'=' * 70}\n")

    return df
