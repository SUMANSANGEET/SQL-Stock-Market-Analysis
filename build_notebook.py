import nbformat as nbf
nb = nbf.v4.new_notebook()
C = []
md = lambda s: C.append(nbf.v4.new_markdown_cell(s.strip()))
code = lambda s: C.append(nbf.v4.new_code_cell(s.strip()))

md("""
# Stock Market Analysis in SQL
### Moving averages, golden-cross signals and a data trap hiding in plain sight
**Data:** 6 NSE stocks (Bajaj Auto, Eicher Motors, Hero Motocorp, Infosys, TCS, TVS Motors), 889 trading days each, 1 Jan 2015 - 31 Jul 2018.
**Stack:** SQL (window functions, CTEs) for all analysis, Python/Plotly for interactive visuals, Streamlit for the live app.

---
## Executive summary
1. **Signals reproduced exactly.** 56 Buy / 57 Sell signals across the six stocks; the latest trend per stock matches the course deck.
2. **The data contains a trap.** TCS (31 May 2018) and Infosys (15 Jun 2015) each show a ~50% one-day "crash". Both are **1:1 bonus issues**, not losses.
3. **Adjusting flips the story.** Raw returns say TCS -23.8% and Infosys -30.9%. Adjusted for the bonus issues they are **+52.4%** and **+38.2%**.
4. **The recommendation changes too.** On adjusted prices TCS's latest signal is a *Buy* (20 Apr 2018), not the *Sell* the raw data produces.
5. **Signals did not beat buy-and-hold.** The 20/50-day golden-cross strategy trailed buy-and-hold on all six stocks in this window (no costs included).

> Every number below comes from a SQL query you can read in this notebook, or from `sql/analysis_sqlite.sql`.
""")

md("## 0. Setup\nThe CSVs are loaded into an in-memory SQLite database (dates converted from `31-July-2018` to ISO `2018-07-31` so text sorting equals time sorting). All analysis SQL lives in one tagged file and is executed section by section.")
code("""
import sys, pathlib
ROOT = pathlib.Path.cwd() if (pathlib.Path.cwd() / "stockdb.py").exists() else pathlib.Path.cwd().parent
sys.path.insert(0, str(ROOT))   # so `import stockdb` works when opened from notebooks/

import pandas as pd, numpy as np, plotly.express as px, plotly.graph_objects as go
from plotly.subplots import make_subplots
from IPython.display import display, Markdown
import plotly.io as pio
import stockdb, analytics as A

pio.renderers.default = "plotly_mimetype+notebook_connected"
pio.templates.default = "plotly_white"
pd.set_option("display.float_format", "{:,.2f}".format)

con = stockdb.build_connection()
SECTIONS = stockdb.load_sections()
COLORS = stockdb.COLORS

def task(tid, show_sql=True):
    \"\"\"Show the SQL for a task, run it, display the result and return it as a DataFrame.\"\"\"
    sec = SECTIONS[tid]
    display(Markdown(f"#### Task {tid} - {sec['title']}"))
    if show_sql:
        display(Markdown("```sql\\n" + sec["sql"] + "\\n```"))
    df = stockdb.run_section(con, sec["sql"])
    display(df)
    return df
""")

md("## 1. Get to know the data")
code("t1 = task('1')")
code("t2 = task('2')")
md("**Insight:** all five of Eicher's best closes fall in **September 2017**, the stock's peak (Rs 32,786 on 7 Sep 2017). It sits about 15% below that peak at the end of the data.")
code("t3 = task('3')")
md("2018 only contains seven months, so it should not be called the 'best year' on averages alone.")
code("t4 = task('4')")
md("Six rows on only **two dates** (9 Dec 2015 and 31 Aug 2017). Four different companies share one date, so the gap comes from the **exchange's reporting**, not the companies. It affects `deliverable_qty` only, never prices, so it does not touch the signals.")

