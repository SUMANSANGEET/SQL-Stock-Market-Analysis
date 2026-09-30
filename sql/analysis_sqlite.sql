-- =====================================================================
--  STOCK MARKET ANALYSIS IN SQL  |  Six NSE stocks, Jan 2015 - Jul 2018
--  Dialect : SQLite (runs in the notebook, Streamlit playground, DB Browser)
--  MySQL 8 : see sql/analysis_mysql.sql (same logic, MySQL syntax)
--  Raw tables (created by stockdb.py from the CSVs, 889 rows each):
--    bajaj_auto, eicher_motors, hero_motocorp, infosys, tcs, tvs_motors
--  Sections are tagged "-- ### TASK <id> | <title>" so Python can run them one by one.
-- =====================================================================


-- ### TASK 1 | How much history do we have?
SELECT COUNT(*)  AS trading_days,
       MIN(date) AS first_day,
       MAX(date) AS last_day
FROM bajaj_auto;


-- ### TASK 2 | Eicher's five best closes
SELECT date, close_price
FROM eicher_motors
ORDER BY close_price DESC
LIMIT 5;


-- ### TASK 3 | TCS, year by year
SELECT strftime('%Y', date)          AS year,
       ROUND(AVG(close_price), 2)    AS avg_close
FROM tcs
GROUP BY strftime('%Y', date)
ORDER BY year;


-- ### TASK 4 | Find the holes (missing deliverable_qty)
SELECT 'bajaj_auto'    AS stock, date FROM bajaj_auto    WHERE deliverable_qty IS NULL
UNION ALL
SELECT 'eicher_motors' AS stock, date FROM eicher_motors WHERE deliverable_qty IS NULL
UNION ALL
SELECT 'hero_motocorp' AS stock, date FROM hero_motocorp WHERE deliverable_qty IS NULL
UNION ALL
SELECT 'infosys'       AS stock, date FROM infosys       WHERE deliverable_qty IS NULL
UNION ALL
SELECT 'tcs'           AS stock, date FROM tcs           WHERE deliverable_qty IS NULL
UNION ALL
SELECT 'tvs_motors'    AS stock, date FROM tvs_motors    WHERE deliverable_qty IS NULL;


-- ### TASK 5 | Moving averages for Bajaj Auto -> table bajaj1
DROP TABLE IF EXISTS bajaj1;

CREATE TABLE bajaj1 AS
SELECT date,
       close_price,
       CASE WHEN ROW_NUMBER() OVER (ORDER BY date) >= 20
            THEN ROUND(AVG(close_price) OVER (ORDER BY date
                       ROWS BETWEEN 19 PRECEDING AND CURRENT ROW), 2) END AS ma20,
       CASE WHEN ROW_NUMBER() OVER (ORDER BY date) >= 50
            THEN ROUND(AVG(close_price) OVER (ORDER BY date
                       ROWS BETWEEN 49 PRECEDING AND CURRENT ROW), 2) END AS ma50
FROM bajaj_auto;

SELECT * FROM bajaj1 ORDER BY date DESC LIMIT 5;


-- ### TASK 6 | Master table: one close-price column per stock
DROP TABLE IF EXISTS master_table;

CREATE TABLE master_table AS
SELECT b.date,
       b.close_price AS bajaj,
       t.close_price AS tcs,
       v.close_price AS tvs,
       i.close_price AS infosys,
       e.close_price AS eicher,
       h.close_price AS hero
FROM bajaj_auto b
JOIN tcs           t ON t.date = b.date
JOIN tvs_motors    v ON v.date = b.date
JOIN infosys       i ON i.date = b.date
JOIN eicher_motors e ON e.date = b.date
JOIN hero_motocorp h ON h.date = b.date;

SELECT * FROM master_table ORDER BY date DESC LIMIT 5;


-- ### TASK 7 | Golden-cross Buy / Sell / Hold signals for Bajaj -> table bajaj2
DROP TABLE IF EXISTS bajaj2;

