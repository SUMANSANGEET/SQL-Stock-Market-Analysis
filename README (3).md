# 📈 SQL Stock Market Analysis

### Interactive Financial Analytics • SQL Engineering • Market Intelligence

<p align="center">
  <img src="https://img.shields.io/badge/SQL-Analytics-0F766E?style=for-the-badge&logo=sqlite&logoColor=white" alt="SQL Analytics"/>
  <img src="https://img.shields.io/badge/Python-Analytics-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python"/>
  <img src="https://img.shields.io/badge/Streamlit-Interactive_App-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white" alt="Streamlit"/>
  <img src="https://img.shields.io/badge/Pandas-Data_Processing-150458?style=for-the-badge&logo=pandas&logoColor=white" alt="Pandas"/>
</p>

<p align="center">
  <strong>From raw NSE stock prices to actionable market intelligence using SQL, Python, and interactive analytics.</strong>
</p>

<p align="center">
  <a href="https://sql-stock-market-analysis-env8nvagivl5pokcrooupb.streamlit.app/">
    <img src="https://img.shields.io/badge/🚀_LIVE_STREAMLIT_APP-Open_Dashboard-FF4B4B?style=for-the-badge" alt="Live Streamlit App"/>
  </a>
</p>

<p align="center">
  🔴 <strong>Live Interactive Dashboard:</strong>
  <a href="https://sql-stock-market-analysis-env8nvagivl5pokcrooupb.streamlit.app/">
    https://sql-stock-market-analysis-env8nvagivl5pokcrooupb.streamlit.app/
  </a>
</p>

---

## 🚀 Project Overview

**SQL Stock Market Analysis** is an end-to-end financial analytics project that transforms historical stock-market data into an interactive analytical experience.

The project analyzes daily price data for **6 NSE-listed companies** across the period:

> **1 January 2015 – 31 July 2018**

The analysis combines **SQL querying, financial metrics, statistical analysis, data engineering, Python analytics, and interactive Streamlit visualization** to investigate price behavior, returns, volatility, trading activity, and cross-company performance.

### 🎯 Companies Analyzed

| Company       | Market    |
| ------------- | --------- |
| Bajaj Auto    | NSE India |
| Eicher Motors | NSE India |
| Hero Motocorp | NSE India |
| Infosys       | NSE India |
| TCS           | NSE India |
| TVS Motors    | NSE India |

---

# 🌐 Live Interactive Application

## 🚀 Explore the Dashboard

### 👉 [Open Live Streamlit App](https://sql-stock-market-analysis-env8nvagivl5pokcrooupb.streamlit.app/)

**Live Application:**
https://sql-stock-market-analysis-env8nvagivl5pokcrooupb.streamlit.app/

The deployed application provides an interactive environment for exploring the historical stock-market dataset and SQL-driven analytical outputs.

### Dashboard capabilities

* 📊 Market overview
* 📈 Price trend exploration
* 💹 Return analysis
* 📉 Volatility analysis
* 🔎 Stock-level filtering
* 🧮 SQL-powered analytical queries
* 📅 Date-range analysis
* 🏢 Company comparison
* 📋 Detailed analytical tables
* 📌 KPI-driven market summaries
* ⚡ Interactive exploratory analysis

---

# 🖥️ Interactive Dashboard Preview

Place your screenshots in the repository:

```text
screenshots/
├── 01_overview.png
├── 02_price_analysis.png
├── 03_returns_analysis.png
├── 04_volatility_analysis.png
└── 05_sql_insights.png
```

<p align="center">
  <img src="screenshots/01_overview.png" width="95%" alt="SQL Stock Market Analysis Dashboard"/>
</p>

<p align="center">
  <em>Interactive SQL Stock Market Analysis Dashboard</em>
</p>

### 🔗 Try the dashboard

