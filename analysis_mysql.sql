-- =====================================================================
--  STOCK MARKET ANALYSIS IN SQL  |  MySQL 8.0+ submission file
--  Same logic as sql/analysis_sqlite.sql, MySQL syntax.
--  NOTE: written against the SQLite version that was run and verified here;
--        run it in your own MySQL 8 instance and compare with the checkpoints.
-- =====================================================================

CREATE DATABASE IF NOT EXISTS stock_analysis;
USE stock_analysis;

-- ---------------------------------------------------------------------
-- APPENDIX A - load the CSVs (repeat for each of the six files)
-- Dates in the CSV look like '31-July-2018', so load into a staging column and
-- convert with STR_TO_DATE. Enable local_infile on server and client first.
-- ---------------------------------------------------------------------
DROP TABLE IF EXISTS bajaj_auto;
CREATE TABLE bajaj_auto (
    date DATE PRIMARY KEY,
    open_price DECIMAL(12,2), high_price DECIMAL(12,2), low_price DECIMAL(12,2),
    close_price DECIMAL(12,2), wap DECIMAL(24,18),
    no_of_shares BIGINT, no_of_trades BIGINT, total_turnover DECIMAL(20,2),
    deliverable_qty BIGINT NULL, pct_deli_qty DECIMAL(6,2),
    spread_high_low DECIMAL(12,2), spread_close_open DECIMAL(12,2)
);

LOAD DATA LOCAL INFILE 'data/Bajaj_Auto.csv'
INTO TABLE bajaj_auto
FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 LINES
(@d, open_price, high_price, low_price, close_price, wap, no_of_shares, no_of_trades,
 total_turnover, @dq, pct_deli_qty, spread_high_low, spread_close_open)
SET date = STR_TO_DATE(@d, '%e-%M-%Y'),
    deliverable_qty = NULLIF(@dq, '');

-- Clone the structure for the other five, then LOAD DATA each CSV the same way:
CREATE TABLE IF NOT EXISTS eicher_motors LIKE bajaj_auto;   -- data/Eicher_Motors.csv
CREATE TABLE IF NOT EXISTS hero_motocorp LIKE bajaj_auto;   -- data/Hero_Motocorp.csv
CREATE TABLE IF NOT EXISTS infosys       LIKE bajaj_auto;   -- data/Infosys.csv
CREATE TABLE IF NOT EXISTS tcs           LIKE bajaj_auto;   -- data/TCS.csv
CREATE TABLE IF NOT EXISTS tvs_motors    LIKE bajaj_auto;   -- data/TVS_Motors.csv


-- ### TASK 1 | How much history do we have?
SELECT COUNT(*) AS trading_days, MIN(date) AS first_day, MAX(date) AS last_day
FROM bajaj_auto;

-- ### TASK 2 | Eicher's five best closes
SELECT date, close_price FROM eicher_motors ORDER BY close_price DESC LIMIT 5;

-- ### TASK 3 | TCS, year by year
SELECT YEAR(date) AS year, ROUND(AVG(close_price), 2) AS avg_close
FROM tcs GROUP BY YEAR(date) ORDER BY year;

-- ### TASK 4 | Find the holes
SELECT 'bajaj_auto' AS stock, date FROM bajaj_auto WHERE deliverable_qty IS NULL
UNION ALL SELECT 'eicher_motors', date FROM eicher_motors WHERE deliverable_qty IS NULL
UNION ALL SELECT 'hero_motocorp', date FROM hero_motocorp WHERE deliverable_qty IS NULL
UNION ALL SELECT 'infosys',       date FROM infosys       WHERE deliverable_qty IS NULL
UNION ALL SELECT 'tcs',           date FROM tcs           WHERE deliverable_qty IS NULL
UNION ALL SELECT 'tvs_motors',    date FROM tvs_motors    WHERE deliverable_qty IS NULL;

-- ### TASK 5 | Moving averages -> bajaj1
DROP TABLE IF EXISTS bajaj1;
CREATE TABLE bajaj1 AS
SELECT date, close_price,
       CASE WHEN ROW_NUMBER() OVER (ORDER BY date) >= 20
            THEN ROUND(AVG(close_price) OVER (ORDER BY date ROWS BETWEEN 19 PRECEDING AND CURRENT ROW), 2) END AS ma20,
       CASE WHEN ROW_NUMBER() OVER (ORDER BY date) >= 50
            THEN ROUND(AVG(close_price) OVER (ORDER BY date ROWS BETWEEN 49 PRECEDING AND CURRENT ROW), 2) END AS ma50
