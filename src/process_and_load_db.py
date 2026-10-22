"""
process_and_load_db.py
----------------------
End-to-end data processing and SQLite database loader.

Performs:
1. Load raw data from data/raw/online_retail_II.xlsx (both sheets)
2. Run src.data_cleaning.clean_data()
3. Save cleaned dataset to data/processed/online_retail_cleaned.csv
4. Create and populate SQLite database at data/processed/ecommerce.db
   with structured tables:
     - transactions (all cleaned line items)
     - products (unique StockCode and latest Description for JOIN queries)
     - customers (unique Customer_ID and primary Country for JOIN queries)
   along with appropriate indexes for high performance.
"""

import os
import sys
import sqlite3

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import pandas as pd
from src.data_cleaning import clean_data
RAW_PATH = os.path.join(PROJECT_ROOT, "data", "raw", "online_retail_II.xlsx")
PROCESSED_DIR = os.path.join(PROJECT_ROOT, "data", "processed")
CLEAN_CSV_PATH = os.path.join(PROCESSED_DIR, "online_retail_cleaned.csv")
DB_PATH = os.path.join(PROCESSED_DIR, "ecommerce.db")


def main():
    os.makedirs(PROCESSED_DIR, exist_ok=True)

    print("=" * 70)
    print("STEP 1: LOADING RAW EXCEL DATASET")
    print("=" * 70)
    if not os.path.exists(RAW_PATH):
        print(f"Error: Raw file not found at {RAW_PATH}")
        sys.exit(1)

    print(f"Reading {RAW_PATH} (both sheets)...")
    df_s1 = pd.read_excel(RAW_PATH, sheet_name="Year 2009-2010")
    df_s2 = pd.read_excel(RAW_PATH, sheet_name="Year 2010-2011")
    df_raw = pd.concat([df_s1, df_s2], ignore_index=True)
    print(f"Loaded raw dataset with {len(df_raw):,} rows.")

    print("\n" + "=" * 70)
    print("STEP 2: RUNNING CLEANING PIPELINE")
    print("=" * 70)
    df_clean = clean_data(df_raw)

    print("\n" + "=" * 70)
    print("STEP 3: SAVING CLEANED CSV")
    print("=" * 70)
    print(f"Writing to {CLEAN_CSV_PATH} ...")
    df_clean.to_csv(CLEAN_CSV_PATH, index=False)
    csv_size_mb = os.path.getsize(CLEAN_CSV_PATH) / (1024 * 1024)
    print(f"Saved {CLEAN_CSV_PATH} ({csv_size_mb:.1f} MB)")

    print("\n" + "=" * 70)
    print("STEP 4: POPULATING SQLITE DATABASE")
    print("=" * 70)
    print(f"Connecting to {DB_PATH} ...")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Rename 'Customer ID' to 'CustomerID' for cleaner SQL syntax
    db_df = df_clean.copy()
    db_df.rename(columns={"Customer ID": "CustomerID"}, inplace=True)
    # Convert is_cancelled boolean to integer (1 / 0) for SQLite compatibility
    db_df["is_cancelled"] = db_df["is_cancelled"].astype(int)
    # Store InvoiceDate as ISO8601 string for SQLite date functions
    db_df["InvoiceDate"] = db_df["InvoiceDate"].dt.strftime("%Y-%m-%d %H:%M:%S")

    # Table 1: transactions
    print("Creating 'transactions' table...")
    cursor.execute("DROP TABLE IF EXISTS transactions;")
    db_df.to_sql("transactions", conn, if_exists="replace", index=False)

    # Table 2: products (StockCode -> clean representative description)
    print("Creating 'products' table for relational joins...")
    cursor.execute("DROP TABLE IF EXISTS products;")
    cursor.execute("""
        CREATE TABLE products AS
        SELECT 
            StockCode,
            MAX(Description) AS Description,
            COUNT(*) AS TotalTransactions,
            ROUND(AVG(Price), 2) AS AvgUnitPrice
        FROM transactions
        WHERE Description IS NOT NULL AND TRIM(Description) != ''
        GROUP BY StockCode;
    """)

    # Table 3: customers (CustomerID -> primary Country, first & last purchase)
    print("Creating 'customers' table for relational joins...")
    cursor.execute("DROP TABLE IF EXISTS customers;")
    cursor.execute("""
        CREATE TABLE customers AS
        SELECT 
            CustomerID,
            MAX(Country) AS Country,
            MIN(InvoiceDate) AS FirstPurchaseDate,
            MAX(InvoiceDate) AS LastPurchaseDate,
            COUNT(DISTINCT Invoice) AS TotalInvoices,
            ROUND(SUM(LineRevenue), 2) AS LifetimeSpend
        FROM transactions
        WHERE CustomerID IS NOT NULL AND is_cancelled = 0
        GROUP BY CustomerID;
    """)

    # Create indexes for fast querying
    print("Building indexes...")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_trans_invoice ON transactions(Invoice);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_trans_cust ON transactions(CustomerID);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_trans_date ON transactions(InvoiceDate);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_trans_month ON transactions(InvoiceMonth);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_trans_stock ON transactions(StockCode);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_products_stock ON products(StockCode);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_customers_cust ON customers(CustomerID);")

    conn.commit()

    # Verify row counts in SQLite
    cursor.execute("SELECT COUNT(*) FROM transactions;")
    t_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM products;")
    p_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM customers;")
    c_count = cursor.fetchone()[0]

    conn.close()

    db_size_mb = os.path.getsize(DB_PATH) / (1024 * 1024)
    print(f"\nDatabase populated successfully:")
    print(f"  - transactions table: {t_count:,} rows")
    print(f"  - products table:     {p_count:,} rows")
    print(f"  - customers table:    {c_count:,} rows")
    print(f"  - DB file size:       {db_size_mb:.1f} MB")
    print("=" * 70)


if __name__ == "__main__":
    main()
