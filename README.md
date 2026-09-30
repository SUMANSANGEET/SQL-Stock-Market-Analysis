# Stock Market Analysis in SQL

End-to-end data analytics project on six NSE stocks (Bajaj Auto, Eicher Motors, Hero Motocorp, Infosys, TCS, TVS Motors), 889 trading days each, 1 Jan 2015 to 31 Jul 2018. All analysis is written in **SQL** (window functions, CTEs); Python and Streamlit sit on top for visuals and a live SQL playground.

## Headline findings

| | |
|---|---|
| Signals | 20/50-day golden cross gives **56 Buy / 57 Sell** across the six stocks, matching the course deck |
| Data trap | TCS (31 May 2018) and Infosys (15 Jun 2015) show a ~50% one-day "crash". Both are **1:1 bonus issues**, not losses |
| Corrected returns | TCS **-23.8% to +52.4%**, Infosys **-30.9% to +38.2%** after adjusting |
| Changed call | On adjusted prices TCS's latest signal is a **Buy** (20 Apr 2018), not the deck's Sell |
| Strategy check | The golden-cross strategy **trailed buy-and-hold on all six** stocks (no costs included) |
| Final view | Buy Bajaj Auto, Infosys, TCS. Sell / reduce Eicher, TVS, Hero |

## What is in the box

```
streamlit_app.py            Dashboard + SQL playground (6 tabs)
sandbox.py                  Safe per-session SQL sandbox + "Check answer" logic
stockdb.py                  CSV -> SQLite loader; runs the tagged .sql file section by section
analytics.py                Backtest, risk table, current trend (reads SQL-built tables)
sql/analysis_sqlite.sql     SUBMISSION 1: all 13 tasks + 3 extensions (verified against every guide checkpoint)
sql/analysis_mysql.sql      MySQL 8 version with CSV loader and get_signal() function (see note below)
notebooks/                  Stock_Market_SQL_Analysis.ipynb (executed, interactive Plotly) + .html export
report/                     SUBMISSION 2: Stock_Market_SQL_Insights.pdf (6 pages)
build_notebook.py, build_report.py   Regenerate the notebook and the PDF
data/                       The six source CSVs
```

## Run it

```bash
python -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt

streamlit run streamlit_app.py                          # dashboard + SQL playground
jupyter notebook notebooks/Stock_Market_SQL_Analysis.ipynb
python build_report.py                                  # rebuilds report/*.pdf
```

The app builds an in-memory SQLite database from the CSVs at start-up (about a second); no external database is needed.

## Deploy on Streamlit Community Cloud (free)

1. Push this folder to a public GitHub repo (keep `data/` and `sql/` in it).
2. Go to share.streamlit.io, choose **New app**, pick the repo, set **Main file path** to `streamlit_app.py`.
3. Deploy. `requirements.txt` is picked up automatically (the report/notebook packages can be removed for a lighter build).

## The SQL playground

- A real SQLite database, private to each visitor's session; **Reset database** restores it.
- Start from *raw + analysis tables*, or *raw tables only* to practise building `bajaj1`, `master_table`, `bajaj2` yourself.
- Pick any of Tasks 1-13, write your query, and press **Check answer**. It compares your result with the verified reference without showing the solution. **Load solution SQL** reveals it.
- Schema browser, query history, CSV download, and a "chart this result" builder.
- Guard rails: ATTACH / PRAGMA / extension loading are blocked, queries stop after 6 s, results are capped at 5,000 rows.

## Notes and caveats

- **MySQL file:** written from the SQLite version that was run and verified here. I could not run MySQL in this environment, so run it in your own MySQL 8 instance and compare against the checkpoints (889 rows, first Buy 2015-05-18, 56 / 57 signals in total). Enable `local_infile` for `LOAD DATA LOCAL INFILE`.
- **Bonus dates** (Infosys 2015-06-15, TCS 2018-05-31) were found from the price series (Task 12) and are hard-coded in Task 13 / E1. A production pipeline should read a corporate-actions table.
- **Backtest:** long-only, no transaction costs or taxes, dividends excluded, single in-sample period. Illustrative, not investment advice.
- **Course-deck discrepancies:** the deck prints Infosys as a "3% decrease" (data: -30.9%), and its TCS line shows values from the wrong rows. Details are in section 10 of the notebook and page 6 of the PDF.

## Video walkthrough outline (about 5 minutes)

1. **0:00** The problem and the data: six stocks, 889 days, what a golden cross is (30 s).
2. **0:30** SQL walkthrough: window function with `ROWS BETWEEN 19 PRECEDING`, why the first 19 rows are NULL, `LAG()` for the two-day cross test (90 s).
3. **2:00** Scale up: one chained-CTE query for all six stocks, `PARTITION BY stock`, totals 56 / 57 (45 s).
4. **2:45** The data trap: worst-day query, TCS and Infosys at -50%, bonus issue explained, returns before and after (90 s).
5. **4:15** Live demo in Streamlit: signal explorer, raw/adjusted toggle, then run and check a query in the playground (45 s).
6. **5:00** Recommendation, and the honest limitation that the strategy trailed buy-and-hold (30 s).