CREATE TABLE bajaj2 AS
WITH t AS (
    SELECT date, close_price, ma20, ma50,
           LAG(ma20) OVER (ORDER BY date) AS prev_ma20,
           LAG(ma50) OVER (ORDER BY date) AS prev_ma50
    FROM bajaj1
)
SELECT date,
       close_price,
       CASE
           WHEN ma20 IS NULL OR ma50 IS NULL
             OR prev_ma20 IS NULL OR prev_ma50 IS NULL THEN 'Hold'
           WHEN ma20 > ma50 AND prev_ma20 <= prev_ma50  THEN 'Buy'
           WHEN ma20 < ma50 AND prev_ma20 >= prev_ma50  THEN 'Sell'
           ELSE 'Hold'
       END AS signal
FROM t;

SELECT * FROM bajaj2 WHERE signal <> 'Hold' ORDER BY date LIMIT 6;


-- ### TASK 8 | How often did the signals trigger? (Bajaj)
SELECT signal, COUNT(*) AS days
FROM bajaj2
GROUP BY signal
ORDER BY signal;


-- ### TASK 9 | Signal on a given day (Bajaj, 2018-06-21)
SELECT signal
FROM bajaj2
WHERE date = '2018-06-21';


-- ### TASK 10 | All six stocks in one query
WITH prices AS (
    SELECT 'Bajaj Auto'    AS stock, date, close_price FROM bajaj_auto    UNION ALL
    SELECT 'Eicher Motors' AS stock, date, close_price FROM eicher_motors UNION ALL
    SELECT 'Hero Motocorp' AS stock, date, close_price FROM hero_motocorp UNION ALL
    SELECT 'Infosys'       AS stock, date, close_price FROM infosys       UNION ALL
    SELECT 'TCS'           AS stock, date, close_price FROM tcs           UNION ALL
    SELECT 'TVS Motors'    AS stock, date, close_price FROM tvs_motors
),
ma AS (
    SELECT stock, date, close_price,
           CASE WHEN ROW_NUMBER() OVER (PARTITION BY stock ORDER BY date) >= 20
                THEN AVG(close_price) OVER (PARTITION BY stock ORDER BY date
                         ROWS BETWEEN 19 PRECEDING AND CURRENT ROW) END AS ma20,
           CASE WHEN ROW_NUMBER() OVER (PARTITION BY stock ORDER BY date) >= 50
                THEN AVG(close_price) OVER (PARTITION BY stock ORDER BY date
                         ROWS BETWEEN 49 PRECEDING AND CURRENT ROW) END AS ma50
    FROM prices
),
lagged AS (
    SELECT stock, date, close_price, ma20, ma50,
           LAG(ma20) OVER (PARTITION BY stock ORDER BY date) AS prev_ma20,
           LAG(ma50) OVER (PARTITION BY stock ORDER BY date) AS prev_ma50
    FROM ma
),
sig AS (
    SELECT stock, date, close_price,
           CASE
               WHEN ma20 IS NULL OR ma50 IS NULL
                 OR prev_ma20 IS NULL OR prev_ma50 IS NULL THEN 'Hold'
               WHEN ma20 > ma50 AND prev_ma20 <= prev_ma50  THEN 'Buy'
               WHEN ma20 < ma50 AND prev_ma20 >= prev_ma50  THEN 'Sell'
               ELSE 'Hold'
           END AS signal
    FROM lagged
),
latest AS (
    SELECT stock, date, signal,
           ROW_NUMBER() OVER (PARTITION BY stock ORDER BY date DESC) AS rn
    FROM sig
    WHERE signal <> 'Hold'
)
SELECT s.stock,
       SUM(s.signal = 'Buy')  AS buys,
       SUM(s.signal = 'Sell') AS sells,
       l.date                 AS last_signal_date,
       l.signal               AS last_signal
FROM sig s
JOIN latest l ON l.stock = s.stock AND l.rn = 1
GROUP BY s.stock
ORDER BY s.stock;


