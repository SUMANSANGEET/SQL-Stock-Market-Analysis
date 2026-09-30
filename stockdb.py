"""Shared helpers: load the six NSE CSVs into an in-memory SQLite database.

Dates in the raw files look like '31-July-2018'. They are converted to ISO
'YYYY-MM-DD' text so that string sorting == chronological sorting (this is what
the student guide assumes for every query).
"""
from pathlib import Path
import sqlite3
import pandas as pd

DATA_DIR = Path(__file__).parent / "data"

# table name -> (display name, csv file, colour used in every chart)
STOCKS = {
    "bajaj_auto":    ("Bajaj Auto",    "Bajaj_Auto.csv",    "#1f77b4"),
    "eicher_motors": ("Eicher Motors", "Eicher_Motors.csv", "#ff7f0e"),
    "hero_motocorp": ("Hero Motocorp", "Hero_Motocorp.csv", "#2ca02c"),
    "infosys":       ("Infosys",       "Infosys.csv",       "#d62728"),
    "tcs":           ("TCS",           "TCS.csv",           "#9467bd"),
    "tvs_motors":    ("TVS Motors",    "TVS_Motors.csv",    "#8c564b"),
}
NAME_TO_TABLE = {v[0]: k for k, v in STOCKS.items()}
COLORS = {v[0]: v[2] for v in STOCKS.values()}

COLUMN_MAP = {
    "Date": "date", "Open Price": "open_price", "High Price": "high_price",
    "Low Price": "low_price", "Close Price": "close_price", "WAP": "wap",
    "No.of Shares": "no_of_shares", "No. of Trades": "no_of_trades",
    "Total Turnover (Rs.)": "total_turnover",
    "Deliverable Quantity": "deliverable_qty",
    "% Deli. Qty to Traded Qty": "pct_deli_qty",
    "Spread High-Low": "spread_high_low", "Spread Close-Open": "spread_close_open",
}


def load_csv(table: str) -> pd.DataFrame:
    _, fname, _ = STOCKS[table]
    df = pd.read_csv(DATA_DIR / fname).rename(columns=COLUMN_MAP)
    df["date"] = pd.to_datetime(df["date"], format="%d-%B-%Y").dt.strftime("%Y-%m-%d")
    return df.sort_values("date").reset_index(drop=True)


def build_connection(check_same_thread: bool = False) -> sqlite3.Connection:
    """Fresh in-memory SQLite DB with the six raw tables."""
    con = sqlite3.connect(":memory:", check_same_thread=check_same_thread)
    for table in STOCKS:
        load_csv(table).to_sql(table, con, index=False)
        con.execute(f"CREATE INDEX idx_{table}_date ON {table}(date)")
    return con


# ---------------------------------------------------------------------
# Running the tagged .sql file section by section
# ---------------------------------------------------------------------
import re

SQL_FILE = Path(__file__).parent / "sql" / "analysis_sqlite.sql"
_TAG = re.compile(r"^-- ### TASK (\S+) \| (.*)$", re.M)


def load_sections(path: Path = SQL_FILE) -> dict:
    """{task_id: {'title': str, 'sql': str}} in file order."""
    text = Path(path).read_text()
    marks = list(_TAG.finditer(text))
    out = {}
    for i, m in enumerate(marks):
        end = marks[i + 1].start() if i + 1 < len(marks) else len(text)
        body = text[m.end():end]
        body = re.split(r"\n-- =+\n", body)[0].strip()   # drop trailing banner comments
        out[m.group(1)] = {"title": m.group(2).strip(), "sql": body}
    return out


def split_statements(sql: str):
    """Split a script into complete statements (sqlite3-aware, handles comments)."""
    stmts, buf = [], ""
    for line in sql.splitlines(keepends=True):
        buf += line
        if sqlite3.complete_statement(buf):
            if buf.strip():
                stmts.append(buf.strip())
            buf = ""
    if buf.strip():
        stmts.append(buf.strip())
    return stmts


def run_section(con: sqlite3.Connection, sql: str) -> pd.DataFrame:
    """Execute every statement; return the result of the last SELECT (if any)."""
    result = pd.DataFrame()
    for stmt in split_statements(sql):
        body = re.sub(r"(?m)^\s*--.*$", "", stmt).strip()
        if not body:
            continue
        if re.match(r"(?is)^(with|select)\b", body) and not re.match(r"(?is)^with.*\binsert\b", body):
            result = pd.read_sql_query(stmt, con)
        else:
            con.execute(stmt)
    con.commit()
    return result


def run_all(con: sqlite3.Connection) -> dict:
    """Run the whole analysis file in order; returns {task_id: DataFrame}."""
    return {tid: run_section(con, sec["sql"]) for tid, sec in load_sections().items()}