md("## 2. Bajaj Auto: moving averages and golden-cross signals\nA **20-day** average reacts fast, a **50-day** average is slow. When the fast line crosses **above** the slow one (golden cross) momentum is turning up: **Buy**. Crossing **below** is a **Sell**.\nTwo details matter: windows are exactly 20 and 50 rows (`19/49 PRECEDING`), and the first 19/49 days are NULL because a partial window is not a real average.")
code("t5 = task('5')")
code("""
b = pd.read_sql_query("SELECT * FROM bajaj1", con, parse_dates=["date"])
print("rows:", len(b), "| first ma20:", b.dropna(subset=['ma20']).date.iloc[0].date(), "| first ma50:", b.dropna(subset=['ma50']).date.iloc[0].date())
""")
code("t7 = task('7')")
code("t8 = task('8')")
code("t9 = task('9')")
code("""
b2 = pd.read_sql_query("SELECT b.date, b.close_price, b.ma20, b.ma50, s.signal FROM bajaj1 b JOIN bajaj2 s USING(date)", con, parse_dates=["date"])
fig = go.Figure()
fig.add_scatter(x=b2.date, y=b2.close_price, name="Close", line=dict(color="#9aa0a6", width=1))
fig.add_scatter(x=b2.date, y=b2.ma20, name="20-day MA", line=dict(color="#1f77b4", width=2))
fig.add_scatter(x=b2.date, y=b2.ma50, name="50-day MA", line=dict(color="#ff7f0e", width=2))
for sig, sym, col in [("Buy","triangle-up","#0a8f3c"),("Sell","triangle-down","#d62728")]:
    d = b2[b2.signal == sig]
    fig.add_scatter(x=d.date, y=d.close_price, mode="markers", name=sig,
                    marker=dict(symbol=sym, size=13, color=col, line=dict(width=1, color="white")))
fig.update_layout(title="Bajaj Auto: price, 20/50-day averages and golden-cross signals", height=520,
                  yaxis_title="Rs", legend=dict(orientation="h", y=1.08), hovermode="x unified")
fig.show()
""")
md("**Insight:** 12 Buys and 11 Sells; the first Buy is 18 May 2015 and the latest is **21 Jun 2018**, so Bajaj's trend as of the end of the data is **up**. Buys and Sells alternate, so their counts can differ by at most one.")

md("## 3. Master table: all six stocks side by side")
code("t6 = task('6')")
code("""
m = pd.read_sql_query("SELECT * FROM master_table ORDER BY date", con, parse_dates=["date"]).set_index("date")
names = {"bajaj":"Bajaj Auto","tcs":"TCS","tvs":"TVS Motors","infosys":"Infosys","eicher":"Eicher Motors","hero":"Hero Motocorp"}
rebased = (m / m.iloc[0] * 100).rename(columns=names)
fig = px.line(rebased, color_discrete_map=COLORS, title="Raw closing prices rebased to 100 (1 Jan 2015) - note TCS and Infosys")
fig.update_layout(height=480, yaxis_title="Index (start = 100)", legend_title="", hovermode="x unified")
fig.show()
""")
md("TVS and Eicher finish highest. **TCS and Infosys** each fall off a cliff in one day. That picture is the setup for Part 5.")

md("## 4. All six stocks in one query\nOne chained-CTE query does everything: stack the tables, window per stock (`PARTITION BY stock`), lag, signal, latest non-Hold row per stock. It must reproduce the 56 Buy / 57 Sell totals.")
code("t10 = task('10')")
code("""
print("Total Buys:", t10.buys.sum(), "| Total Sells:", t10.sells.sum())
assert (t10.buys.sum(), t10.sells.sum()) == (56, 57)
""")

