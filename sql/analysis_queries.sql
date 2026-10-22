-- ============================================================================
-- E-commerce Sales and Customer Behaviour Analysis
-- SQLite Analytical Queries
-- ============================================================================
-- Database: data/processed/ecommerce.db
-- Tables:
--   1. transactions (Invoice, StockCode, Description, Quantity, InvoiceDate,
--                    Price, CustomerID, Country, is_cancelled, LineRevenue,
--                    InvoiceMonth, InvoiceYear, InvoiceHour, DayOfWeek)
--   2. products     (StockCode, Description, TotalTransactions, AvgUnitPrice)
--   3. customers    (CustomerID, Country, FirstPurchaseDate, LastPurchaseDate,
--                    TotalInvoices, LifetimeSpend)
-- ============================================================================


-- ----------------------------------------------------------------------------
-- QUERY 1: KPI Summary — Gross Sales, Cancellation Value, and Net Sales
-- Concept: Aggregation & Conditional Logic (CASE WHEN / FILTER)
-- Business Question: What are the total sales figures and cancellation impact?
-- ----------------------------------------------------------------------------
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


-- ----------------------------------------------------------------------------
-- QUERY 2: Monthly Revenue and Month-over-Month (MoM) Growth
-- Concept: CTE (Common Table Expression) + Window Function (LAG)
-- Business Question 1: How does revenue change over time?
-- ----------------------------------------------------------------------------
WITH MonthlyRevenue AS (
    SELECT 
        InvoiceMonth,
        COUNT(DISTINCT CASE WHEN is_cancelled = 0 THEN Invoice END) AS OrdersCount,
        COUNT(DISTINCT CustomerID) AS ActiveCustomers,
        ROUND(SUM(LineRevenue), 2) AS MonthlyNetRevenue
    FROM transactions
    GROUP BY InvoiceMonth
)
SELECT 
    InvoiceMonth,
    OrdersCount,
    ActiveCustomers,
    MonthlyNetRevenue,
    LAG(MonthlyNetRevenue, 1) OVER (ORDER BY InvoiceMonth) AS PrevMonthRevenue,
    ROUND(
        (MonthlyNetRevenue - LAG(MonthlyNetRevenue, 1) OVER (ORDER BY InvoiceMonth)) 
        / LAG(MonthlyNetRevenue, 1) OVER (ORDER BY InvoiceMonth) * 100.0, 
        2
    ) AS MoM_Growth_Pct
FROM MonthlyRevenue
ORDER BY InvoiceMonth;


-- ----------------------------------------------------------------------------
-- QUERY 3: Top 10 Products by Total Net Revenue (With Product Table Join)
-- Concept: Relational INNER JOIN + Aggregation + Ranking
-- Business Question 2: Which products generate the most revenue?
-- ----------------------------------------------------------------------------
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
LIMIT 10;


-- ----------------------------------------------------------------------------
-- QUERY 4: International Sales Breakdown (Excluding UK)
-- Concept: Filtering, Aggregation, and Share of International Sales
-- Business Question 3: Which countries contribute most to non-UK revenue?
-- ----------------------------------------------------------------------------
WITH CountryTotals AS (
    SELECT 
        Country,
        COUNT(DISTINCT CustomerID) AS CustomerCount,
        COUNT(DISTINCT Invoice) AS OrderCount,
        ROUND(SUM(LineRevenue), 2) AS CountryNetRevenue
    FROM transactions
    WHERE Country != 'United Kingdom' AND is_cancelled = 0
    GROUP BY Country
)
SELECT 
    Country,
    CustomerCount,
    OrderCount,
    CountryNetRevenue,
    ROUND(CountryNetRevenue * 100.0 / SUM(CountryNetRevenue) OVER (), 2) AS PctOfInternationalRevenue
FROM CountryTotals
ORDER BY CountryNetRevenue DESC
LIMIT 10;


-- ----------------------------------------------------------------------------
-- QUERY 5: Repeat vs. One-Time Customer Revenue Contribution
-- Concept: CTE + Subquery + Conditional Aggregation
-- Business Question 4: How much revenue comes from repeat customers?
-- ----------------------------------------------------------------------------
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