-- ### TASK 11 | Who went up? (raw, unadjusted)
WITH prices AS (
    SELECT 'Bajaj Auto'    AS stock, date, close_price FROM bajaj_auto    UNION ALL
    SELECT 'Eicher Motors' AS stock, date, close_price FROM eicher_motors UNION ALL
    SELECT 'Hero Motocorp' AS stock, date, close_price FROM hero_motocorp UNION ALL
    SELECT 'Infosys'       AS stock, date, close_price FROM infosys       UNION ALL
    SELECT 'TCS'           AS stock, date, close_price FROM tcs           UNION ALL
    SELECT 'TVS Motors'    AS stock, date, close_price FROM tvs_motors
),
ends AS (
    SELECT stock, MIN(date) AS first_day, MAX(date) AS last_day
    FROM prices GROUP BY stock
)
SELECT e.stock,
       f.close_price AS first_close,
       l.close_price AS last_close,
       ROUND(100.0 * (l.close_price - f.close_price) / f.close_price, 1) AS pct_change
FROM ends e
JOIN prices f ON f.stock = e.stock AND f.date = e.first_day
JOIN prices l ON l.stock = e.stock AND l.date = e.last_day
ORDER BY pct_change DESC;


-- ### TASK 12 | The data trap: each stock's single worst day
WITH prices AS (
    SELECT 'Bajaj Auto'    AS stock, date, close_price FROM bajaj_auto    UNION ALL
    SELECT 'Eicher Motors' AS stock, date, close_price FROM eicher_motors UNION ALL
    SELECT 'Hero Motocorp' AS stock, date, close_price FROM hero_motocorp UNION ALL
    SELECT 'Infosys'       AS stock, date, close_price FROM infosys       UNION ALL
    SELECT 'TCS'           AS stock, date, close_price FROM tcs           UNION ALL
    SELECT 'TVS Motors'    AS stock, date, close_price FROM tvs_motors
),
moves AS (
    SELECT stock, date, close_price,
           100.0 * (close_price / LAG(close_price) OVER (PARTITION BY stock ORDER BY date) - 1) AS pct_move
    FROM prices
),
ranked AS (
    SELECT *, ROW_NUMBER() OVER (PARTITION BY stock ORDER BY pct_move) AS rk
    FROM moves
    WHERE pct_move IS NOT NULL
)
SELECT stock, date, close_price, ROUND(pct_move, 1) AS pct_move
FROM ranked
WHERE rk = 1
ORDER BY pct_move;


-- ### TASK 13 | Fix it: adjust TCS and Infosys for their 1:1 bonus issues
-- Event dates = first day trading at the new (halved) level, found in Task 12.
--   Infosys 2015-06-15   |   TCS 2018-05-31
WITH adjusted AS (
    SELECT 'TCS' AS stock, date,
           CASE WHEN date < '2018-05-31' THEN close_price / 2.0 ELSE close_price END AS adj_close
    FROM tcs
    UNION ALL
    SELECT 'Infosys' AS stock, date,
           CASE WHEN date < '2015-06-15' THEN close_price / 2.0 ELSE close_price END AS adj_close
    FROM infosys
)
SELECT stock,
       ROUND(100.0 * (MAX(CASE WHEN date = '2018-07-31' THEN adj_close END) /
                      MAX(CASE WHEN date = '2015-01-01' THEN adj_close END) - 1), 1) AS adjusted_pct_change
FROM adjusted
GROUP BY stock
ORDER BY stock;


-- =====================================================================
--  PART 4 - EXTENSIONS (portfolio-level additions beyond the brief)
-- =====================================================================

-- ### TASK E1 | Price table with bonus adjustment for all six stocks -> prices_adj
DROP TABLE IF EXISTS prices_adj;