md("## 5. Who went up? And the data trap")
code("t11 = task('11')")
code("""
fig = px.bar(t11.sort_values("pct_change"), x="pct_change", y="stock", orientation="h", text="pct_change",
             color="pct_change", color_continuous_scale=["#d62728","#eeeeee","#0a8f3c"], color_continuous_midpoint=0,
             title="Raw % change, 1 Jan 2015 to 31 Jul 2018")
fig.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
fig.update_layout(height=380, coloraxis_showscale=False, xaxis_title="% change", yaxis_title="")
fig.show()
""")
md("Two negatives: TCS and Infosys, two of India's most consistently profitable companies. That should make you suspicious. **Task 12** looks for the single worst day per stock.")
code("t12 = task('12')")
code("""
fig = px.bar(t12.sort_values("pct_move", ascending=False), x="pct_move", y="stock", orientation="h", text="pct_move",
             color=(t12.sort_values("pct_move", ascending=False).pct_move < -20).map({True:"Not a real loss", False:"Normal bad day"}),
             color_discrete_map={"Not a real loss":"#d62728","Normal bad day":"#9aa0a6"},
             title="Worst single-day move per stock")
fig.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
fig.update_layout(height=380, legend_title="", xaxis_title="% one-day move", yaxis_title="")
fig.show()
""")
md("""
Four stocks have a worst day between -6% and -10%. **TCS (-50.4%)** and **Infosys (-49.9%)** are twice as bad as anything else and happened on days with no bad news. A search for the stock name plus *bonus issue* explains it:

| Stock | Event date (first day at new price) | Corporate action |
|---|---|---|
| Infosys | 2015-06-15 | 1:1 bonus issue (shares double, price halves) |
| TCS | 2018-05-31 | 1:1 bonus issue (shares double, price halves) |

Nobody lost anything: shareholders simply hold twice the shares at half the price. Any price series that is not adjusted will show a fake -50% crash on that day, which corrupts **returns, moving averages and signals** around it.
""")
code("""
zoom = []
for name, ev in A.BONUS_EVENTS.items():
    d = pd.read_sql_query(f"SELECT date, close_price FROM {stockdb.NAME_TO_TABLE[name]} WHERE date BETWEEN date('{ev}','-25 day') AND date('{ev}','+25 day')", con, parse_dates=["date"])
    d["stock"] = name; zoom.append(d)
zoom = pd.concat(zoom)
fig = px.line(zoom, x="date", y="close_price", facet_col="stock", markers=True, facet_col_spacing=0.08,
              title="The 'crash' that never happened: 50 days around each bonus issue")
fig.update_xaxes(matches=None); fig.update_yaxes(matches=None, showticklabels=True)
fig.update_layout(height=380)
fig.show()
""")

md("## 6. Fix it: adjust for the bonus issues\nDivide every price **before** the event date by 2. Prices on and after the event stay as they are.")
code("t13 = task('13')")
code("t_e1 = task('E1')")
code("""
raw = t11.set_index("stock")["pct_change"].rename("raw_pct")
adj = pd.read_sql_query(
    "SELECT stock, ROUND(100.0*(MAX(CASE WHEN date='2018-07-31' THEN adj_close END)/MAX(CASE WHEN date='2015-01-01' THEN adj_close END)-1),1) AS adjusted_pct FROM prices_adj GROUP BY stock", con
).set_index("stock")
cmp = pd.concat([raw, adj], axis=1).sort_values("adjusted_pct", ascending=False)
cmp["difference_pts"] = cmp.adjusted_pct - cmp.raw_pct
display(cmp)
long = cmp[["raw_pct","adjusted_pct"]].reset_index().melt("stock", var_name="basis", value_name="pct")
fig = px.bar(long, x="stock", y="pct", color="basis", barmode="group", text="pct",
             color_discrete_map={"raw_pct":"#bbbbbb","adjusted_pct":"#1f77b4"},
             title="Total return: raw vs bonus-adjusted")
fig.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
fig.update_layout(height=430, yaxis_title="% change", xaxis_title="", legend_title="")
fig.show()
""")
md("**Insight:** TCS moves from **-23.8% to +52.4%** and Infosys from **-30.9% to +38.2%**. The corrected ranking is TVS (+86.9%), Eicher (+82.6%), TCS (+52.4%), Infosys (+38.2%), Bajaj (+10.0%), Hero (+6.0%). No stock lost money over the period.")

