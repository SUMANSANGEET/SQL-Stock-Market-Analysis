"""Safe, per-session SQL sandbox used by the Streamlit playground.

* Each visitor gets a private in-memory copy of the database (nothing is written to disk).
* An authorizer blocks ATTACH/DETACH/PRAGMA and extension loading.
* A progress handler aborts any query that runs longer than TIME_LIMIT seconds.
"""
import re
import sqlite3
import time
import numpy as np
import pandas as pd
import stockdb

TIME_LIMIT = 6.0
MAX_ROWS = 5000

_DENIED = {sqlite3.SQLITE_ATTACH, sqlite3.SQLITE_DETACH, sqlite3.SQLITE_PRAGMA}


def _authorizer(action, arg1, arg2, dbname, source):
    if action in _DENIED:
        return sqlite3.SQLITE_DENY
    if action == sqlite3.SQLITE_FUNCTION and str(arg2).lower() in {"load_extension", "readfile", "writefile"}:
        return sqlite3.SQLITE_DENY
    return sqlite3.SQLITE_OK


def snapshot_bytes(con: sqlite3.Connection):
    """Serialized copy of a prepared database (Python 3.11+), else None."""
    return con.serialize() if hasattr(con, "serialize") else None


def new_session_db(snapshot: bytes | None, with_analysis_tables: bool = True) -> sqlite3.Connection:
    """Private DB for one visitor. `with_analysis_tables=False` gives the six raw tables only."""
    if with_analysis_tables and snapshot is not None:
        con = sqlite3.connect(":memory:", check_same_thread=False)
        con.deserialize(snapshot)
    else:
        con = stockdb.build_connection()
        if with_analysis_tables:
            stockdb.run_all(con)
    con.set_authorizer(_authorizer)
    return con


def execute(con: sqlite3.Connection, sql: str):
    """Run a script; returns (DataFrame | None, message, seconds). Never raises."""
    t0 = time.time()
    con.set_progress_handler(lambda: 1 if time.time() - t0 > TIME_LIMIT else 0, 10000)
    df, msg = None, ""
    try:
        for stmt in stockdb.split_statements(sql):
            body = re.sub(r"(?m)^\s*--.*$", "", stmt).strip()
            if not body:
                continue
            cur = con.execute(stmt)
            if cur.description is not None:
                cols = [d[0] for d in cur.description]
                rows = cur.fetchmany(MAX_ROWS + 1)
                df = pd.DataFrame(rows[:MAX_ROWS], columns=cols)
                msg = f"{len(df):,} row(s)" + (f" (truncated to first {MAX_ROWS:,})" if len(rows) > MAX_ROWS else "")
            else:
                msg = "Statement executed" + (f" ({cur.rowcount} rows affected)" if cur.rowcount and cur.rowcount > 0 else "")
        con.commit()
    except sqlite3.OperationalError as e:
        text = str(e)
        if "interrupted" in text:
            text = f"Query stopped: it ran longer than {TIME_LIMIT:.0f}s."
        return None, f"Error: {text}", time.time() - t0
    except sqlite3.Error as e:
        return None, f"Error: {e}", time.time() - t0
    finally:
        con.set_progress_handler(None, 0)
    return df, msg, time.time() - t0


# ---------------------------------------------------------------------
# Practice mode: "Check answer" without revealing the solution
# ---------------------------------------------------------------------
# task -> (kind, what to compare).  'select' compares the query result;
# 'table' compares SELECT * FROM <table> in the learner's own database.
PRACTICE = {
    "1":  ("select", "Trading days, first and last date of Bajaj Auto"),
    "2":  ("select", "Eicher's five highest closes"),
    "3":  ("select", "TCS average close by year"),
    "4":  ("select", "Rows with missing deliverable_qty, all six tables"),
    "5":  ("table", "bajaj1", "Create table bajaj1 (date, close_price, ma20, ma50)"),
    "6":  ("table", "master_table", "Create master_table (date, bajaj, tcs, tvs, infosys, eicher, hero)"),
    "7":  ("table", "bajaj2", "Create table bajaj2 (date, close_price, signal)"),
    "8":  ("select", "Signal counts for Bajaj"),
    "9":  ("select", "Signal on 2018-06-21"),
    "10": ("select", "Buys, sells, last signal for all six stocks"),
    "11": ("select", "First/last close and % change per stock"),
    "12": ("select", "Worst day per stock"),
    "13": ("select", "Adjusted % change for TCS and Infosys"),
}


def _norm(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out.columns = [str(c).lower() for c in out.columns]
    for c in out.columns:
        if pd.api.types.is_numeric_dtype(out[c]):
            out[c] = out[c].astype(float).round(2)
        else:
            out[c] = out[c].astype(str)
    return out.reset_index(drop=True)


def compare(user: pd.DataFrame | None, ref: pd.DataFrame) -> tuple[bool, str]:
    if user is None or user.empty and not ref.empty:
        return False, "Your query returned no result table. Finish with a SELECT."
    if list(map(str.lower, map(str, user.columns))) != list(map(str.lower, ref.columns)):
        return False, f"Column names/order differ. Expected: {', '.join(ref.columns)}"
    if len(user) != len(ref):
        return False, f"Expected {len(ref):,} row(s), got {len(user):,}."
    u, r = _norm(user), _norm(ref)
    for c in r.columns:
        if pd.api.types.is_float_dtype(r[c]):
            ok = np.allclose(u[c].to_numpy(dtype=float), r[c].to_numpy(dtype=float), atol=0.011, equal_nan=True)
        else:
            ok = (u[c] == r[c]).all()
        if not ok:
            return False, f"Column '{c}' has values that do not match the expected result."
    return True, "Correct! Your result matches the expected answer."


def check_answer(tid: str, user_df, con: sqlite3.Connection, reference: dict) -> tuple[bool, str]:
    spec = PRACTICE[tid]
    if spec[0] == "table":
        try:
            user_df = pd.read_sql_query(f"SELECT * FROM {spec[1]} ORDER BY date", con)
        except Exception:
            return False, f"Table {spec[1]} does not exist yet. Create it first."
        ref = reference[f"table:{spec[1]}"]
    else:
        ref = reference[tid]
    return compare(user_df, ref)


def build_reference(con_prepared: sqlite3.Connection) -> dict:
    """Reference answers from the verified SQL file (run once, cached by the app)."""
    ref = {tid: stockdb.run_section(con_prepared, sec["sql"]) for tid, sec in stockdb.load_sections().items()
           if tid in PRACTICE and PRACTICE[tid][0] == "select"}
    for tid, spec in PRACTICE.items():
        if spec[0] == "table":
            ref[f"table:{spec[1]}"] = pd.read_sql_query(f"SELECT * FROM {spec[1]} ORDER BY date", con_prepared)
    return ref
