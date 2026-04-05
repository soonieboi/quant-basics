import numpy as np
import pandas as pd
import plotly.graph_objects as go
import statsmodels.api as sm
import streamlit as st
from plotly.subplots import make_subplots
from scipy.optimize import minimize

from content.config import TICKER_OPTIONS
from core.ai import ai_insight
from core.data import load_prices
from core.metrics import compute_metrics, hex_to_rgba
from core.strategies import apply_costs, rsi_signal, sma_signal, strategy_returns
from ui.components import chart_caption, render_bottom_nav
from ui.styles import PLOTLY_THEME

def render_phase_1(START, END, selected_tickers, api_key):
        st.markdown("<span class='phase-badge yellow'>Phase 1</span>", unsafe_allow_html=True)
        st.markdown("## Asset Universe Metrics")
        st.markdown(f"<p class='section-label'>Annualised · log returns · {START} → {END}</p>", unsafe_allow_html=True)
    
        # ── 101 Explainer ──────────────────────────────────────────────────────────
        with st.expander("101 — What are we measuring and why?", expanded=False):
            st.markdown("""
    <div class='explainer-box'>
    <h4>The four metrics every quant lives by</h4>
    
    Before building any strategy, you need to understand what you're measuring.
    Think of these as the "unit tests" for financial performance.
    
    <br>
    
    <b>1. Returns — but why log returns?</b><br>
    You might expect us to use simple returns: <code>(price_today - price_yesterday) / price_yesterday</code>.
    We use <b>log returns</b> instead: <code>log(price_today / price_yesterday)</code>.
    <br>
    Why? Two reasons:
    <span class='rule'>They're <b>additive over time</b>. A 3-day log return = day1 + day2 + day3. Simple returns multiply, which is harder to work with mathematically.</span>
    <span class='rule'>They're <b>symmetric</b>. A +50% gain followed by a -50% loss in simple returns doesn't get you back to 1.0. Log returns behave consistently.</span>
    
    <br>
    
    <b>2. Annualised Return</b>
    <span class='formula'>Ann. Return = mean(daily_log_returns) × 252</span>
    There are ~252 trading days in a year. We scale daily average returns up to get a yearly figure.
    <span class='rule'>SPY gave <b class='good'>+11.1%/year</b> over this period. That's the passive "do nothing" baseline.</span>
    
    <br>
    
    <b>3. Volatility (Risk)</b>
    <span class='formula'>Ann. Vol = std(daily_log_returns) × √252</span>
    Volatility is the standard deviation of returns — it measures how much prices jump around.
    High volatility = risky. We multiply by √252 to annualise it (standard stats rule for scaling std dev over time).
    <span class='rule'>SPY: <b>22.7%</b> vol. BTC: much higher — it moves wildly. High vol isn't always bad, but you need to be paid for the risk.</span>
    
    <br>
    
    <b>4. Sharpe Ratio — the core risk-adjusted metric</b>
    <span class='formula'>Sharpe = Ann. Return / Ann. Volatility</span>
    The Sharpe ratio asks: <b>how much return are you getting per unit of risk?</b>
    It's return divided by risk. Higher is better. It lets you compare strategies fairly — a 5% return with tiny volatility beats a 20% return with huge swings.
    <span class='rule'><b class='bad'>< 0.5</b> — poor. Taking too much risk for the return.</span>
    <span class='rule'><b class='warn'>0.5 – 1.0</b> — acceptable. Most passive indices live here.</span>
    <span class='rule'><b class='good'>> 1.0</b> — good. Hedge funds aim for this.</span>
    <span class='rule'><b class='good'>> 2.0</b> — exceptional. Very rare in practice.</span>
    Note: In real life you'd subtract the risk-free rate (e.g. T-bill yield) from the return first. We're ignoring that here for simplicity.
    
    <br>
    
    <b>5. Max Drawdown — the gut-punch metric</b>
    <span class='formula'>Drawdown(t) = (cumulative_return(t) - peak_so_far) / peak_so_far</span>
    <span class='formula'>Max Drawdown = min(Drawdown) over all time</span>
    This answers: <b>what was the worst loss from a peak to a trough?</b>
    If you invested $100 and it fell to $64.25 before recovering, your max drawdown is -35.75%.
    <span class='rule'>SPY: <b class='warn'>-35.75%</b> (COVID crash 2020). Could you hold without selling? Most people can't.</span>
    <span class='rule'>BTC: <b class='bad'>-83.72%</b>. It recovered — but you need extreme conviction to not panic-sell.</span>
    Max drawdown is important because strategies that look great on paper can destroy you psychologically if the drawdown is too deep.
    
    </div>
    """, unsafe_allow_html=True)
    
        # ── Data ───────────────────────────────────────────────────────────────────
        tickers = {t: TICKER_OPTIONS[t] for t in selected_tickers}
        rows = []
        cumulative_map = {}
        with st.spinner("Pulling data…"):
            for ticker in tickers:
                prices  = load_prices(ticker, START, END)
                returns = np.log(prices / prices.shift(1)).dropna()
                m       = compute_metrics(returns)
                rows.append({
                    "Ticker":       ticker.replace("-USD", ""),
                    "Ann. Return":  m["ann_return"],
                    "Ann. Vol":     m["ann_vol"],
                    "Sharpe":       m["sharpe"],
                    "Max Drawdown": m["max_dd"],
                })
                cumulative_map[ticker] = m["cumulative"]
    
        # ── KPI strip ─────────────────────────────────────────────────────────────
        baseline = selected_tickers[0].replace("-USD", "")
        cols = st.columns(4)
        kpi_labels = ["Ann. Return", "Ann. Vol", "Sharpe", "Max Drawdown"]
        for col, lbl in zip(cols, kpi_labels):
            with col:
                vals = {r["Ticker"]: r[lbl] for r in rows}
                fmt  = "{:.2f}" if lbl == "Sharpe" else "{:.2%}"
                st.metric(label=lbl,
                          value=fmt.format(vals[baseline]),
                          delta=f"{baseline} baseline")
    
        st.markdown("<br>", unsafe_allow_html=True)
    
        # ── Table ─────────────────────────────────────────────────────────────────
        st.markdown("<p class='section-label'>Full breakdown</p>", unsafe_allow_html=True)
        df_table = pd.DataFrame(rows).set_index("Ticker")
        df_table["Ann. Return"]  = df_table["Ann. Return"].map("{:.2%}".format)
        df_table["Ann. Vol"]     = df_table["Ann. Vol"].map("{:.2%}".format)
        df_table["Sharpe"]       = df_table["Sharpe"].map("{:.2f}".format)
        df_table["Max Drawdown"] = df_table["Max Drawdown"].map("{:.2%}".format)
        st.dataframe(df_table, width="stretch")
    
        st.markdown("<br>", unsafe_allow_html=True)
    
        # ── Equity curves ─────────────────────────────────────────────────────────
        st.markdown("<p class='section-label'>Growth of $1</p>", unsafe_allow_html=True)
        fig = go.Figure()
        for ticker, color in tickers.items():
            curve = cumulative_map[ticker]
            lbl   = ticker.replace("-USD", "")
            fig.add_trace(go.Scatter(
                x=curve.index, y=curve.values, name=lbl,
                line=dict(color=color, width=1.5),
                hovertemplate=f"<b>{lbl}</b><br>%{{x|%Y-%m-%d}}<br>$%{{y:.3f}}<extra></extra>",
            ))
        fig.update_layout(**PLOTLY_THEME, height=340,
                          legend=dict(orientation="h", y=1.08, x=0, font=dict(size=10)),
                          yaxis_title="Growth of $1", hovermode="x unified")
        st.plotly_chart(fig, width="stretch")
        best_row = max(rows, key=lambda r: r["Sharpe"])
        chart_caption(ai_insight(
            f"Equity curves for {', '.join(r['Ticker'] for r in rows)} from {START} to {END}. "
            f"Best Sharpe: {best_row['Ticker']} at {best_row['Sharpe']:.2f}. "
            f"SPY annualised return: {rows[0]['Ann. Return']:.2%}, vol: {rows[0]['Ann. Vol']:.2%}.",
            api_key) or
            f"Each line shows how $1 invested grew over time. "
            f"The steeper and smoother the curve, the better the risk-adjusted performance. "
            f"{best_row['Ticker']} had the highest Sharpe ratio ({best_row['Sharpe']:.2f}) in this period.")
    
        # ── Drawdown chart ─────────────────────────────────────────────────────────
        st.markdown("<p class='section-label'>Drawdown</p>", unsafe_allow_html=True)
        fig2 = go.Figure()
        for ticker, color in tickers.items():
            prices  = load_prices(ticker)
            returns = np.log(prices / prices.shift(1)).dropna()
            cum     = (1 + returns).cumprod()
            dd      = (cum - cum.cummax()) / cum.cummax()
            lbl     = ticker.replace("-USD", "")
            fig2.add_trace(go.Scatter(
                x=dd.index, y=dd.values, name=lbl,
                fill="tozeroy", line=dict(color=color, width=1),
                fillcolor=hex_to_rgba(color, 0.08),
                hovertemplate=f"<b>{lbl}</b><br>%{{x|%Y-%m-%d}}<br>%{{y:.2%}}<extra></extra>",
            ))
        fig2.update_layout(**PLOTLY_THEME, height=260,
                           legend=dict(orientation="h", y=1.08, x=0, font=dict(size=10)),
                           hovermode="x unified")
        fig2.update_yaxes(tickformat=".0%", zeroline=True, zerolinecolor="var(--qb-border-strong)")
        st.plotly_chart(fig2, width="stretch")
        worst_dd = min(rows, key=lambda r: r["Max Drawdown"])
        chart_caption(ai_insight(
            f"Drawdown chart for {', '.join(r['Ticker'] for r in rows)}. "
            f"Worst max drawdown: {worst_dd['Ticker']} at {worst_dd['Max Drawdown']:.2%}. "
            f"SPY max drawdown: {rows[0]['Max Drawdown']:.2%}.",
            api_key) or
            f"Drawdown measures how far each asset fell from its previous peak. "
            f"{worst_dd['Ticker']} had the deepest drawdown at {worst_dd['Max Drawdown']:.2%} — "
            f"meaning if you bought at the top, you'd have been down that much at the worst point.")
        render_bottom_nav("Phase 1 — Asset Metrics")
    
    
    # ════════════════════════════════════════════════════════════════════════════
    #  PHASE 2 — SMA CROSSOVER
    # ════════════════════════════════════════════════════════════════════════════

