# Financial Analyzer

A Python-based tool to automatically fetch, analyze, and store fundamental financial insights (pros & cons) for a list of companies using an external financial data API and a MySQL database.

## 🚀 Overview

This project:

1. Fetches financial data (balance sheet, profit & loss, cash flow) for each company from an API.  
2. Computes key metrics such as:
   - Debt levels and debt reduction  
   - Return on Equity (ROE)  
   - Dividend payout  
   - Sales and profit growth (1-year, 5-year average, 10-year median)  
3. Generates human-readable **pros** and **cons** based on these metrics.  
4. Stores the results in a MySQL table (`ml`) for later use in dashboards, apps, or reports.  

The main logic is implemented in the `FinancialAnalyzer` class and executed via the `main()` function.

---

## 🧩 Features

- ✅ Fetches company financials from a REST API using `requests`
- ✅ Robust numeric handling with safe float conversion
- ✅ Growth calculations:
  - Year-over-year growth
  - 5-year average growth
  - 10-year median growth
- ✅ Rule-based generation of **pros** and **cons** strings
- ✅ MySQL integration using SQLAlchemy
- ✅ Upsert-style insert (`ON DUPLICATE KEY UPDATE`) to keep the latest analysis
- ✅ Batch processing of multiple companies

---

## 🛠 Tech Stack

- **Language:** Python  
- **Libraries:**
  - `pandas`
  - `numpy`
  - `requests`
  - `sqlalchemy`
  - `mysql-connector-python`
- **Database:** MySQL

---

## 📁 Main Components

### `FinancialAnalyzer` class

Key methods:

- `__init__()`
  - Sets API key, base URL, DB config, and creates a SQLAlchemy engine.
- `create_db_connection()`
  - Builds a MySQL connection string and returns an SQLAlchemy engine.
- `safe_float_conversion(value)`
  - Safely converts values to `float`, returning `0.0` on failure.
- `fetch_company_data(company_id)`
  - Calls the external API and returns JSON data for a given company.
- `calculate_growth_metrics(data_list, value_key)`
  - Calculates 1-year growth rate for a field (e.g. `net_profit`, `sales`).
- `calculate_average_growth(data_list, value_key, years=5)`
  - Calculates average growth over up to the last 5 years.
- `calculate_median_growth(data_list, value_key, years=10)`
  - Calculates median growth over up to the last 10 years.
- `analyze_financials(company_data)`
  - Core logic that:
    - Sorts financial data by year (latest first)
    - Evaluates debt level, ROE, dividend payout, profit growth, and sales growth
    - Builds lists of **pros** and **cons** (max 3 each)
- `store_analysis_results(company_id, company_name, pros, cons)`
  - Stores pros/cons as JSON strings in the `ml` table.
- `process_company(company_id)`
  - Orchestrates: fetch → analyze → print → store.
- `process_all_companies(company_list)`
  - Iterates through a list of company IDs and processes them.

### `main()` function

- Initializes `FinancialAnalyzer`
- Defines a list of company IDs (e.g., `ABB`, `ADANIENT`, `RELIANCE`, etc.)
- Calls `process_all_companies()` for batch processing

---

## ⚙️ Setup & Installation

### 1. Clone / Copy the Project

Place the script into your project folder, e.g.:

```bash
financial-analyzer/
  └── financial_analyzer.py