CREATE TABLE prices_adj AS
SELECT 'Bajaj Auto' AS stock, date, close_price AS raw_close, close_price AS adj_close FROM bajaj_auto
UNION ALL
SELECT 'Eicher Motors', date, close_price, close_price FROM eicher_motors
UNION ALL
SELECT 'Hero Motocorp', date, close_price, close_price FROM hero_motocorp
UNION ALL
SELECT 'Infosys', date, close_price,
       CASE WHEN date < '2015-06-15' THEN close_price / 2.0 ELSE close_price END FROM infosys
UNION ALL
SELECT 'TCS', date, close_price,
       CASE WHEN date < '2018-05-31' THEN close_price / 2.0 ELSE close_price END FROM tcs
UNION ALL
SELECT 'TVS Motors', date, close_price, close_price FROM tvs_motors;

SELECT stock, COUNT(*) AS rows_, MIN(date) AS first_day, MAX(date) AS last_day
FROM prices_adj GROUP BY stock ORDER BY stock;


-- ### TASK E2 | Signals for all six stocks, RAW vs ADJUSTED prices -> stock_signals
-- price_basis = 'raw' reproduces the course deck; 'adjusted' removes the bonus-issue jump.
DROP TABLE IF EXISTS stock_signals;

CREATE TABLE stock_signals AS
WITH basis AS (
    SELECT 'raw'      AS price_basis, stock, date, raw_close AS close_price FROM prices_adj
    UNION ALL
    SELECT 'adjusted' AS price_basis, stock, date, adj_close AS close_price FROM prices_adj
),
ma AS (
    SELECT price_basis, stock, date, close_price,
           ROW_NUMBER() OVER w AS rn,
           AVG(close_price) OVER (PARTITION BY price_basis, stock ORDER BY date
                ROWS BETWEEN 19 PRECEDING AND CURRENT ROW) AS avg20,
           AVG(close_price) OVER (PARTITION BY price_basis, stock ORDER BY date
                ROWS BETWEEN 49 PRECEDING AND CURRENT ROW) AS avg50
    FROM basis
    WINDOW w AS (PARTITION BY price_basis, stock ORDER BY date)
),
ma2 AS (
    SELECT price_basis, stock, date, close_price,
           CASE WHEN rn >= 20 THEN avg20 END AS ma20,
           CASE WHEN rn >= 50 THEN avg50 END AS ma50
    FROM ma
),
lagged AS (
    SELECT *, LAG(ma20) OVER (PARTITION BY price_basis, stock ORDER BY date) AS prev_ma20,
              LAG(ma50) OVER (PARTITION BY price_basis, stock ORDER BY date) AS prev_ma50
    FROM ma2
)
SELECT price_basis, stock, date, close_price, ma20, ma50,
       CASE
           WHEN ma20 IS NULL OR ma50 IS NULL
             OR prev_ma20 IS NULL OR prev_ma50 IS NULL THEN 'Hold'
           WHEN ma20 > ma50 AND prev_ma20 <= prev_ma50  THEN 'Buy'
           WHEN ma20 < ma50 AND prev_ma20 >= prev_ma50  THEN 'Sell'
           ELSE 'Hold'
       END AS signal
FROM lagged;

SELECT price_basis, stock,
       SUM(signal = 'Buy') AS buys, SUM(signal = 'Sell') AS sells
FROM stock_signals
GROUP BY price_basis, stock
ORDER BY stock, price_basis;


-- ### TASK E3 | Risk profile: daily volatility and worst/best day (adjusted prices)
WITH moves AS (
    SELECT stock, date,
           adj_close / LAG(adj_close) OVER (PARTITION BY stock ORDER BY date) - 1 AS r
    FROM prices_adj
)
SELECT stock,
       ROUND(100 * AVG(r), 3)                                            AS avg_daily_pct,
       ROUND(100 * SQRT(AVG(r * r) - AVG(r) * AVG(r)), 3)                AS daily_vol_pct,
       ROUND(100 * MIN(r), 1)                                            AS worst_day_pct,
       ROUND(100 * MAX(r), 1)                                            AS best_day_pct
FROM moves
WHERE r IS NOT NULL
GROUP BY stock
ORDER BY daily_vol_pct DESC;
