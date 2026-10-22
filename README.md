# E-commerce Sales and Customer Behaviour Analysis

A portfolio-grade data analytics project investigating revenue evolution, product velocity, regional demand, and customer purchasing behaviour across **1,061,163 real-world e-commerce transactions** totaling **£19.43M in net revenue**.

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![License: CC BY 4.0](https://img.shields.io/badge/License-CC_BY_4.0-lightgrey.svg)](https://creativecommons.org/licenses/by/4.0/)
[![Tests](https://img.shields.io/badge/Tests-Passing-brightgreen.svg)](tests/)
[![SQLite](https://img.shields.io/badge/Database-SQLite-003B57.svg)](sql/)

---

## 1. Project Overview & Business Problem

### Business Context
The dataset originates from a registered UK online retail business selling gifts and homewares to individual shoppers and wholesale accounts between **December 2009 and December 2011**. 

### Stakeholder & Objective
- **Target Audience:** Head of E-commerce, Inventory Operations Managers, and CRM Marketing Directors.
- **Goal:** Analyze transactional health, quantify the financial impact of cancellations, identify high-yield customer segments, and determine operational recommendations to accelerate growth and protect margins.

### Core Business Questions Answered
1. **Revenue Trajectory:** How does monthly net revenue evolve, and what seasonal patterns exist?
2. **Product Performance:** Which commercial stock codes generate the highest sales volume and financial return?
3. **Market Expansion:** Which international regions outside the UK yield the highest revenue and customer volume?
4. **Customer Retention:** What proportion of revenue stems from repeat customers vs. one-time purchasers?
5. **Customer Concentration:** What is the spending distribution among top-tier accounts?
6. **Cancellation Impact:** How significantly do product returns and order cancellations erode gross revenue?
7. **Customer Segmentation:** How do customer cohorts segment across Recency, Frequency, and Monetary (RFM) dimensions?

---

## 2. Dataset Specification & Data Integrity

- **Source:** [UCI Machine Learning Repository — Online Retail II](https://archive.ics.uci.edu/dataset/502/online+retail+ii) (DOI: [10.24432/C5CG6D](https://doi.org/10.24432/C5CG6D))
- **Author / Citation:** Chen, D. (2012). *Online Retail II*. UCI Machine Learning Repository.
- **License:** [Creative Commons Attribution 4.0 International (CC BY 4.0)](https://creativecommons.org/licenses/by/4.0/)
- **Period Covered:** 01/12/2009 – 09/12/2011 (738 calendar days, 25 months)
- **Unit of Observation:** Each record represents an individual line item on an invoice.

### Data Cleaning & Auditing Pipeline (`src/data_cleaning.py`)
| Audit Check | Raw Condition | Resolution & Rationale | Cleaned Impact |
|---|---|---|---|
| **Accounting Adjustments** | 6 rows with `Invoice` starting with `'A'` | Removed entries (e.g. *"Adjust bad debt"* with prices up to -£53,594) as they represent internal balance sheet adjustments, not commercial sales. | -6 rows |
| **Zero-Price Items** | 6,202 rows with `Price == 0.00` | Removed damaged goods entries, warehouse adjustments, and unbilled gift samples. | -6,202 rows |
| **Order Cancellations** | 19,494 rows with `Invoice` starting with `'C'` | Retained and flagged via `is_cancelled = True` with negative line revenue (`Quantity * Price`). Enables separate returns auditing. | 19,494 rows flagged |
| **Missing Customer IDs** | 243,007 rows (22.77%) missing `Customer ID` | Retained for macro revenue and product metrics; explicitly isolated from customer-level RFM and retention metrics. | 236,870 rows isolated |
| **Derived Features** | None | Added `LineRevenue`, `InvoiceMonth`, `InvoiceYear`, `InvoiceHour`, and `DayOfWeek`. | Enriched schema |

**Cleaning Summary:**
- **Raw Instances:** 1,067,371 rows
- **Cleaned Dataset:** 1,061,163 rows (-0.58% data removed)
- **Valid Sales Records:** 1,041,669 rows | **Cancellations:** 19,494 rows

---

## 3. Financial Metrics & Python-SQL Reconciliation

All metrics follow strict financial definitions and have been programmatically reconciled across **both Python (`src.metrics`) and SQLite (`sql/analysis_queries.sql`)** with zero discrepancy:

| Metric | Formal Definition | Population / Exclusions | Computed Value | Reconciled? |
|---|---|---|---|---|
| **Gross Sales** | $\sum (\text{Quantity} \times \text{Price})$ | Non-cancelled transactions (`is_cancelled = False`) | **£20,961,532.51** | Exact match |
| **Cancellation Loss** | $\sum |\text{Quantity} \times \text{Price}|$ | Cancelled invoices (`Invoice` prefix `'C'`) | **£1,527,415.00** | Exact match |
| **Net Sales** | $\text{Gross Sales} - \text{Cancellation Loss}$ | All commercial rows | **£19,434,864.65** | Exact match |
| **Cancellation Rate** | $\frac{\text{Cancellation Loss}}{\text{Gross Sales}} \times 100$ | Financial erosion percentage | **7.29%** | Exact match |
| **Valid Orders** | $\text{COUNT}(\text{DISTINCT } \text{Invoice})$ | Successful order transactions | **40,076** | Exact match |
| **Average Order Value (AOV)** | $\frac{\text{Net Sales}}{\text{Valid Orders}}$ | Average basket spend | **£484.95** | Exact match |
| **Unique Customers** | $\text{COUNT}(\text{DISTINCT } \text{CustomerID})$ | Accounts with non-null Customer ID | **5,878** | Exact match |
| **Repeat-Customer Rate** | $\frac{\text{Customers with } \ge 2 \text{ orders}}{\text{Unique Customers}}$ | Customer retention metric | **72.39%** | Exact match |

---

## 4. Key Analytical Findings & Evidence

### 1. The Repeat Customer Powerhouse
- **Finding:** Repeat customers represent **72.39% of all purchasing accounts (4,255 buyers)**, but generate an extraordinary **96.80% of customer-attributed revenue (£17,175,255.35)**.
- **Spend Multiplier:** Repeat buyers spend an average of **£4,036.49** over their customer lifetime, compared to just **£350.08** for one-time buyers (an **11.5x spend multiplier**).

![Repeat vs One-Time Customers](reports/figures/04_repeat_vs_onetime_revenue.png)

### 2. High Seasonality & Q4 Concentration
- **Finding:** Monthly net revenue spikes aggressively in Q4 each year. Revenue jumps from **£591.9k in August 2010** to a peak of **£1,437.4k in November 2010 (+142.8%)**, and reaches **£1,461.8k in November 2011**.
- **Post-Holiday Drop:** January sales contract by **-56.3% MoM**, reflecting a classic B2B and retail post-holiday inventory absorption period.

![Monthly Revenue and Growth](reports/figures/01_monthly_revenue_and_growth.png)

### 3. Customer Segmentation (RFM Analysis)
Using quintile scoring ($1\text{--}5$) on Recency (relative to December 10, 2011), Frequency, and Monetary spend:
- **Champions (1,483 accounts, 25.2%):** Generate **£12,296,897.92 (69.3% of total customer revenue)** with an average order frequency of 15.7 purchases and recency of 20.2 days.
- **At Risk / High Value (824 accounts, 14.0%):** Historically purchased ~5 times with average spend of £1,982.98, but have not made a purchase in an average of **369 days**.
- **Hibernating / Lost (1,523 accounts, 25.9%):** Made an average of 1.25 orders before lapsing over 450 days ago.

![RFM Customer Segments](reports/figures/07_rfm_customer_segments.png)

### 4. International Expansion Outside the UK
- While the UK accounts for **85.9% of total revenue**, four European markets represent substantial B2B wholesale demand:
  1. **EIRE (Ireland):** £615,519.58 (33.0% of non-UK sales)
  2. **Netherlands:** £548,524.47 (29.4% of non-UK sales)
  3. **Germany:** £417,988.62 (22.4% of non-UK sales)
  4. **France:** £328,172.10 (17.6% of non-UK sales)

---

## 5. Repository Structure

```
ecommerce-sales-analysis/
├── README.md                          # Executive summary, findings, and technical guide
├── requirements.txt                   # Tested Python dependencies
├── .gitignore                         # Data and cache exclusion rules
├── download_data.py                   # Automated UCI dataset downloader
├── data/
│   ├── raw/                           # Raw Excel dataset (excluded from git)
│   └── processed/
│       ├── online_retail_cleaned.csv  # Cleaned dataset (1,061,163 rows)
│       └── ecommerce.db               # Indexed relational SQLite database
├── notebooks/
│   ├── 01_load_and_inspect.py         # Initial inspection script
│   └── 01_ecommerce_analysis.ipynb    # End-to-end reproducible Jupyter Notebook
├── src/
│   ├── __init__.py
│   ├── data_cleaning.py               # Modular cleaning pipeline and schema validators
│   ├── metrics.py                     # Mathematical implementations of core KPIs
│   ├── process_and_load_db.py         # ETL runner from raw Excel to SQLite database
│   ├── run_sql_and_reconcile.py       # SQL query runner & metric reconciliation
│   └── eda_and_charts.py              # Visualizations generator (7 publication figures)
├── sql/
│   └── analysis_queries.sql           # 9 advanced SQL queries (CTEs, Window Functions)
├── reports/
│   ├── figures/                       # 7 publication-ready chart figures (PNG, 300 DPI)
│   └── executive_summary.md           # Business stakeholder briefing
└── tests/
    └── test_metrics.py                # Unit test suite with synthetic fixtures
```

---

## 6. Setup and Execution Instructions

### Prerequisites
- Python 3.10+
- Git

### 1. Clone & Install
```bash
git clone https://github.com/your-username/ecommerce-sales-analysis.git
cd ecommerce-sales-analysis
python -m venv venv
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

pip install -r requirements.txt
```

### 2. Download Data & Run ETL Pipeline
```bash
# 1. Download raw dataset from UCI Repository
python download_data.py

# 2. Run data cleaning and build SQLite database
python src/process_and_load_db.py

# 3. Run unit tests
python -m unittest tests/test_metrics.py

# 4. Execute SQL queries and verify reconciliation
python src/run_sql_and_reconcile.py

# 5. Generate all 7 analytical figures
python src/eda_and_charts.py
```

### 3. Open the Interactive Notebook
```bash
jupyter notebook notebooks/01_ecommerce_analysis.ipynb
```

---

## 7. Sample SQL Analytics (`sql/analysis_queries.sql`)

### Query: Repeat Customer Revenue Contribution (CTE + Conditional Aggregation)
```sql
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
```

---

## 8. Strategic Business Recommendations

1. **Protect and Incentivize the 1,483 "Champions":**
   - *Evidence:* This cohort generates **£12.30M (69.3% of revenue)**.
   - *Action:* Introduce dedicated account representatives and volume-based pricing tiers to mitigate customer churn risk.

2. **Reactivate the 824 "At Risk" Wholesalers:**
   - *Evidence:* These accounts previously spent **£1.63M (avg ~5 orders)** but haven't placed an order in over 12 months.
   - *Action:* Deploy a quarterly re-engagement campaign offering early-access holiday catalogs or introductory seasonal re-order terms.

3. **Align Warehouse Capacity with Q4 Surge:**
   - *Evidence:* Order demand surges over **+140% between August and November**, while cancellations remain stable (~7.3%).
   - *Action:* Staffing and freight carrier reservations must be locked in by early Q3.

---

## 9. Assumptions & Limitations

- **Lack of Cost Data (COGS):** Operating margins, marketing CAC, and net profitability cannot be evaluated; all figures represent observed top-line revenue.
- **Guest Checkout / Missing Customer Identifiers:** 22.3% of rows lack a `Customer ID`. While fully accounted for in transaction, product, and regional metrics, these are excluded from customer-level RFM segmentations.
- **Wholesale Skew:** Transaction patterns reflect wholesale buying (e.g. bulk purchases of decorative bags), meaning B2C e-commerce benchmarks (such as low AOV) do not apply directly.

---

## 10. Interview Talking Points & CV Bullet Points

### Truthful CV Bullet Points:
- *Analyzed 1.06M+ e-commerce transactions using Python, pandas, and SQLite, uncovering that 72.4% repeat customers drive 96.8% of £19.4M net revenue.*
- *Architected an automated ETL pipeline and RFM customer segmentation engine, identifying £1.63M in dormant revenue across 824 at-risk wholesale accounts.*

### Top Interview Questions & Preparation:
1. **"How did you handle cancellations and negative quantities?"**  
   *Answer:* Rather than blindly dropping negative rows, I parsed invoice prefixes to flag `'C'` transactions as commercial cancellations, while filtering out non-commercial accounting adjustments (`'A'` prefix bad-debt write-offs up to -£53.5k). This enabled accurate gross (£20.96M), cancellation (£1.53M), and net sales (£19.43M) auditing.
2. **"Why did you avoid calling total customer spending 'Customer Lifetime Value'?"**  
   *Answer:* CLV requires a predictive model incorporating future retention probabilities, gross margins, and discount rates. Calling historical spend CLV is misleading; I reported it truthfully as *historical observed customer spend*.
3. **"How did you ensure consistency between Python and SQL?"**  
   *Answer:* I wrote automated reconciliation checks in `tests/reconcile_sql_python.py` comparing Python aggregations with SQLite window functions and CTEs, proving exact matches on revenue, order counts, and monthly trends down to the penny.