code("""
adj_prices = A.wide(con, "adjusted"); raw_prices = A.wide(con, "raw")
fig = make_subplots(rows=1, cols=2, subplot_titles=("Raw (unadjusted)", "Bonus-adjusted"), shared_yaxes=False)
for s in adj_prices.columns:
    fig.add_scatter(x=raw_prices.index, y=raw_prices[s]/raw_prices[s].iloc[0]*100, name=s, legendgroup=s, line=dict(color=COLORS[s]), row=1, col=1)
    fig.add_scatter(x=adj_prices.index, y=adj_prices[s]/adj_prices[s].iloc[0]*100, name=s, legendgroup=s, showlegend=False, line=dict(color=COLORS[s]), row=1, col=2)
fig.update_layout(height=470, title="Rebased to 100: the same six stocks before and after the fix", hovermode="x unified")
fig.show()
""")

md("## 7. Does the fix change the signals?\nTask E2 recomputes every stock's signals on **raw** and **adjusted** prices (same SQL, one extra partition key).")
code("t_e2 = task('E2', show_sql=False)")
code("""
piv = t_e2.pivot(index="stock", columns="price_basis", values=["buys","sells"])
piv.columns = [f"{a}_{b}" for a, b in piv.columns]
display(piv)
trend_raw, trend_adj = A.current_trend(con, "raw"), A.current_trend(con, "adjusted")
tr = trend_raw.merge(trend_adj, on="stock", suffixes=("_raw","_adjusted"))
tr["changed"] = tr.trend_raw != tr.trend_adjusted
display(tr)
""")
md("""
- **TCS (raw):** the bonus-day drop drags the 20-day average under the 50-day and creates a **fake Sell** (13 Sells vs 12 Buys). Adjusted: 12 / 12, and the latest signal is a **Buy on 20 Apr 2018**.
- **Infosys (raw):** the 2015 bonus jump *hid* a real Buy and produced a fake Sell. Adjusted: 10 Buys / 10 Sells instead of 9 / 9. The latest signal (Buy, 7 May 2018) is unchanged.
- The other four stocks have no corporate action, so nothing changes.
""")
code("""
sg = A.signals(con, "adjusted"); sr = A.signals(con, "raw")
fig = make_subplots(rows=3, cols=2, subplot_titles=sorted(sg.stock.unique()), vertical_spacing=0.09)
for i, s in enumerate(sorted(sg.stock.unique())):
    r, c = i//2 + 1, i%2 + 1
    d = sg[sg.stock == s]
    fig.add_scatter(x=d.date, y=d.close_price, line=dict(color="#b0b0b0", width=1), showlegend=False, row=r, col=c)
    fig.add_scatter(x=d.date, y=d.ma20, line=dict(color="#1f77b4", width=1.5), showlegend=(i==0), name="20-day", row=r, col=c)
    fig.add_scatter(x=d.date, y=d.ma50, line=dict(color="#ff7f0e", width=1.5), showlegend=(i==0), name="50-day", row=r, col=c)
    for sig, sym, col in [("Buy","triangle-up","#0a8f3c"),("Sell","triangle-down","#d62728")]:
        e = d[d.signal == sig]
        fig.add_scatter(x=e.date, y=e.close_price, mode="markers", marker=dict(symbol=sym, size=8, color=col),
                        showlegend=(i==0), name=sig, row=r, col=c)
fig.update_layout(height=900, title="Golden-cross signals on bonus-adjusted prices, all six stocks", hovermode="closest")
fig.show()
""")