-- ----------------------------------------------------------------------------
-- QUERY 6: Top 10 Customers with Cumulative Spend and Percentile
-- Concept: Window Functions (DENSE_RANK, SUM OVER, CUME_DIST)
-- Business Question 5: Which customers have the highest observed purchase value?
-- ----------------------------------------------------------------------------
WITH RankedCustomers AS (
    SELECT 
        c.CustomerID,
        c.Country,
        c.TotalInvoices,
        c.LifetimeSpend,
        DENSE_RANK() OVER (ORDER BY c.LifetimeSpend DESC) AS SpendRank,
        ROUND(SUM(c.LifetimeSpend) OVER (ORDER BY c.LifetimeSpend DESC), 2) AS CumulativeSpend_GBP,
        ROUND(CUME_DIST() OVER (ORDER BY c.LifetimeSpend), 4) AS SpendPercentile
    FROM customers c
)
SELECT 
    SpendRank,
    CustomerID,
    Country,
    TotalInvoices,
    LifetimeSpend AS TotalSpend_GBP,
    CumulativeSpend_GBP,
    ROUND(SpendPercentile * 100.0, 2) AS TopPercentile
FROM RankedCustomers
WHERE SpendRank <= 10;


-- ----------------------------------------------------------------------------
-- QUERY 7: Cancellation Rate by Month and Financial Impact
-- Concept: CTE + Aggregation + Ratio Calculation
-- Business Question 6: How do cancellations affect gross sales over time?
-- ----------------------------------------------------------------------------
SELECT 
    InvoiceMonth,
    COUNT(DISTINCT CASE WHEN is_cancelled = 0 THEN Invoice END) AS SuccessfulOrders,
    COUNT(DISTINCT CASE WHEN is_cancelled = 1 THEN Invoice END) AS CancelledOrders,
    ROUND(
        COUNT(DISTINCT CASE WHEN is_cancelled = 1 THEN Invoice END) * 100.0 
        / COUNT(DISTINCT Invoice), 
        2
    ) AS CancellationOrderRate_Pct,
    ROUND(SUM(CASE WHEN is_cancelled = 0 THEN LineRevenue ELSE 0 END), 2) AS GrossSales_GBP,
    ROUND(SUM(CASE WHEN is_cancelled = 1 THEN ABS(LineRevenue) ELSE 0 END), 2) AS CancellationLoss_GBP,
    ROUND(
        SUM(CASE WHEN is_cancelled = 1 THEN ABS(LineRevenue) ELSE 0 END) * 100.0 
        / SUM(CASE WHEN is_cancelled = 0 THEN LineRevenue ELSE 0 END), 
        2
    ) AS LossToGrossRate_Pct
FROM transactions
GROUP BY InvoiceMonth
ORDER BY InvoiceMonth;


-- ----------------------------------------------------------------------------
-- QUERY 8: Purchasing Patterns by Day of Week and Hour of Day
-- Concept: Multi-column Grouping & Aggregation
-- Business Question: When do customers place orders most frequently?
-- ----------------------------------------------------------------------------
SELECT 
    DayOfWeek,
    InvoiceHour,
    COUNT(DISTINCT Invoice) AS TotalOrders,
    ROUND(SUM(LineRevenue), 2) AS TotalRevenue_GBP,
    ROUND(AVG(LineRevenue), 2) AS AvgLineItemValue_GBP
FROM transactions
WHERE is_cancelled = 0
GROUP BY DayOfWeek, InvoiceHour
ORDER BY TotalOrders DESC
LIMIT 15;


-- ----------------------------------------------------------------------------
-- QUERY 9: RFM Customer Metrics Raw Extraction
-- Concept: Date Math + Window Functions + Subquery
-- Business Question 7: Customer Recency, Frequency, and Monetary scores
-- Note: Reference date set to 2011-12-10 (day after last transaction in dataset)
-- ----------------------------------------------------------------------------
WITH CustomerRFM AS (
    SELECT 
        CustomerID,
        -- Days since last order relative to dataset reference date (2011-12-10)
        ROUND(JULIANDAY('2011-12-10') - JULIANDAY(MAX(InvoiceDate))) AS RecencyDays,
        COUNT(DISTINCT Invoice) AS Frequency,
        ROUND(SUM(LineRevenue), 2) AS Monetary
    FROM transactions
    WHERE CustomerID IS NOT NULL AND is_cancelled = 0
    GROUP BY CustomerID
)
SELECT 
    CustomerID,
    RecencyDays,
    Frequency,
    Monetary,
    NTILE(5) OVER (ORDER BY RecencyDays DESC) AS R_Score,  -- 5 = most recent
    NTILE(5) OVER (ORDER BY Frequency ASC) AS F_Score,     -- 5 = highest frequency
    NTILE(5) OVER (ORDER BY Monetary ASC) AS M_Score       -- 5 = highest monetary
FROM CustomerRFM
ORDER BY Monetary DESC
LIMIT 15;