FROM bajaj_auto;

-- ### TASK 6 | Master table
DROP TABLE IF EXISTS master_table;
CREATE TABLE master_table AS
SELECT b.date, b.close_price AS bajaj, t.close_price AS tcs, v.close_price AS tvs,
       i.close_price AS infosys, e.close_price AS eicher, h.close_price AS hero
FROM bajaj_auto b
JOIN tcs t           ON t.date = b.date
JOIN tvs_motors v    ON v.date = b.date
JOIN infosys i       ON i.date = b.date
JOIN eicher_motors e ON e.date = b.date
JOIN hero_motocorp h ON h.date = b.date;

-- ### TASK 7 | Golden-cross signals -> bajaj2   (`signal` is reserved in MySQL: backticks)
DROP TABLE IF EXISTS bajaj2;
CREATE TABLE bajaj2 AS
WITH t AS (
    SELECT date, close_price, ma20, ma50,
           LAG(ma20) OVER (ORDER BY date) AS prev_ma20,
           LAG(ma50) OVER (ORDER BY date) AS prev_ma50
    FROM bajaj1
)
SELECT date, close_price,
       CASE
           WHEN ma20 IS NULL OR ma50 IS NULL OR prev_ma20 IS NULL OR prev_ma50 IS NULL THEN 'Hold'
           WHEN ma20 > ma50 AND prev_ma20 <= prev_ma50 THEN 'Buy'
           WHEN ma20 < ma50 AND prev_ma20 >= prev_ma50 THEN 'Sell'
           ELSE 'Hold'
       END AS `signal`
FROM t;

-- ### TASK 8 | Signal counts
SELECT `signal`, COUNT(*) AS days FROM bajaj2 GROUP BY `signal` ORDER BY `signal`;

-- ### TASK 9 | Signal on a given day, as a reusable function
DROP FUNCTION IF EXISTS get_signal;
DELIMITER $$
CREATE FUNCTION get_signal(p_date DATE) RETURNS VARCHAR(10)
READS SQL DATA
BEGIN
    DECLARE s VARCHAR(10);
    SELECT `signal` INTO s FROM bajaj2 WHERE date = p_date;
    RETURN s;            -- NULL when the market was closed
END$$
DELIMITER ;
SELECT get_signal('2018-06-21') AS signal_on_day;

-- ### TASK 10 | All six stocks in one query
WITH prices AS (
    SELECT 'Bajaj Auto' AS stock, date, close_price FROM bajaj_auto    UNION ALL
    SELECT 'Eicher Motors',       date, close_price FROM eicher_motors UNION ALL
    SELECT 'Hero Motocorp',       date, close_price FROM hero_motocorp UNION ALL
    SELECT 'Infosys',             date, close_price FROM infosys       UNION ALL
    SELECT 'TCS',                 date, close_price FROM tcs           UNION ALL
    SELECT 'TVS Motors',          date, close_price FROM tvs_motors
),
ma AS (
    SELECT stock, date, close_price,
           CASE WHEN ROW_NUMBER() OVER (PARTITION BY stock ORDER BY date) >= 20
                THEN AVG(close_price) OVER (PARTITION BY stock ORDER BY date ROWS BETWEEN 19 PRECEDING AND CURRENT ROW) END AS ma20,
           CASE WHEN ROW_NUMBER() OVER (PARTITION BY stock ORDER BY date) >= 50
                THEN AVG(close_price) OVER (PARTITION BY stock ORDER BY date ROWS BETWEEN 49 PRECEDING AND CURRENT ROW) END AS ma50
    FROM prices
),
lagged AS (
    SELECT *, LAG(ma20) OVER (PARTITION BY stock ORDER BY date) AS prev_ma20,
              LAG(ma50) OVER (PARTITION BY stock ORDER BY date) AS prev_ma50
    FROM ma
),
sig AS (
    SELECT stock, date, close_price,
           CASE
               WHEN ma20 IS NULL OR ma50 IS NULL OR prev_ma20 IS NULL OR prev_ma50 IS NULL THEN 'Hold'
               WHEN ma20 > ma50 AND prev_ma20 <= prev_ma50 THEN 'Buy'
               WHEN ma20 < ma50 AND prev_ma20 >= prev_ma50 THEN 'Sell'
               ELSE 'Hold'
           END AS `signal`
    FROM lagged
),
latest AS (
    SELECT stock, date, `signal`,
           ROW_NUMBER() OVER (PARTITION BY stock ORDER BY date DESC) AS rn
    FROM sig WHERE `signal` <> 'Hold'
)
SELECT s.stock,
       SUM(s.`signal` = 'Buy')  AS buys,
       SUM(s.`signal` = 'Sell') AS sells,
       l.date                   AS last_signal_date,
       l.`signal`               AS last_signal