**[🚀 Launch Live Streamlit Application](https://sql-stock-market-analysis-env8nvagivl5pokcrooupb.streamlit.app/)**

---

# 💡 Business Problem

Historical stock datasets contain valuable information, but raw price records alone do not provide an analytical decision-support layer.

This project addresses questions such as:

* Which companies experienced different patterns of historical price movement?
* How did stock prices change over time?
* How can historical volatility be measured?
* How can daily returns be calculated using SQL?
* What were the strongest and weakest trading periods?
* How can multiple companies be analyzed consistently?
* How can SQL transform raw financial data into business-ready insights?
* How can analytical results be exposed through an interactive application?

---

# 🎯 Project Objectives

### 01 — Data Preparation

Clean, validate, structure, and standardize historical stock-market data.

### 02 — SQL Analytics

Develop analytical SQL queries for financial and market metrics.

### 03 — Financial Metrics

Calculate price movement, returns, volatility, trading activity, and related indicators.

### 04 — Comparative Analysis

Compare historical market behavior across six companies.

### 05 — Interactive Visualization

Convert analytical results into an intuitive Streamlit experience.

### 06 — Portfolio Demonstration

Demonstrate practical skills across SQL, Python, analytics, visualization, and data storytelling.

---

# 🧠 Analytical Framework

```text
                 RAW STOCK DATA
                       │
                       ▼
              ┌─────────────────┐
              │ Data Validation  │
              │ & Preparation    │
              └────────┬────────┘
                       │
                       ▼
              ┌─────────────────┐
              │ SQL Data Layer   │
              │ SQLite / MySQL   │
              └────────┬────────┘
                       │
                       ▼
             ┌──────────────────┐
             │ Financial Metrics │
             ├──────────────────┤
             │ Price Trends      │
             │ Returns           │
             │ Volatility        │
             │ Volume            │
             │ Rankings          │
             └─────────┬────────┘
                       │
                       ▼
              ┌─────────────────┐
              │ Python Analytics │
              │ Pandas / NumPy   │
              └────────┬────────┘
                       │
                       ▼
             ┌──────────────────┐
             │ Streamlit UI      │
             │ Interactive       │
             │ Exploration       │
             └─────────┬────────┘
                       │
                       ▼
              MARKET INSIGHTS
```

---

# 📊 Key Analytical Areas

## 📈 Price Trend Analysis

Historical price movement is examined across different companies and time periods.

Typical questions include:

* Opening vs closing price movement
* Highest and lowest historical prices
* Price appreciation
* Daily price changes
* Long-term price trajectories

---

## 💹 Return Analysis

The project calculates historical returns to understand price performance.

Example:

```sql
SELECT
    Date,
    Close,
    LAG(Close) OVER (ORDER BY Date) AS Previous_Close,
    ((Close - LAG(Close) OVER (ORDER BY Date))
        / LAG(Close) OVER (ORDER BY Date)) * 100 AS Daily_Return
FROM stock_prices;
```

This demonstrates practical use of:

* Window functions
* `LAG()`
* Percentage calculations
* Ordered analytical transformations

---

# 📉 Volatility Analysis

Historical volatility provides a way to quantify how widely returns varied over time.

The project explores:

* Daily return variation
* Standard deviation
* High/low price ranges
* Relative market movement
* Company-level volatility comparisons

---

# 🧮 SQL Analysis

The project demonstrates practical SQL techniques including:

### Core SQL

```text
SELECT
WHERE
GROUP BY
HAVING
ORDER BY
LIMIT
DISTINCT
```

### Analytical SQL

```text
CASE
CTEs
Subqueries
Aggregate Functions
Window Functions
LAG()
LEAD()
ROW_NUMBER()
RANK()
```

### Financial Analytics

```text
Daily Returns
Cumulative Returns
Price Change
Volatility
Moving Metrics
High/Low Analysis
Company Rankings
Trading Activity
```

---

# 🗄️ SQL Database Support

The project includes SQL analysis for:

### SQLite

```text
sql/analysis_sqlite.sql
```

### MySQL

```text
sql/analysis_mysql.sql
```

This demonstrates analytical SQL across two database environments.

---

# 🐍 Python Analytics Layer

Python is used to support:

* Data loading
* Data cleaning
* SQL integration
* Data transformation
* Exploratory analysis
* Financial calculations
* Visualization
* Streamlit application development

### Main technologies

```text
Python
Pandas
NumPy
Matplotlib
Plotly
Streamlit
SQLite
MySQL
```

---

# 📊 KPI Layer

The dashboard is designed around decision-oriented KPIs such as:

| KPI               | Purpose                                          |
| ----------------- | ------------------------------------------------ |
| 📈 Latest Price   | Historical closing price for the selected record |
| 📊 Price Change   | Measures price movement                          |
| 💹 Return         | Evaluates historical performance                 |
| 📉 Volatility     | Measures historical price variability            |
| 🔺 Highest Price  | Identifies historical peak                       |
| 🔻 Lowest Price   | Identifies historical trough                     |
| 📦 Trading Volume | Measures market activity                         |

> KPI definitions depend on the selected company and analysis period.

---

# 🔎 Interactive Analysis

The Streamlit application enables users to explore the dataset dynamically.

### Interactive controls

```text
Company Selection
Date Range
Metric Selection
Analysis Type
SQL Query Exploration
```

Users can move through the analytical workflow:

```text
Market Overview
      ↓
Company Selection
      ↓
Historical Trend
      ↓
Returns
      ↓
Volatility
      ↓
Detailed SQL Analysis
      ↓
Market Insights
```

---

# 📌 Example SQL Business Questions

### Q1. What is the highest recorded closing price?

```sql
SELECT
    MAX(Close) AS Highest_Close
FROM stock_prices;
```

### Q2. What is the lowest recorded closing price?

```sql
SELECT
    MIN(Close) AS Lowest_Close
FROM stock_prices;
```

### Q3. What is the average closing price?

```sql
SELECT
    AVG(Close) AS Average_Close
FROM stock_prices;
```

### Q4. Which dates experienced the largest price movements?

```sql
SELECT
    Date,
    Close,
    Open,
    (Close - Open) AS Price_Change
FROM stock_prices
ORDER BY ABS(Close - Open) DESC;
```

### Q5. How can stocks be ranked by historical return?

```sql
SELECT
    Company,
    AVG(Daily_Return) AS Average_Return
FROM stock_returns
GROUP BY Company
ORDER BY Average_Return DESC;
```

---

# 🏢 Business Use Cases

## 💼 Portfolio & Investment Research

Historical market data can be explored to understand:

* Price behavior
* Historical returns
* Volatility
* Cross-company differences

> **Educational analysis only — not investment advice.**

---

## 🛡️ Risk Analysis

Historical volatility and price movements can support analytical exercises involving:

* Risk measurement
* Market variability
* Historical drawdowns
* Comparative risk profiles

---

## 🧹 Data Quality & Corporate Analytics

The project demonstrates a complete transformation workflow:

```text
Collected
   ↓
Validated
   ↓
Cleaned
   ↓
Transformed
   ↓
Analyzed
   ↓
Visualized
```

---

## 🏦 FinTech & Wealth-Tech Prototyping

The architecture can serve as a foundation for prototypes involving:

* Market dashboards
* Financial analytics
* Portfolio monitoring
* Stock-screening interfaces
* Historical market exploration

---

## 📊 Analytics Engineering & BI

```text
Data → SQL → Metrics → Python → Dashboard → Insights
```

---

# 🧱 Project Structure

```text
SQL-Stock-Market-Analysis/
│
├── 📁 .streamlit/
│   └── config.toml
│
├── 📁 data/
│   ├── Bajaj_Auto.csv
│   ├── Eicher_Motors.csv
│   ├── Hero_Motocorp.csv
│   ├── Infosys.csv
│   ├── TCS.csv
│   └── TVS_Motors.csv
│
├── 📁 datasets/
│   ├── Bajaj Auto.csv
│   ├── Eicher Motors.csv
│   ├── Hero Motocorp.csv
│   ├── Infosys.csv
│   ├── TCS.csv
│   └── TVS Motors.csv
│
├── 📁 notebooks/
│   ├── Stock_Market_SQL_Analysis.html
│   └── Stock_Market_SQL_Analysis.ipynb
│
├── 📁 sql/
│   ├── analysis_mysql.sql
│   └── analysis_sqlite.sql
│
├── 📁 report/
│   └── Stock_Market_SQL_Insights.pdf
│
├── 📄 app.py
├── 📄 analytics.py
├── 📄 stockdb.py
├── 📄 build_notebook.py
├── 📄 build_report.py
├── 📄 requirements.txt
├── 📄 README.md
└── 📄 .gitignore
```

---

# ⚙️ Installation

Clone the repository:

```bash
git clone https://github.com/YOUR_USERNAME/SQL-Stock-Market-Analysis.git
```

Navigate into the project:

```bash
cd SQL-Stock-Market-Analysis
```

Create a virtual environment:

```bash
python -m venv venv
```

Activate it on Windows:

```bash
venv\Scripts\activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

---

# ▶️ Run the Streamlit Application

Execute:

```bash
streamlit run app.py
```

The application will normally open at:

```text
http://localhost:8501
```

### 🌐 Deployed Version

The production-style deployed version is available here:

### [🚀 Open SQL Stock Market Analysis — Live App](https://sql-stock-market-analysis-env8nvagivl5pokcrooupb.streamlit.app/)

---

# 🗃️ SQL Setup

## SQLite

```text
sql/analysis_sqlite.sql
```

## MySQL

```text
sql/analysis_mysql.sql
```

Configure the required database connection according to your local environment.

**Never commit database passwords, API keys, secrets, or credentials to GitHub.**

---

# 📚 Project Deliverables

| Deliverable                       | Description                        |
| --------------------------------- | ---------------------------------- |
| `app.py`                          | Interactive Streamlit application  |
| `analytics.py`                    | Analytics and metric logic         |
| `stockdb.py`                      | Database/data access functionality |
| `analysis_mysql.sql`              | MySQL analytical queries           |
| `analysis_sqlite.sql`             | SQLite analytical queries          |
| `Stock_Market_SQL_Analysis.ipynb` | Notebook-based analysis            |
| `Stock_Market_SQL_Insights.pdf`   | Analytical report                  |
| `requirements.txt`                | Python dependencies                |

---

# 🔬 Skills Demonstrated

### SQL