md("## 8. Did the signals actually make money?\nA long-only test: buy at the close of a Buy day, sell at the close of the next Sell day, cash in between. Each day's position is decided from the **previous** close (no look-ahead). No transaction costs or taxes are included, and it is a single in-sample period, so treat it as a sanity check rather than proof.")
code("""
bt = A.backtest_all(con, "adjusted")
display(bt.rename(columns={"strategy_pct":"golden_cross_%","buy_hold_pct":"buy_and_hold_%"}))
long = bt.melt("stock", ["strategy_pct","buy_hold_pct"], var_name="approach", value_name="pct")
long["approach"] = long.approach.map({"strategy_pct":"Golden-cross strategy","buy_hold_pct":"Buy and hold"})
fig = px.bar(long, x="stock", y="pct", color="approach", barmode="group", text="pct",
             color_discrete_map={"Golden-cross strategy":"#ff7f0e","Buy and hold":"#1f77b4"},
             title="Golden-cross strategy vs buy-and-hold (adjusted prices)")
fig.update_traces(texttemplate="%{text:.0f}%", textposition="outside")
fig.update_layout(height=430, legend_title="", xaxis_title="", yaxis_title="Total return %")
fig.show()
""")
code("""
sel = st_sel = "TCS"
fig = go.Figure()
res = {s: A.backtest_stock(g) for s, g in sg.groupby("stock")}
for s, r in res.items():
    f = r["frame"]
    fig.add_scatter(x=f.date, y=f.strat_eq, name=s, legendgroup=s, line=dict(color=COLORS[s], width=2))
    fig.add_scatter(x=f.date, y=f.bh_eq, name=s+" (buy & hold)", legendgroup=s, line=dict(color=COLORS[s], width=1, dash="dot"), visible="legendonly")
fig.update_layout(title="Strategy equity curves (start = 100). Click legend to toggle buy-and-hold lines", height=480, hovermode="x unified")
fig.show()
""")
md("""
**Insight:** the strategy lagged buy-and-hold on **all six** stocks. Eicher's trades all won (6 of 6) yet it still trailed, because it was out of the market roughly half the time during a strong uptrend. TCS is the starkest case: buy-and-hold **+52%** vs strategy **-22%**, with only 2 of 11 trades profitable. Moving-average crossovers lag price, so in choppy or steadily rising markets they buy late and sell late.
""")

md("## 9. Risk and diversification")
code("""
rk = A.risk_table(con)
display(rk)
fig = px.scatter(rk.reset_index(), x="ann_vol_pct", y="ann_return_pct", size=rk.max_drawdown_pct.abs().values, color="stock",
                 color_discrete_map=COLORS, text="stock", title="Risk vs return (bubble size = max drawdown)")
fig.update_traces(textposition="top center")
fig.update_layout(height=470, xaxis_title="Annualised volatility %", yaxis_title="Annualised return %", showlegend=False)
fig.show()
""")
code("""
corr = adj_prices.pct_change().dropna().corr()
fig = px.imshow(corr.round(2), text_auto=True, color_continuous_scale="RdBu_r", zmin=-1, zmax=1,
                title="Correlation of daily returns (bonus-adjusted)")
fig.update_layout(height=480)
fig.show()
""")
md("""
**Insight:** Eicher and TVS delivered the highest returns but also the deepest drawdowns (-28% / -35%). TCS delivered the third-highest return with the lowest volatility of the six (21.6% annualised) and a shallower drawdown (-24%); its return per unit of risk (0.59) is close to Eicher's (0.64) and TVS's (0.63). Correlations are low (0.1-0.5), especially between the IT names (TCS, Infosys) and the auto names, so a mix of the two groups diversifies.
""")