FROM sig s
JOIN latest l ON l.stock = s.stock AND l.rn = 1
GROUP BY s.stock, l.date, l.`signal`
ORDER BY s.stock;

-- ### TASK 11 | Who went up? (raw)
WITH prices AS (
    SELECT 'Bajaj Auto' AS stock, date, close_price FROM bajaj_auto    UNION ALL
    SELECT 'Eicher Motors',       date, close_price FROM eicher_motors UNION ALL
    SELECT 'Hero Motocorp',       date, close_price FROM hero_motocorp UNION ALL
    SELECT 'Infosys',             date, close_price FROM infosys       UNION ALL
    SELECT 'TCS',                 date, close_price FROM tcs           UNION ALL
    SELECT 'TVS Motors',          date, close_price FROM tvs_motors
),
ends AS (SELECT stock, MIN(date) AS first_day, MAX(date) AS last_day FROM prices GROUP BY stock)
SELECT e.stock, f.close_price AS first_close, l.close_price AS last_close,
       ROUND(100.0 * (l.close_price - f.close_price) / f.close_price, 1) AS pct_change
FROM ends e
JOIN prices f ON f.stock = e.stock AND f.date = e.first_day
JOIN prices l ON l.stock = e.stock AND l.date = e.last_day
ORDER BY pct_change DESC;

-- ### TASK 12 | The data trap: worst day per stock
WITH prices AS (
    SELECT 'Bajaj Auto' AS stock, date, close_price FROM bajaj_auto    UNION ALL
    SELECT 'Eicher Motors',       date, close_price FROM eicher_motors UNION ALL
    SELECT 'Hero Motocorp',       date, close_price FROM hero_motocorp UNION ALL
    SELECT 'Infosys',             date, close_price FROM infosys       UNION ALL
    SELECT 'TCS',                 date, close_price FROM tcs           UNION ALL
    SELECT 'TVS Motors',          date, close_price FROM tvs_motors
),
moves AS (
    SELECT stock, date, close_price,
           100.0 * (close_price / LAG(close_price) OVER (PARTITION BY stock ORDER BY date) - 1) AS pct_move
    FROM prices
),
ranked AS (
    SELECT *, ROW_NUMBER() OVER (PARTITION BY stock ORDER BY pct_move) AS rk
    FROM moves WHERE pct_move IS NOT NULL
)
SELECT stock, date, close_price, ROUND(pct_move, 1) AS pct_move
FROM ranked WHERE rk = 1 ORDER BY pct_move;

-- ### TASK 13 | Fix it: bonus-issue adjustment (Infosys 2015-06-15, TCS 2018-05-31)
WITH adjusted AS (
    SELECT 'TCS' AS stock, date,
           CASE WHEN date < '2018-05-31' THEN close_price / 2 ELSE close_price END AS adj_close FROM tcs
    UNION ALL
    SELECT 'Infosys', date,
           CASE WHEN date < '2015-06-15' THEN close_price / 2 ELSE close_price END FROM infosys
)
SELECT stock,
       ROUND(100.0 * (MAX(CASE WHEN date = '2018-07-31' THEN adj_close END) /
                      MAX(CASE WHEN date = '2015-01-01' THEN adj_close END) - 1), 1) AS adjusted_pct_change
FROM adjusted GROUP BY stock ORDER BY stock;
