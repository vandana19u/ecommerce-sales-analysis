"""
Step 1: Load and Inspect the Dataset
=====================================
This script loads the raw Online Retail II dataset and performs the initial
inspection — the first thing any data analyst does with new data.

What we'll check:
    1. Shape (rows, columns)
    2. Column names and data types
    3. First and last few rows
    4. Missing values per column
    5. Basic statistics for numeric columns
    6. Date range
    7. Unique value counts for key columns
    8. Sample of cancellation rows (Invoice starts with "C")

Run from the project root:
    python notebooks/01_load_and_inspect.py
"""

import os
import sys
import pandas as pd

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
# Use relative paths so this works on any machine
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DATA_PATH = os.path.join(PROJECT_ROOT, "data", "raw", "online_retail_II.xlsx")

# ---------------------------------------------------------------------------
# 1. Load the data
# ---------------------------------------------------------------------------
print("=" * 70)
print("STEP 1: LOADING THE DATASET")
print("=" * 70)

if not os.path.exists(RAW_DATA_PATH):
    print(f"\n✗ File not found: {RAW_DATA_PATH}")
    print("  Run 'python download_data.py' first.")
    sys.exit(1)

print(f"\nReading {RAW_DATA_PATH} ...")
print("(This may take 30-60 seconds — it's a large Excel file)\n")

# The xlsx has two sheets: 'Year 2009-2010' and 'Year 2010-2011'
# We read both and combine them into one DataFrame.
df_sheet1 = pd.read_excel(RAW_DATA_PATH, sheet_name="Year 2009-2010")
df_sheet2 = pd.read_excel(RAW_DATA_PATH, sheet_name="Year 2010-2011")

print(f"Sheet 'Year 2009-2010': {df_sheet1.shape[0]:,} rows, {df_sheet1.shape[1]} columns")
print(f"Sheet 'Year 2010-2011': {df_sheet2.shape[0]:,} rows, {df_sheet2.shape[1]} columns")

# Combine both sheets
df = pd.concat([df_sheet1, df_sheet2], ignore_index=True)
print(f"\nCombined dataset:       {df.shape[0]:,} rows, {df.shape[1]} columns")

# ---------------------------------------------------------------------------
# 2. Column names and data types
# ---------------------------------------------------------------------------
print("\n" + "=" * 70)
print("STEP 2: COLUMNS AND DATA TYPES")
print("=" * 70)
print()
print(df.dtypes.to_string())

# ---------------------------------------------------------------------------
# 3. First and last rows
# ---------------------------------------------------------------------------
print("\n" + "=" * 70)
print("STEP 3: FIRST 5 ROWS")
print("=" * 70)
print()
print(df.head().to_string())

print("\n" + "=" * 70)
print("LAST 5 ROWS")
print("=" * 70)
print()
print(df.tail().to_string())

# ---------------------------------------------------------------------------
# 4. Missing values
# ---------------------------------------------------------------------------
print("\n" + "=" * 70)
print("STEP 4: MISSING VALUES")
print("=" * 70)
print()

missing = df.isnull().sum()
missing_pct = (df.isnull().sum() / len(df) * 100).round(2)
missing_df = pd.DataFrame({
    "Missing Count": missing,
    "Missing %": missing_pct
})
print(missing_df.to_string())
print(f"\nTotal rows: {len(df):,}")

# ---------------------------------------------------------------------------
# 5. Basic statistics for numeric columns
# ---------------------------------------------------------------------------
print("\n" + "=" * 70)
print("STEP 5: NUMERIC SUMMARY STATISTICS")
print("=" * 70)
print()
print(df.describe().round(2).to_string())

# ---------------------------------------------------------------------------
# 6. Date range
# ---------------------------------------------------------------------------
print("\n" + "=" * 70)
print("STEP 6: DATE RANGE")
print("=" * 70)
print()
print(f"Earliest transaction: {df['InvoiceDate'].min()}")
print(f"Latest transaction:   {df['InvoiceDate'].max()}")
print(f"Date span:            {(df['InvoiceDate'].max() - df['InvoiceDate'].min()).days} days")

# ---------------------------------------------------------------------------
# 7. Unique values for key columns
# ---------------------------------------------------------------------------
print("\n" + "=" * 70)
print("STEP 7: UNIQUE VALUE COUNTS")
print("=" * 70)
print()
key_cols = ["Invoice", "StockCode", "Description", "Customer ID", "Country"]
for col in key_cols:
    if col in df.columns:
        print(f"{col:15s}: {df[col].nunique():>10,} unique values")

# ---------------------------------------------------------------------------
# 8. Cancellation overview
# ---------------------------------------------------------------------------
print("\n" + "=" * 70)
print("STEP 8: CANCELLATIONS (Invoice starts with 'C')")
print("=" * 70)
print()

# Convert Invoice to string to safely check prefix
df["Invoice"] = df["Invoice"].astype(str)
cancellations = df[df["Invoice"].str.startswith("C")]
non_cancellations = df[~df["Invoice"].str.startswith("C")]

print(f"Total rows:               {len(df):>10,}")
print(f"Non-cancellation rows:    {len(non_cancellations):>10,}  ({len(non_cancellations)/len(df)*100:.1f}%)")
print(f"Cancellation rows:        {len(cancellations):>10,}  ({len(cancellations)/len(df)*100:.1f}%)")
print(f"\nCancelled invoices:       {cancellations['Invoice'].nunique():>10,}")
print(f"Non-cancelled invoices:   {non_cancellations['Invoice'].nunique():>10,}")

print("\n--- Sample cancellation rows ---")
print(cancellations.head(5).to_string())

# ---------------------------------------------------------------------------
# 9. Quantity and Price edge cases
# ---------------------------------------------------------------------------
print("\n" + "=" * 70)
print("STEP 9: EDGE CASES — QUANTITY AND PRICE")
print("=" * 70)
print()

neg_qty = df[df["Quantity"] < 0]
zero_price = df[df["Price"] == 0]
neg_price = df[df["Price"] < 0]

print(f"Rows with negative Quantity: {len(neg_qty):>10,}")
print(f"Rows with zero Price:        {len(zero_price):>10,}")
print(f"Rows with negative Price:    {len(neg_price):>10,}")

if len(neg_price) > 0:
    print("\n--- Sample rows with negative price ---")
    print(neg_price.head(5).to_string())

if len(zero_price) > 0:
    print("\n--- Sample rows with zero price ---")
    print(zero_price.head(5).to_string())

# ---------------------------------------------------------------------------
# 10. Country distribution (top 10)
# ---------------------------------------------------------------------------
print("\n" + "=" * 70)
print("STEP 10: TOP 10 COUNTRIES BY ROW COUNT")
print("=" * 70)
print()
country_counts = df["Country"].value_counts().head(10)
for country, count in country_counts.items():
    print(f"  {country:30s} {count:>10,} rows  ({count/len(df)*100:.1f}%)")

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
print("\n" + "=" * 70)
print("INSPECTION COMPLETE")
print("=" * 70)
print("""
Key observations to review:
  1. Check the column data types — are dates parsed correctly?
  2. How many rows have missing Customer ID?
  3. What's the range of Quantity and Price?
  4. How many cancellations are there?
  5. Are there zero or negative prices to investigate?
  6. Which countries dominate the data?

Next step: Data cleaning (Step 2)
""")
