"""Builds report/Stock_Market_SQL_Insights.pdf from the SQL-derived data."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
import pandas as pd
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (BaseDocTemplate, Frame, Image, KeepTogether, PageBreak, PageTemplate,
                                Paragraph, Spacer, Table, TableStyle)
import analytics as A, stockdb

con = A.prepared_connection()
COL = stockdb.COLORS
plt.rcParams.update({"font.size": 9, "axes.spines.top": False, "axes.spines.right": False, "axes.grid": True,
                     "grid.alpha": .25, "figure.dpi": 170})

raw_w, adj_w = A.wide(con, "raw"), A.wide(con, "adjusted")
sg_adj, sg_raw = A.signals(con, "adjusted"), A.signals(con, "raw")
t10 = stockdb.run_section(con, stockdb.load_sections()["10"]["sql"]).set_index("stock")
t11 = stockdb.run_section(con, stockdb.load_sections()["11"]["sql"]).set_index("stock")
t12 = stockdb.run_section(con, stockdb.load_sections()["12"]["sql"])
bt = A.backtest_all(con, "adjusted")
rk = A.risk_table(con)
tot_raw = (raw_w.iloc[-1] / raw_w.iloc[0] - 1) * 100
tot_adj = (adj_w.iloc[-1] / adj_w.iloc[0] - 1) * 100
tr_raw = A.current_trend(con, "raw").set_index("stock")
tr_adj = A.current_trend(con, "adjusted").set_index("stock")
ASSETS = "assets/"

# ------------------------------------------------------------------ charts
def save(fig, name):
    fig.tight_layout(); fig.savefig(ASSETS + name, bbox_inches="tight"); plt.close(fig)

# 1 Bajaj golden cross
d = sg_adj[sg_adj.stock == "Bajaj Auto"]
fig, ax = plt.subplots(figsize=(7.4, 3.4))
ax.plot(d.date, d.close_price, color="#b0b0b0", lw=.9, label="Close")
ax.plot(d.date, d.ma20, color="#1f77b4", lw=1.6, label="20-day MA")
ax.plot(d.date, d.ma50, color="#ff7f0e", lw=1.6, label="50-day MA")
for s, m, c in [("Buy", "^", "#0a8f3c"), ("Sell", "v", "#d62728")]:
    e = d[d.signal == s]; ax.scatter(e.date, e.close_price, marker=m, s=46, color=c, zorder=5, label=s, edgecolor="white", lw=.6)
ax.set_ylabel("Rs"); ax.legend(ncol=5, loc="upper center", bbox_to_anchor=(.5, 1.13), frameon=False)
ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
save(fig, "r_bajaj.png")

# 2 raw vs adjusted rebased
fig, axs = plt.subplots(1, 2, figsize=(7.4, 3.0), sharey=True)
for ax, w, t in [(axs[0], raw_w, "Raw prices"), (axs[1], adj_w, "Bonus-adjusted prices")]:
    for s in w.columns:
        ax.plot(w.index, w[s] / w[s].iloc[0] * 100, color=COL[s], lw=1.3, label=s)
    ax.set_title(t, fontsize=9, loc="left"); ax.axhline(100, color="#888", lw=.6, ls="--")
    ax.xaxis.set_major_locator(mdates.YearLocator()); ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
axs[0].set_ylabel("Index (1 Jan 2015 = 100)")
axs[1].legend(fontsize=7, frameon=False, loc="upper left")
save(fig, "r_rebased.png")

# 3 worst day + zoom
fig, axs = plt.subplots(1, 3, figsize=(7.4, 2.7), gridspec_kw={"width_ratios": [1.15, 1, 1]})
w = t12.sort_values("pct_move", ascending=False)
axs[0].barh(w.stock, w.pct_move, color=["#d62728" if v < -20 else "#9aa0a6" for v in w.pct_move])
for i, v in enumerate(w.pct_move): axs[0].text(v - 1, i, f"{v:.1f}%", va="center", ha="right", fontsize=7)
axs[0].set_xlim(-65, 0); axs[0].set_title("Worst day per stock", fontsize=9, loc="left"); axs[0].grid(False)
for ax, (name, ev) in zip(axs[1:], A.BONUS_EVENTS.items()):
    e = pd.Timestamp(ev); m = (raw_w.index >= e - pd.Timedelta(days=40)) & (raw_w.index <= e + pd.Timedelta(days=40))
    ax.plot(raw_w.index[m], raw_w[name][m], color="#d62728", marker="o", ms=2.5, lw=1, label="Raw")
    ax.plot(adj_w.index[m], adj_w[name][m], color="#1f77b4", marker="o", ms=2.5, lw=1, label="Adjusted")
    ax.axvline(e, color="#666", ls="--", lw=.8); ax.set_title(f"{name}: bonus {e:%d %b %Y}", fontsize=8, loc="left")
    ax.xaxis.set_major_locator(mdates.AutoDateLocator(maxticks=3)); ax.xaxis.set_major_formatter(mdates.DateFormatter("%d %b")); ax.tick_params(axis="x", labelsize=7, rotation=30)
axs[1].legend(fontsize=7, frameon=False)
save(fig, "r_trap.png")

# 4 returns raw vs adjusted
order = tot_adj.sort_values(ascending=False).index
fig, ax = plt.subplots(figsize=(7.4, 2.9)); x = np.arange(len(order)); wd = .38
b1 = ax.bar(x - wd/2, tot_raw[order], wd, color="#c9c9c9", label="Raw"); b2 = ax.bar(x + wd/2, tot_adj[order], wd, color="#1f77b4", label="Adjusted")
for b in list(b1) + list(b2):
    h = b.get_height(); ax.text(b.get_x() + b.get_width()/2, h + (2 if h >= 0 else -9), f"{h:.1f}%", ha="center", fontsize=7)
ax.axhline(0, color="#444", lw=.8); ax.set_xticks(x); ax.set_xticklabels(order, fontsize=8); ax.set_ylabel("Total return %"); ax.legend(frameon=False)
ax.set_ylim(min(tot_raw.min(), 0) - 15, tot_adj.max() + 15)
save(fig, "r_returns.png")

# 5 backtest
b = bt.set_index("stock").loc[order]
fig, ax = plt.subplots(figsize=(7.4, 2.9))
b1 = ax.bar(x - wd/2, b.buy_hold_pct, wd, color="#1f77b4", label="Buy and hold"); b2 = ax.bar(x + wd/2, b.strategy_pct, wd, color="#ff7f0e", label="Golden-cross strategy")
for bar in list(b1) + list(b2):
    h = bar.get_height(); ax.text(bar.get_x() + bar.get_width()/2, h + (2 if h >= 0 else -9), f"{h:.0f}%", ha="center", fontsize=7)
ax.axhline(0, color="#444", lw=.8); ax.set_xticks(x); ax.set_xticklabels(order, fontsize=8); ax.set_ylabel("Total return %"); ax.legend(frameon=False)
ax.set_ylim(-35, 105)
save(fig, "r_bt.png")

# 6 risk scatter + correlation
fig, axs = plt.subplots(1, 2, figsize=(7.4, 3.1), gridspec_kw={"width_ratios": [1.2, 1]})
for s, r in rk.iterrows():
    axs[0].scatter(r.ann_vol_pct, r.ann_return_pct, s=abs(r.max_drawdown_pct) * 9, color=COL[s], alpha=.85)
    off = {"Hero Motocorp": (0, -16), "Bajaj Auto": (26, 6), "Eicher Motors": (-8, -17), "TVS Motors": (0, 13)}.get(s, (0, 11))
    axs[0].annotate(s, (r.ann_vol_pct, r.ann_return_pct), textcoords="offset points", xytext=off, ha="center", fontsize=7)
axs[0].set_xlabel("Annualised volatility %"); axs[0].set_ylabel("Annualised return %"); axs[0].set_title("Risk vs return (size = max drawdown)", fontsize=8, loc="left")
axs[0].set_xlim(19, 33); axs[0].set_ylim(-1, 23)
corr = adj_w.pct_change().dropna().corr(); im = axs[1].imshow(corr, cmap="RdBu_r", vmin=-1, vmax=1)
axs[1].set_xticks(range(6)); axs[1].set_yticks(range(6))
short = [c.split()[0] for c in corr.columns]; axs[1].set_xticklabels(short, rotation=45, ha="right", fontsize=7); axs[1].set_yticklabels(short, fontsize=7)
for i in range(6):
    for j in range(6): axs[1].text(j, i, f"{corr.iloc[i, j]:.2f}", ha="center", va="center", fontsize=6.5, color="white" if abs(corr.iloc[i, j]) > .6 else "black")
axs[1].grid(False); axs[1].set_title("Daily-return correlation", fontsize=8, loc="left")
save(fig, "r_risk.png")

# 7 TCS raw vs adjusted signals (zoom on 2018)
fig, axs = plt.subplots(1, 2, figsize=(7.4, 2.9), sharey=False)
for ax, sgx, ttl in [(axs[0], sg_raw, "TCS on raw prices"), (axs[1], sg_adj, "TCS on bonus-adjusted prices")]:
    d = sgx[(sgx.stock == "TCS") & (sgx.date >= "2018-02-01")]
    ax.plot(d.date, d.close_price, color="#b0b0b0", lw=.9); ax.plot(d.date, d.ma20, color="#1f77b4", lw=1.5, label="20-day MA"); ax.plot(d.date, d.ma50, color="#ff7f0e", lw=1.5, label="50-day MA")
    for sname, m, c in [("Buy", "^", "#0a8f3c"), ("Sell", "v", "#d62728")]:
        e = d[d.signal == sname]; ax.scatter(e.date, e.close_price, marker=m, s=55, color=c, zorder=5, edgecolor="white", lw=.6, label=sname)
        for _, r in e.iterrows(): ax.annotate(f"{sname} {r.date:%d %b}", (r.date, r.close_price), textcoords="offset points", xytext=(0, 10) if sname == "Buy" else (26, -3), ha="center", fontsize=7, color=c)
    ax.axvline(pd.Timestamp("2018-05-31"), color="#666", ls="--", lw=.8); ax.set_title(ttl, fontsize=9, loc="left")
    ax.xaxis.set_major_locator(mdates.MonthLocator()); ax.xaxis.set_major_formatter(mdates.DateFormatter("%b")); ax.set_ylabel("Rs")
axs[0].legend(fontsize=7, frameon=False, loc="lower left")
save(fig, "r_tcs_signals.png")

# ------------------------------------------------------------------ document
ss = getSampleStyleSheet()
NAVY, GREY = colors.HexColor("#14213d"), colors.HexColor("#5b6472")
H1 = ParagraphStyle("H1", parent=ss["Heading1"], fontName="Helvetica-Bold", fontSize=15, textColor=NAVY, spaceBefore=4, spaceAfter=6)
H2 = ParagraphStyle("H2", parent=ss["Heading2"], fontName="Helvetica-Bold", fontSize=11, textColor=NAVY, spaceBefore=8, spaceAfter=3)
BODY = ParagraphStyle("B", parent=ss["BodyText"], fontName="Helvetica", fontSize=9, leading=12.5, alignment=TA_LEFT, spaceAfter=4)
SMALL = ParagraphStyle("S", parent=BODY, fontSize=7.5, leading=10, textColor=GREY)
BUL = ParagraphStyle("BUL", parent=BODY, leftIndent=12, bulletIndent=2, spaceAfter=2)
CELL = ParagraphStyle("C", parent=BODY, fontSize=8, leading=10, spaceAfter=0)
CELLB = ParagraphStyle("CB", parent=CELL, fontName="Helvetica-Bold")
TITLE = ParagraphStyle("T", parent=H1, fontSize=22, leading=26, spaceAfter=2)
SUB = ParagraphStyle("SUB", parent=BODY, fontSize=10.5, textColor=GREY, leading=14)

def bullets(items): return [Paragraph(t, BUL, bulletText="\u2022") for t in items]
def img(name, w=17): 
    from PIL import Image as PI
    iw, ih = PI.open(ASSETS + name).size
    return Image(ASSETS + name, width=w * cm, height=w * cm * ih / iw)
def table(data, widths, hdr=NAVY, zebra=True, extra=None, pad=3.5):
    t = Table(data, colWidths=[w * cm for w in widths], repeatRows=1)
    st = [("BACKGROUND", (0, 0), (-1, 0), hdr), ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
          ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"), ("FONTSIZE", (0, 0), (-1, -1), 8),
          ("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("GRID", (0, 0), (-1, -1), .25, colors.HexColor("#d5d9e0")),
          ("TOPPADDING", (0, 0), (-1, -1), pad), ("BOTTOMPADDING", (0, 0), (-1, -1), pad)]
    if zebra: st += [("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f4f6fa")])]
    t.setStyle(TableStyle(st + (extra or []))); return t

def footer(canvas, doc):
    canvas.saveState(); canvas.setFont("Helvetica", 7.5); canvas.setFillColor(GREY)
    canvas.drawString(2 * cm, 1.1 * cm, "Stock Market Analysis in SQL  |  Educational analysis, not investment advice")
    canvas.drawRightString(A4[0] - 2 * cm, 1.1 * cm, f"Page {doc.page}")
    canvas.setStrokeColor(colors.HexColor("#d5d9e0")); canvas.line(2 * cm, 1.5 * cm, A4[0] - 2 * cm, 1.5 * cm); canvas.restoreState()

doc = BaseDocTemplate("report/Stock_Market_SQL_Insights.pdf", pagesize=A4, leftMargin=2 * cm, rightMargin=2 * cm,
                      topMargin=1.8 * cm, bottomMargin=2 * cm, title="Stock Market Analysis in SQL: Insights",
                      author="Data Analytics Project", subject="SQL analysis of six NSE stocks, 2015-2018")
doc.addPageTemplates([PageTemplate(id="p", frames=[Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="f")], onPage=footer)])
S = []

# ---- page 1: summary
S += [Paragraph("Stock Market Analysis in SQL", TITLE),
      Paragraph("Golden-cross signals on six NSE stocks, and the data trap that changes the answer", SUB),
      Paragraph("Data: Bajaj Auto, Eicher Motors, Hero Motocorp, Infosys, TCS, TVS Motors | 889 trading days each | 1 Jan 2015 to 31 Jul 2018 | Tools: SQL (window functions, CTEs), Python, Streamlit", SMALL),
      Spacer(1, 8), Paragraph("Executive summary", H1)]
S += bullets([
    "<b>Signals reproduced exactly.</b> A 20/50-day golden-cross rule gives <b>56 Buy and 57 Sell</b> signals across the six stocks. Counts, latest-signal dates and trends all match the course deck.",
    "<b>The data hides a trap.</b> TCS (31 May 2018) and Infosys (15 Jun 2015) each show a one-day drop of about 50%. Both are <b>1:1 bonus issues</b>: the share count doubled and the price halved. No value was lost.",
    f"<b>Adjusting reverses two conclusions.</b> Raw returns say TCS {tot_raw['TCS']:.1f}% and Infosys {tot_raw['Infosys']:.1f}%. Adjusted, they are <b>{tot_adj['TCS']:+.1f}%</b> and <b>{tot_adj['Infosys']:+.1f}%</b>. No stock lost money over the period.",
    "<b>The TCS call flips.</b> On raw prices TCS's latest signal is a Sell (5 Jun 2018). On adjusted prices it is a <b>Buy (20 Apr 2018)</b>. The deck's 'sell TCS' is an artefact of the unadjusted bonus issue.",
    "<b>Signals did not beat buy-and-hold.</b> The strategy trailed buy-and-hold on all six stocks (no costs included). Treat crossovers as one input, not a standalone system."])
S.append(Spacer(1, 6))
rows = [["Stock", "Raw return", "Adjusted return", "Latest signal (adjusted)", "Verdict"]]
verdict = {"Bajaj Auto": "Buy", "Infosys": "Buy", "TCS": "Buy (deck: Sell)", "Eicher Motors": "Sell / reduce", "TVS Motors": "Sell / reduce", "Hero Motocorp": "Sell"}
for s in order:
    t = tr_adj.loc[s]; rows.append([s, f"{tot_raw[s]:+.1f}%", f"{tot_adj[s]:+.1f}%", f"{t.signal}, {t.date:%d %b %Y}", verdict[s]])
extra = [("TEXTCOLOR", (4, i), (4, i), colors.HexColor("#0a8f3c") if rows[i][4].startswith("Buy") else colors.HexColor("#c0392b")) for i in range(1, 7)]
extra += [("FONTNAME", (4, 1), (4, -1), "Helvetica-Bold")]
S += [table(rows, [3.3, 2.6, 3.0, 4.6, 3.5], extra=extra), Spacer(1, 4),
      Paragraph("Verdicts follow the latest golden-cross direction on adjusted prices. Sell / reduce for Eicher and TVS is a trend call, not a value call: both have the highest 3.6-year returns.", SMALL),
      Spacer(1, 6), img("r_rebased.png", 16.6)]
S.append(PageBreak())

# ---- page 2: method + Bajaj
S += [Paragraph("1. Method: moving averages and golden-cross signals", H1),
      Paragraph("All analysis is written in SQL. Each stock's close price is smoothed with a <b>20-day</b> and a <b>50-day</b> moving average using window functions "
                "(<font face='Courier'>AVG() OVER (... ROWS BETWEEN 19 PRECEDING AND CURRENT ROW)</font>). The averages stay empty until a full window exists, "
                "because a partial window is not a real average and would create fake signals.", BODY),
      Paragraph("A <b>Buy</b> is issued on the single day the 20-day average moves from at-or-below to above the 50-day average; a <b>Sell</b> on the reverse. "
                "A crossover is about <i>two days</i> (today and yesterday, via <font face='Courier'>LAG()</font>), not one; testing only today would mark hundreds of days as Buy.", BODY),
      img("r_bajaj.png", 16.6),
      Paragraph("Bajaj Auto: 12 Buys and 11 Sells. First Buy 18 May 2015, first Sell 24 Aug 2015, latest signal a Buy on 21 Jun 2018 (trend up).", SMALL),
      Paragraph("Signals across all six stocks (raw prices, as in the course deck)", H2)]
rows = [["Stock", "Buys", "Sells", "Last signal date", "Last signal", "Trend"]]
for s in t10.index:
    rows.append([s, int(t10.loc[s, "buys"]), int(t10.loc[s, "sells"]), pd.Timestamp(t10.loc[s, "last_signal_date"]).strftime("%d %b %Y"), t10.loc[s, "last_signal"], tr_raw.loc[s, "trend"]])
rows.append(["Total", int(t10.buys.sum()), int(t10.sells.sum()), "", "", ""])
S += [table(rows, [3.6, 1.6, 1.6, 3.6, 2.8, 3.2], extra=[("FONTNAME", (0, 7), (-1, 7), "Helvetica-Bold"), ("BACKGROUND", (0, 7), (-1, 7), colors.HexColor("#e6eaf2"))]),
      Paragraph("Data quality: <b>deliverable_qty</b> is missing on just two dates (9 Dec 2015 for Eicher, Hero, TCS, TVS; 31 Aug 2017 for Bajaj, Infosys). "
                "Four unrelated companies share one date, so the gap is the exchange's reporting, not the companies. It does not touch prices or signals.", BODY)]
S.append(PageBreak())

# ---- page 3: data trap
S += [Paragraph("2. The data trap: two crashes that never happened", H1),
      Paragraph("Ranking the raw returns shows TCS at -23.8% and Infosys at -30.9%, two of India's most consistently profitable companies. "
                "Looking for each stock's single worst day explains why:", BODY), img("r_trap.png", 16.8)]
rows = [["Stock", "Worst day", "Close (Rs)", "Day move", "Explanation"]]
for _, r in t12.iterrows():
    ex = "1:1 bonus issue (price halves)" if r.pct_move < -20 else "Market sell-off"
    rows.append([r.stock, pd.Timestamp(r.date).strftime("%d %b %Y"), f"{r.close_price:,.2f}", f"{r.pct_move:.1f}%", ex])
S += [table(rows, [3.2, 2.8, 2.6, 2.3, 6.0], extra=[("TEXTCOLOR", (3, 1), (3, 2), colors.HexColor("#c0392b")), ("FONTNAME", (3, 1), (3, 2), "Helvetica-Bold")]),
      Spacer(1, 6),
      Paragraph("Four stocks lose 6% to 10% on their worst day. TCS and Infosys lose about half of their value on days with no bad news. In a 1:1 bonus issue every shareholder receives one extra share per share held, "
                "so the price halves and nobody gains or loses. Any unadjusted series shows a fake crash, and that corrupts <b>returns</b>, <b>moving averages</b> and <b>signals</b> around the date.", BODY),
      Paragraph("The fix", H2),
      Paragraph("Divide every price <b>before</b> the event date by 2 (Infosys before 15 Jun 2015, TCS before 31 May 2018); prices on and after the event stay unchanged. In SQL this is a <font face='Courier'>CASE</font> inside a CTE.", BODY),
      img("r_returns.png", 16.2)]
S.append(PageBreak())

# ---- page 4: effect on signals + recommendation
S += [Paragraph("3. What the fix changes", H1),
      Paragraph(f"Returns move dramatically: TCS from {tot_raw['TCS']:.1f}% to {tot_adj['TCS']:+.1f}% and Infosys from {tot_raw['Infosys']:.1f}% to {tot_adj['Infosys']:+.1f}%. "
                "Signals move too, because the averages are built from prices around the bonus date:", BODY)]
cnt = lambda sg, s, k: int((sg[(sg.stock == s)].signal == k).sum())
rows = [["Stock", "Raw B / S", "Adjusted B / S", "Latest (raw)", "Latest (adjusted)", "What happened"]]
what = {"TCS": "Bonus-day drop drags the 20-day average below the 50-day: a fake Sell. Adjusted: latest signal is a Buy.",
        "Infosys": "2015 bonus jump hid a real Buy and created a fake Sell. Latest signal unchanged."}
for s in ["TCS", "Infosys"]:
    rows.append([Paragraph(f"<b>{s}</b>", CELL), f"{cnt(sg_raw, s, 'Buy')} / {cnt(sg_raw, s, 'Sell')}", f"{cnt(sg_adj, s, 'Buy')} / {cnt(sg_adj, s, 'Sell')}",
                 f"{tr_raw.loc[s].signal} {tr_raw.loc[s].date:%d %b %y}", f"{tr_adj.loc[s].signal} {tr_adj.loc[s].date:%d %b %y}", Paragraph(what[s], CELL)])
S += [table(rows, [2.0, 1.9, 2.4, 2.9, 3.2, 4.6]),
      Paragraph("The other four stocks have no corporate action in the window, so nothing changes for them.", SMALL),
      Spacer(1, 4), img("r_tcs_signals.png", 16.4),
      Paragraph("Dashed line: TCS bonus-issue date (31 May 2018). On raw prices the drop drags the 20-day average under the 50-day and triggers a Sell on 5 Jun; on adjusted prices no such cross occurs and the latest signal remains the Buy of 20 Apr.", SMALL),
      Paragraph("Recommendation", H1)]
rows = [["Stock", "Adj. return", "Latest (adjusted)", "Call", "Reasoning"]]
why = {"Bajaj Auto": "Fresh Buy on 21 Jun 2018; modest but positive history.",
       "Infosys": "Buy since 7 May 2018; +38% adjusted, not the -31% the raw data shows.",
       "TCS": "Adjusted data gives a Buy (20 Apr 2018) and +52%; the deck's Sell is a data artefact.",
       "Eicher Motors": "Trend turned down 6 Jun 2018 after the 2017 peak; deepest drawdown risk with TVS.",
       "TVS Motors": "Trend down since 17 May 2018; highest volatility (30.8% annualised).",
       "Hero Motocorp": "Trend down since 22 May 2018 and the weakest return (+6.0%)."}
for s in ["Bajaj Auto", "Infosys", "TCS", "Eicher Motors", "TVS Motors", "Hero Motocorp"]:
    t = tr_adj.loc[s]; rows.append([Paragraph(f"<b>{s}</b>", CELL), f"{tot_adj[s]:+.1f}%", f"{t.signal}, {t.date:%d %b %Y}",
                                    Paragraph(f"<b>{verdict[s]}</b>", CELL), Paragraph(why[s], CELL)])
S += [table(rows, [2.7, 2.0, 3.3, 2.6, 6.4]),
      Spacer(1, 6),
      Paragraph("<b>Bottom line:</b> buy Bajaj Auto, Infosys and (after correcting the data) TCS; sell or reduce Eicher, TVS and Hero. "
                "The course deck reached 'sell TCS' only because its final call rests on unadjusted prices.", BODY)]
S.append(PageBreak())

# ---- page 5: backtest & risk
S += [Paragraph("4. Did the signals make money?", H1),
      Paragraph("Long-only test on adjusted prices: buy at the close of a Buy day, sell at the close of the next Sell, hold cash in between. "
                "Each day's position is decided from the previous close (no look-ahead). Transaction costs and taxes are ignored.", BODY), img("r_bt.png", 12.6)]
rows = [["Stock", "Buy & hold", "Golden cross", "Closed trades", "Win rate", "Avg trade", "Time in market"]]
for s in order:
    r = bt.set_index("stock").loc[s]
    rows.append([s, f"{r.buy_hold_pct:+.1f}%", f"{r.strategy_pct:+.1f}%", int(r.closed_trades), f"{r.win_rate:.0f}%", f"{r.avg_trade_pct:+.1f}%", f"{r.in_market_pct:.0f}%"])
S += [table(rows, [3.3, 2.3, 2.5, 2.4, 2.0, 2.2, 2.6], pad=2.6),
      Paragraph("The strategy lagged buy-and-hold on <b>all six</b> stocks. Eicher won 6 of 6 trades yet still trailed, because it sat out about half the time during a strong uptrend. "
                "TCS is the starkest case: +52.4% buy-and-hold against -22.4% for the strategy, with only 2 of 11 trades profitable. Moving averages lag price, so in rising or choppy markets they buy late and sell late.", BODY),
      Paragraph("5. Risk and diversification", H1), img("r_risk.png", 13.4)]
rows = [["Stock", "Ann. return", "Ann. volatility", "Max drawdown", "Return / risk"]]
for s, r in rk.iterrows(): rows.append([s, f"{r.ann_return_pct:.1f}%", f"{r.ann_vol_pct:.1f}%", f"{r.max_drawdown_pct:.1f}%", f"{r.return_per_risk:.2f}"])
S += [table(rows, [3.6, 2.8, 3.2, 3.2, 2.8], pad=2.6),
      Paragraph("Eicher and TVS earned the most but suffered the deepest drawdowns (-28% and -35%). TCS delivered the third-highest return with the lowest volatility of the six. "
                "Correlations are low (0.10 to 0.52) and lowest between the IT names and the auto names, so mixing the two groups diversifies.", BODY)]

# ---- page 6: risk (above) then deck check, limits, reproducibility
S += [Paragraph("6. Reconciling with the course deck", H1),
      Paragraph("Signal counts, latest-signal dates and trend directions match the deck for all six stocks. Three of the deck's return lines contain discrepancies:", BODY)]
S += bullets(["<b>Infosys</b> is printed as a '3% decrease'. The data gives <b>-30.9%</b> (a dropped digit).",
              "<b>TCS</b> lists 2548.20 as the 31 Jul 2018 close and 2454.1 as the 1 Jan 2015 close. In the data 2548.20 is TCS's <b>1 Jan 2015</b> close, 1941.25 is the 31 Jul 2018 close, and 2454.1 is <b>Bajaj's</b> 1 Jan 2015 close. The -23.8% itself is correct.",
              "<b>Eicher</b>'s 82.5% is 82.56% truncated rather than rounded (82.6%)."])
S += [Paragraph("Limitations", H1)]
S += bullets(["Moving-average signals are lagging indicators and underperformed buy-and-hold here. They should be combined with other evidence.",
              "3.6 years of data in one market regime; results are in-sample, with no costs or taxes. Nothing here is investment advice.",
              "Only close prices are used. Volume, delivery percentage and volatility filters are natural next steps.",
              "The two bonus dates were found from price behaviour and confirmed by name. A production pipeline should load a corporate-actions table (splits, bonuses, dividends) instead of hard-coding dates.",
              "Dividends are not included in returns."])
S += [KeepTogether([Paragraph("Reproducibility", H1),
      Paragraph("Everything in this report is generated from the SQL in <font face='Courier'>sql/analysis_sqlite.sql</font> (MySQL 8 version: <font face='Courier'>sql/analysis_mysql.sql</font>). "
                "The notebook walks through each query with interactive charts, and the Streamlit app adds a live SQL playground with 13 practice tasks and an answer checker.", BODY)])]
doc.build(S)
print("built report/Stock_Market_SQL_Insights.pdf")
