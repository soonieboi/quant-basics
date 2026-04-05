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

def render_phase_5(START, END, selected_tickers, api_key):
        st.markdown("<span class='phase-badge' style='background:#b48ead'>Phase 5</span>", unsafe_allow_html=True)
        st.markdown("## Combining Signals")
        st.markdown(f"<p class='section-label'>Ensemble methods · SMA + RSI · {START} → {END}</p>", unsafe_allow_html=True)
    
        with st.expander("101 — Why combine signals?", expanded=False):
            st.markdown("""
    <div class='explainer-box'>
    <h4>Diversification applies to signals, not just assets</h4>
    
    You've seen two very different strategies:
    <span class='rule'><b>SMA crossover</b>: trend-following. Wins when markets trend strongly in one direction.</span>
    <span class='rule'><b>RSI mean reversion</b>: buy the dip. Wins when markets oscillate around a range.</span>
    
    These regimes alternate. Sometimes markets trend for months (2020 recovery, 2022 crash).
    Other times they chop sideways for months (much of 2023). One strategy shines while the other suffers.
    
    <b>The key insight</b>: if two strategies are <b>negatively correlated</b> — one wins when the other loses —
    combining them produces a smoother, more consistent equity curve with a better Sharpe ratio.
    This is the same math as portfolio diversification, applied to signals.
    
    <br>
    
    <b>Three ways to combine</b><br>
    <span class='rule'><b>AND logic</b>: only go long when <i>both</i> signals agree. Very selective. Fewer trades, higher conviction.</span>
    <span class='rule'><b>OR logic</b>: go long when <i>either</i> signal fires. More aggressive. More time invested.</span>
    <span class='rule'><b>AVG (fractional)</b>: position = (SMA signal + RSI signal) / 2. Can be 0, 0.5, or 1. Continuous sizing.</span>
    
    None is universally better — it depends on the regime. BUT the combined Sharpe is often
    higher than either individual strategy, even if the combined return isn't the max.
    
    <br>
    
    <b>Signal correlation matters</b><br>
    If two signals are perfectly correlated (always agree), combining them adds nothing.
    If they're perfectly anti-correlated, the combined signal is flat and earns nothing.
    The sweet spot is low-but-positive correlation — you get diversification without cancellation.
    
    <br>
    
    <b>This is the foundation of systematic multi-strategy funds</b><br>
    Real quant funds (Two Sigma, Renaissance, D.E. Shaw) run hundreds of uncorrelated signals
    and combine them. No single signal is amazing. The combination is robust.
    The more uncorrelated signals you have, the more your Sharpe scales with √N.
    
    </div>
    """, unsafe_allow_html=True)
    
        # ── Controls ───────────────────────────────────────────────────────────────
        col_t, col_f, col_s, col_r, _ = st.columns([1, 1, 1, 1, 2])
        with col_t:
            comb_ticker  = st.selectbox("Ticker", options=list(TICKER_OPTIONS.keys()), index=0, key="comb_ticker")
        with col_f:
            fast_w = st.number_input("Fast SMA", min_value=5, max_value=100, value=50, step=5, key="c_fast")
        with col_s:
            slow_w = st.number_input("Slow SMA", min_value=20, max_value=400, value=200, step=10, key="c_slow")
        with col_r:
            rsi_p  = st.number_input("RSI Period", min_value=5, max_value=30, value=14, step=1, key="c_rsi")
    
        # ── Compute ────────────────────────────────────────────────────────────────
        with st.spinner("Computing…"):
            prices   = load_prices(comb_ticker, START, END)
            log_ret  = np.log(prices / prices.shift(1))
    
            sig_sma            = sma_signal(prices, fast_w, slow_w).reindex(prices.index).fillna(0)
            sig_rsi, _         = rsi_signal(prices, rsi_p, 30, 70)
            sig_rsi            = sig_rsi.reindex(prices.index).fillna(0)
    
            sig_and  = ((sig_sma == 1) & (sig_rsi == 1)).astype(float)
            sig_or   = ((sig_sma == 1) | (sig_rsi == 1)).astype(float)
            sig_avg  = (sig_sma + sig_rsi) / 2
    
            def ret_from_sig(sig):
                r = (log_ret * sig).dropna()
                return r, log_ret.loc[r.index]
    
            sma_ret,  bh_ret  = ret_from_sig(sig_sma)
            rsi_ret,  _       = ret_from_sig(sig_rsi)
            and_ret,  _       = ret_from_sig(sig_and)
            or_ret,   _       = ret_from_sig(sig_or)
            avg_ret,  _       = ret_from_sig(sig_avg)
    
            m_bh  = compute_metrics(bh_ret)
            m_sma = compute_metrics(sma_ret)
            m_rsi = compute_metrics(rsi_ret)
            m_and = compute_metrics(and_ret)
            m_or  = compute_metrics(or_ret)
            m_avg = compute_metrics(avg_ret)
    
            # Signal correlation
            common = sig_sma.dropna().index.intersection(sig_rsi.dropna().index)
            corr   = sig_sma.loc[common].corr(sig_rsi.loc[common])
    
            pct_long = {
                "SMA":  sig_sma.mean(), "RSI": sig_rsi.mean(),
                "AND":  sig_and.mean(), "OR":  sig_or.mean(), "AVG": sig_avg.mean(),
            }
    
        # ── KPIs ───────────────────────────────────────────────────────────────────
        st.markdown("<br>", unsafe_allow_html=True)
        cols = st.columns(6)
        for col, (name, m) in zip(cols, [("B&H", m_bh), ("SMA", m_sma), ("RSI", m_rsi),
                                          ("AND", m_and), ("OR", m_or),  ("AVG", m_avg)]):
            col.metric(f"Sharpe · {name}", f"{m['sharpe']:.2f}",
                       f"DD: {m['max_dd']:.1%}")
    
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(f"<p class='section-label'>Signal correlation: {corr:.2f} &nbsp;·&nbsp; "
                    f"SMA long {pct_long['SMA']:.0%} · RSI long {pct_long['RSI']:.0%} · "
                    f"AND long {pct_long['AND']:.0%} · OR long {pct_long['OR']:.0%}</p>",
                    unsafe_allow_html=True)
    
        # ── Equity curves ─────────────────────────────────────────────────────────
        st.markdown("<p class='section-label'>Equity curves — all five strategies</p>", unsafe_allow_html=True)
        palette = {"B&H": "var(--qb-muted)", "SMA": "#00ff88", "RSI": "#00b4ff",
                   "AND": "#f5c518", "OR": "#ff4466", "AVG": "#b48ead"}
        fig = go.Figure()
        for name, m in [("B&H", m_bh), ("SMA", m_sma), ("RSI", m_rsi),
                        ("AND", m_and), ("OR", m_or), ("AVG", m_avg)]:
            lw = 2 if name in ("AND", "OR", "AVG") else 1.2
            fig.add_trace(go.Scatter(x=m["cumulative"].index, y=m["cumulative"].values,
                name=name, line=dict(color=palette[name], width=lw),
                hovertemplate=f"{name}: $%{{y:.3f}}<extra></extra>"))
        fig.update_layout(**PLOTLY_THEME, height=400,
                          legend=dict(orientation="h", y=1.05, x=0, font=dict(size=10), bgcolor="rgba(0,0,0,0)"),
                          hovermode="x unified", yaxis_title="Growth of $1")
        st.plotly_chart(fig, width="stretch")
        best_combo = max([("AND",m_and),("OR",m_or),("AVG",m_avg)], key=lambda x: x[1]["sharpe"])
        chart_caption(ai_insight(
            f"Signal combination on {comb_ticker}. SMA Sharpe {m_sma['sharpe']:.2f}, RSI Sharpe {m_rsi['sharpe']:.2f}. "
            f"AND combo Sharpe {m_and['sharpe']:.2f}, OR combo {m_or['sharpe']:.2f}, AVG combo {m_avg['sharpe']:.2f}. "
            f"Signal correlation: {corr:.2f}.",
            api_key) or
            f"The {best_combo[0]} combination had the best Sharpe ({best_combo[1]['sharpe']:.2f}) by requiring {'both signals to agree' if best_combo[0]=='AND' else 'either signal' if best_combo[0]=='OR' else 'averaging both signals'}. "
            f"Signal correlation of {corr:.2f} means the two strategies {'often agree' if corr > 0.5 else 'frequently diverge' if corr < 0.2 else 'partially overlap'} — {'less diversification benefit' if corr > 0.5 else 'good diversification potential'}.")
    
        # ── Sharpe & drawdown bars ─────────────────────────────────────────────────
        st.markdown("<p class='section-label'>Sharpe and max drawdown comparison</p>", unsafe_allow_html=True)
        fig2 = make_subplots(rows=1, cols=2, subplot_titles=("Sharpe Ratio", "Max Drawdown"))
        names   = ["B&H", "SMA", "RSI", "AND", "OR", "AVG"]
        sharpes = [m_bh["sharpe"], m_sma["sharpe"], m_rsi["sharpe"],
                   m_and["sharpe"], m_or["sharpe"], m_avg["sharpe"]]
        dds     = [m_bh["max_dd"], m_sma["max_dd"], m_rsi["max_dd"],
                   m_and["max_dd"], m_or["max_dd"], m_avg["max_dd"]]
        clrs    = [palette[n] for n in names]
        fig2.add_trace(go.Bar(x=names, y=sharpes, marker_color=clrs,
                              text=[f"{s:.2f}" for s in sharpes], textposition="outside"), row=1, col=1)
        fig2.add_trace(go.Bar(x=names, y=dds, marker_color=clrs,
                              text=[f"{d:.1%}" for d in dds], textposition="outside"), row=1, col=2)
        fig2.update_layout(**PLOTLY_THEME, height=340, showlegend=False)
        fig2.update_yaxes(gridcolor="var(--qb-border)", row=1, col=1)
        fig2.update_yaxes(gridcolor="var(--qb-border)", tickformat=".0%", row=1, col=2)
        st.plotly_chart(fig2, width="stretch")
        chart_caption(ai_insight(
            f"Sharpe and max drawdown comparison for combined signals on {comb_ticker}. "
            f"Buy-and-hold Sharpe {m_bh['sharpe']:.2f}, SMA {m_sma['sharpe']:.2f}, RSI {m_rsi['sharpe']:.2f}, "
            f"AND {m_and['sharpe']:.2f}, OR {m_or['sharpe']:.2f}, AVG {m_avg['sharpe']:.2f}.",
            api_key) or
            f"The left bars compare return per unit of risk, while the right bars show worst peak-to-trough loss. "
            f"You want bars that are high on Sharpe and less negative on drawdown, which is why combinations can beat either signal alone.")
    
        # ── Full table ─────────────────────────────────────────────────────────────
        st.markdown("<p class='section-label'>Full metrics table</p>", unsafe_allow_html=True)
        rows_data = []
        for name, m in [("Buy & Hold", m_bh), ("SMA", m_sma), ("RSI", m_rsi),
                        ("AND (both)", m_and), ("OR (either)", m_or), ("AVG (fractional)", m_avg)]:
            rows_data.append({
                "Strategy":    name,
                "Ann. Return": f"{m['ann_return']:.2%}",
                "Ann. Vol":    f"{m['ann_vol']:.2%}",
                "Sharpe":      f"{m['sharpe']:.2f}",
                "Max DD":      f"{m['max_dd']:.2%}",
                "% Long":      f"{pct_long.get(name.split()[0], 1.0):.0%}",
            })
        st.dataframe(pd.DataFrame(rows_data).set_index("Strategy"), width="stretch")
        render_bottom_nav("Phase 5 — Combining Signals")
    
    
    # ════════════════════════════════════════════════════════════════════════════
    #  PHASE 6 — WALK-FORWARD VALIDATION
    # ════════════════════════════════════════════════════════════════════════════