md("## 10. Reconciling with the course deck")
code("""
tr_raw = A.current_trend(con, "raw").set_index("stock")
sig_counts = t10.set_index("stock")
deck = pd.DataFrame([
    ("Eicher Motors", 6, 7, "2018-06-06", "Shifting down", 82.5),
    ("Bajaj Auto",   12, 11, "2018-06-21", "Shifting up", 10.0),
    ("TCS",          12, 13, "2018-06-05", "Shifting down", -23.8),
    ("TVS Motors",    8,  8, "2018-05-17", "Shifting down", 86.9),
    ("Hero Motocorp", 9,  9, "2018-05-22", "Shifting down", 6.0),
    ("Infosys",       9,  9, "2018-05-07", "Shifting up", -3.0),
], columns=["stock","deck_buys","deck_sells","deck_date","deck_trend","deck_pct"]).set_index("stock")
out = deck.join(sig_counts[["buys","sells"]]).join(tr_raw[["date","trend"]]).join(t11.set_index("stock")["pct_change"].rename("sql_pct"))
out["signals_match"] = (out.deck_buys == out.buys) & (out.deck_sells == out.sells)
out["trend_match"] = (out.deck_date == out.date.dt.strftime("%Y-%m-%d")) & (out.deck_trend == out.trend)
out["pct_match"] = (out.deck_pct - out.sql_pct).abs() <= 0.11
display(out[["deck_buys","buys","deck_sells","sells","signals_match","trend_match","deck_pct","sql_pct","pct_match"]])
""")
md("""
**Signals, dates and trends match the deck for all six stocks.** Two of the deck's *percent-change lines* do not:
- **Infosys** is printed as "3% decrease"; the data gives **-30.9%** (a dropped digit).
- **TCS** lists 2548.20 as the 31 Jul 2018 close and 2454.1 as the 1 Jan 2015 close. In the data, 2548.20 is TCS's **1 Jan 2015** close, 1941.25 is the 31 Jul 2018 close, and 2454.1 is *Bajaj's* 1 Jan 2015 close (copied from the wrong row). The -23.8% figure itself is right.
- Eicher's 82.5% is 82.56% truncated instead of rounded (82.6%).

More importantly, the deck's final call rests on **raw** prices. See the recommendation below.
""")

md("""
## 11. Recommendation
| Stock | Latest signal (raw, as in deck) | Latest signal (bonus-adjusted) | Adjusted total return | Verdict |
|---|---|---|---|---|
| Bajaj Auto | Buy, 21 Jun 2018 | Buy, 21 Jun 2018 | +10.0% | **Buy** (trend up, modest history) |
| Infosys | Buy, 7 May 2018 | Buy, 7 May 2018 | +38.2% | **Buy** |
| TCS | Sell, 5 Jun 2018 | **Buy, 20 Apr 2018** | +52.4% | **Deck says Sell; adjusted data says Buy** |
| Eicher Motors | Sell, 6 Jun 2018 | Sell, 6 Jun 2018 | +82.6% | **Sell / reduce** (trend down after a 2017 peak) |
| TVS Motors | Sell, 17 May 2018 | Sell, 17 May 2018 | +86.9% | **Sell / reduce** |
| Hero Motocorp | Sell, 22 May 2018 | Sell, 22 May 2018 | +6.0% | **Sell** |

**Bottom line:** buy Bajaj Auto, Infosys and (after correcting the data) TCS; sell or reduce Eicher, TVS and Hero. The deck's "sell TCS" is an artefact of an unadjusted bonus issue.

### Limitations and next steps
- Moving-average signals are lagging indicators. In this window they **underperformed buy-and-hold on all six stocks**, so treat them as one input, not a standalone strategy.
- 3.6 years of data, one market regime, no transaction costs or taxes; results are illustrative, not investment advice.
- Only close prices are used. Volume, delivery percentage and volatility filters are natural next steps.
- Bonus adjustments were found from price behaviour and confirmed by name; a production pipeline should load a corporate-actions table (splits, bonuses, dividends) instead of hard-coding two dates.
""")

nb["cells"] = C
nb.metadata["kernelspec"] = {"display_name": "Python 3", "language": "python", "name": "python3"}
nbf.write(nb, "notebooks/Stock_Market_SQL_Analysis.ipynb")
print("cells:", len(C))
