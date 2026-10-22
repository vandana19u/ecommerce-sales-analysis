"""
tests/test_metrics.py
---------------------
Unit tests for data cleaning logic and business metric calculations.

Uses a clear, synthetic test fixture with known values to verify:
1. Cancellation flagging and accounting adjustments removal
2. Net sales, gross sales, and cancellation value calculations
3. Order count and Average Order Value (AOV)
4. Unique customers and repeat-customer rate
5. Month-over-Month (MoM) revenue growth
"""

import unittest
import pandas as pd
import numpy as np

from src.data_cleaning import (
    add_cancellation_flag,
    remove_accounting_adjustments,
    remove_zero_price_rows,
    remove_negative_price_non_cancellations,
    add_line_revenue,
    add_time_features,
    validate_cleaned_data,
    clean_data,
)
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


class TestDataCleaningAndMetrics(unittest.TestCase):
    def setUp(self):
        """
        Create a small, deterministic synthetic dataset fixture.
        Notice: All transactions and IDs are synthetic examples created for testing.

        Dataset layout:
        - Invoice 1001: Cust 101, Product A (Qty 2 @ 10.00 = 20.00) + Product B (Qty 1 @ 5.00 = 5.00) -> Inv Total = 25.00
        - Invoice 1002: Cust 101, Product A (Qty 3 @ 10.00 = 30.00) -> Inv Total = 30.00 (Cust 101 has 2 orders -> repeat)
        - Invoice 1003: Cust 102, Product C (Qty 1 @ 50.00 = 50.00) -> Inv Total = 50.00 (Cust 102 has 1 order -> one-time)
        - Invoice 1004: Missing Cust, Product B (Qty 2 @ 5.00 = 10.00) -> Non-null sales, but null customer ID
        - Invoice C1005: Cust 102, Product C cancellation (Qty -1 @ 50.00 = -50.00)
        - Invoice A9999: Accounting bad debt entry (Qty 1 @ -500.00) -> Must be removed
        - Invoice 1006: Zero price row (Qty 5 @ 0.00 = 0.00) -> Must be removed
        """
        self.raw_fixture = pd.DataFrame({
            "Invoice": ["1001", "1001", "1002", "1003", "1004", "C1005", "A9999", "1006"],
            "StockCode": ["PROD_A", "PROD_B", "PROD_A", "PROD_C", "PROD_B", "PROD_C", "B", "PROD_D"],
            "Description": [
                "Item A", "Item B", "Item A", "Item C", "Item B",
                "Item C Return", "Adjust bad debt", "Free sample"
            ],
            "Quantity": [2, 1, 3, 1, 2, -1, 1, 5],
            "InvoiceDate": pd.to_datetime([
                "2010-01-10 10:00:00",
                "2010-01-10 10:00:00",
                "2010-01-20 14:30:00",
                "2010-01-25 11:15:00",
                "2010-02-05 09:00:00",
                "2010-02-10 16:45:00",
                "2010-02-15 12:00:00",
                "2010-02-18 13:00:00",
            ]),
            "Price": [10.00, 5.00, 10.00, 50.00, 5.00, 50.00, -500.00, 0.00],
            "Customer ID": [101.0, 101.0, 101.0, 102.0, np.nan, 102.0, np.nan, 103.0],
            "Country": ["United Kingdom"] * 8
        })

    def test_cleaning_pipeline(self):
        """Verify cleaning stages remove accounting adjustments and zero prices."""
        df_clean = clean_data(self.raw_fixture)

        # A9999 (accounting) and 1006 (zero price) should be dropped
        self.assertEqual(len(df_clean), 6)
        self.assertNotIn("A9999", df_clean["Invoice"].values)
        self.assertNotIn("1006", df_clean["Invoice"].values)

        # Cancellation flag check
        c_rows = df_clean[df_clean["is_cancelled"]]
        self.assertEqual(len(c_rows), 1)
        self.assertEqual(c_rows.iloc[0]["Invoice"], "C1005")

        # LineRevenue calculation check
        expected_rev = [20.0, 5.0, 30.0, 50.0, 10.0, -50.0]
        np.testing.assert_allclose(df_clean["LineRevenue"].values, expected_rev)

    def test_revenue_and_order_metrics(self):
        """Verify gross sales, cancellation value, net sales, and AOV."""
        df_clean = clean_data(self.raw_fixture)

        # Non-cancelled sales rows: 20 + 5 + 30 + 50 + 10 = 115.00
        gross = calculate_gross_sales(df_clean)
        self.assertAlmostEqual(gross, 115.00)

        # Cancellations: |-50.00| = 50.00
        cancel_val = calculate_cancellation_value(df_clean)
        self.assertAlmostEqual(cancel_val, 50.00)

        # Net sales: 115.00 - 50.00 = 65.00
        net = calculate_net_sales(df_clean)
        self.assertAlmostEqual(net, 65.00)

        # Distinct non-cancelled invoices: '1001', '1002', '1003', '1004' -> 4 orders
        order_cnt = calculate_order_count(df_clean)
        self.assertEqual(order_cnt, 4)

        # AOV = Net sales / Order count = 65.00 / 4 = 16.25
        aov = calculate_aov(df_clean)
        self.assertAlmostEqual(aov, 16.25)

    def test_customer_metrics(self):
        """Verify unique customer count and repeat customer rate."""
        df_clean = clean_data(self.raw_fixture)

        # Non-cancelled with valid Customer ID: Cust 101 (inv 1001, 1002) and Cust 102 (inv 1003)
        # Unique customers = 2
        unique_cust = calculate_unique_customers(df_clean)
        self.assertEqual(unique_cust, 2)

        # Repeat customer: Cust 101 has 2 invoices, Cust 102 has 1 invoice
        # Repeat rate = 1 / 2 = 0.5 (50%)
        repeat_rate = calculate_repeat_customer_rate(df_clean)
        self.assertAlmostEqual(repeat_rate, 0.5)

    def test_mom_revenue_growth(self):
        """Verify monthly aggregation and month-over-month growth."""
        df_clean = clean_data(self.raw_fixture)
        monthly = calculate_monthly_revenue(df_clean)

        # Month 2010-01: 20 + 5 + 30 + 50 = 105.00
        # Month 2010-02: 10 + (-50) = -40.00
        self.assertEqual(len(monthly), 2)
        self.assertAlmostEqual(monthly.loc[monthly["InvoiceMonth"] == "2010-01", "Revenue"].values[0], 105.00)
        self.assertAlmostEqual(monthly.loc[monthly["InvoiceMonth"] == "2010-02", "Revenue"].values[0], -40.00)

        # Growth: (-40 - 105) / 105 * 100 = -138.10%
        mom = calculate_mom_growth(monthly)
        self.assertTrue(pd.isna(mom.iloc[0]["MoM_Growth_Pct"]))
        self.assertAlmostEqual(mom.iloc[1]["MoM_Growth_Pct"], -138.10, places=2)


if __name__ == "__main__":
    unittest.main()
