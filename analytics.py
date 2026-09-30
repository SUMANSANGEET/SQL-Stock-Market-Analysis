"""Analytics shared by the notebook, the Streamlit app and the PDF report.
Everything here reads from tables produced by sql/analysis_sqlite.sql."""
import numpy as np
import pandas as pd
import stockdb

BONUS_EVENTS = {   # first trading day at the new (halved) price level, 1:1 bonus issue
    "Infosys": "2015-06-15",
    "TCS": "2018-05-31",
}


def prepared_connection():
    """In-memory DB with raw tables + every table created by the SQL file."""
    con = stockdb.build_connection()
    stockdb.run_all(con)
    return con


def prices(con, basis="adjusted") -> pd.DataFrame:
    col = "adj_close" if basis == "adjusted" else "raw_close"
    df = pd.read_sql_query(f"SELECT stock, date, {col} AS close FROM prices_adj ORDER BY date", con)
    df["date"] = pd.to_datetime(df["date"])
    return df


def wide(con, basis="adjusted") -> pd.DataFrame:
    return prices(con, basis).pivot(index="date", columns="stock", values="close")


def signals(con, basis="adjusted") -> pd.DataFrame:
    df = pd.read_sql_query("SELECT * FROM stock_signals WHERE price_basis = ? ORDER BY stock, date", con, params=(basis,))
    df["date"] = pd.to_datetime(df["date"])
    return df


def backtest_stock(sig: pd.DataFrame) -> dict:
    """Long-only golden-cross strategy on one stock's signal frame.
    Buy at the close of a Buy day, sell at the close of the next Sell day, flat otherwise."""
    s = sig.sort_values("date").reset_index(drop=True)
    pos = 0
    position = []
    for x in s["signal"]:
        if x == "Buy":
            pos = 1
        elif x == "Sell":
            pos = 0
        position.append(pos)
    s["position"] = position
    ret = s["close_price"].pct_change().fillna(0)
    # position decided at yesterday's close earns today's return (no look-ahead)
    s["strat_ret"] = ret * s["position"].shift(1).fillna(0)
    s["strat_eq"] = (1 + s["strat_ret"]).cumprod() * 100
    s["bh_eq"] = (1 + ret).cumprod() * 100
    trades = []
    entry = None
    for _, r in s.iterrows():
        if r["signal"] == "Buy":
            entry = r
        elif r["signal"] == "Sell" and entry is not None:
            trades.append((entry["date"], r["date"], r["close_price"] / entry["close_price"] - 1))
            entry = None
    wins = [t for t in trades if t[2] > 0]
    return {
        "frame": s,
        "strategy_pct": s["strat_eq"].iloc[-1] - 100,
        "buy_hold_pct": s["bh_eq"].iloc[-1] - 100,
        "closed_trades": len(trades),
        "win_rate": (len(wins) / len(trades) * 100) if trades else np.nan,
        "avg_trade_pct": (np.mean([t[2] for t in trades]) * 100) if trades else np.nan,
        "in_market_pct": s["position"].mean() * 100,
        "trades": trades,
    }


def backtest_all(con, basis="adjusted") -> pd.DataFrame:
    sg = signals(con, basis)
    rows = []
    for stock, g in sg.groupby("stock"):
        b = backtest_stock(g)
        rows.append({"stock": stock, **{k: b[k] for k in
                     ["strategy_pct", "buy_hold_pct", "closed_trades", "win_rate", "avg_trade_pct", "in_market_pct"]}})
    return pd.DataFrame(rows).sort_values("buy_hold_pct", ascending=False).reset_index(drop=True)


def max_drawdown(series: pd.Series) -> float:
    peak = series.cummax()
    return ((series / peak) - 1).min() * 100


def risk_table(con) -> pd.DataFrame:
    w = wide(con, "adjusted")
    r = w.pct_change().dropna()
    out = pd.DataFrame({
        "total_return_pct": (w.iloc[-1] / w.iloc[0] - 1) * 100,
        "ann_return_pct": ((w.iloc[-1] / w.iloc[0]) ** (252 / len(w)) - 1) * 100,
        "ann_vol_pct": r.std() * np.sqrt(252) * 100,
        "max_drawdown_pct": w.apply(max_drawdown),
    })
    out["return_per_risk"] = out["ann_return_pct"] / out["ann_vol_pct"]
    return out.sort_values("total_return_pct", ascending=False)


def current_trend(con, basis="raw") -> pd.DataFrame:
    """Latest non-Hold signal per stock -> 'shifting up/down' (deck wording)."""
    sg = signals(con, basis)
    sg = sg[sg["signal"] != "Hold"].sort_values("date").groupby("stock").tail(1)
    sg["trend"] = np.where(sg["signal"] == "Buy", "Shifting up", "Shifting down")
    return sg[["stock", "date", "signal", "trend"]].reset_index(drop=True)
