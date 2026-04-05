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

def render_phase_2(START, END, selected_tickers, api_key):
        st.markdown("<span class='phase-badge'>Phase 2</span>", unsafe_allow_html=True)
        st.markdown("## SMA Crossover Strategy")
        st.markdown(f"<p class='section-label'>Trend-following · Golden cross / death cross · {START} → {END}</p>", unsafe_allow_html=True)
    
        # ── 101 Explainer ──────────────────────────────────────────────────────────
        with st.expander("101 — How does this strategy work?", expanded=False):
            st.markdown("""
    <div class='explainer-box'>
    <h4>Trend-following with moving average crossovers</h4>
    
    <b>What is a Moving Average?</b><br>
    A Simple Moving Average (SMA) smooths out day-to-day price noise by averaging the last N closing prices.
    <code>SMA(50)</code> = average of the last 50 closing prices, updated daily.
    The longer the window, the smoother (and slower) it is.
    
    <br>
    
    <b>Why two moving averages?</b><br>
    <span class='rule'><b>Fast SMA</b> (e.g. 50-day): reacts quickly to recent price changes.</span>
    <span class='rule'><b>Slow SMA</b> (e.g. 200-day): represents the long-term trend.</span>
    When the fast SMA crosses <b>above</b> the slow SMA, recent prices are higher than the long-term average — the market is trending up. This is called a <b class='good'>Golden Cross</b>.
    When the fast SMA crosses <b>below</b> the slow SMA, the trend has reversed. This is a <b class='bad'>Death Cross</b>.
    
    <br>
    
    <b>The signal logic</b>
    <span class='formula'>signal = 1 (long) if SMA_fast > SMA_slow, else 0 (flat/cash)</span>
    We are either fully in (100% long SPY) or fully out (holding cash). No shorting, no leverage.
    
    <br>
    
    <b>The most important implementation detail: .shift(1)</b><br>
    We shift the signal forward by 1 day. Why? Because you calculate today's SMA using today's closing price — and you can't trade at that price. You trade the <i>next day</i>.
    Forgetting this shift is called <b class='bad'>look-ahead bias</b> — your backtest secretly "knows the future" and produces unrealistically good results. A common beginner trap.
    
    <br>
    
    <b>What kind of strategy is this?</b><br>
    This is a <b>trend-following</b> strategy. The core assumption: <i>markets that are going up tend to keep going up</i> (momentum). You get in when the trend starts and get out when it breaks.
    <span class='rule'><b class='good'>Works well in</b>: sustained bull or bear markets (clear trends).</span>
    <span class='rule'><b class='bad'>Fails in</b>: choppy, sideways markets — you get lots of false signals and whipsaws.</span>
    
    <br>
    
    <b>Why did this beat buy-and-hold in 2020–2024?</b><br>
    The 2022 bear market. The death cross hit in early 2022, taking us to cash before the worst of the decline. We missed the drawdown while buy-and-hold investors sat through -35.75%.
    The cost: we were in cash 41% of the time and missed some upside. But the Sharpe nearly doubled because our volatility was much lower.
    
    <br>
    
    <b>The honest caveats</b><br>
    <span class='rule'>Only 3 trades in 4 years — tiny sample size. Hard to be confident.</span>
    <span class='rule'>No transaction costs or slippage modelled (Phase 4 fixes this).</span>
    <span class='rule'>Cash earns 0% — in reality you'd earn T-bill rates (~5% in 2023).</span>
    <span class='rule'>Past regime may not repeat — SMA crossover can fail badly in other periods.</span>
    
    </div>
    """, unsafe_allow_html=True)
    
        # ── Controls ───────────────────────────────────────────────────────────────
        col_t, col_a, col_b, _ = st.columns([1, 1, 1, 3])
        with col_t:
            strat_ticker = st.selectbox("Ticker", options=list(TICKER_OPTIONS.keys()), index=0)
        with col_a:
            fast_window = st.number_input("Fast SMA", min_value=5, max_value=100, value=50, step=5)
        with col_b:
            slow_window = st.number_input("Slow SMA", min_value=20, max_value=400, value=200, step=10)
    
        if fast_window >= slow_window:
            st.warning("Fast window must be smaller than slow window.")
            st.stop()
    
        # ── Compute ────────────────────────────────────────────────────────────────
        with st.spinner("Computing…"):
            prices    = load_prices(strat_ticker, START, END)
            sma_fast  = prices.rolling(fast_window).mean()
            sma_slow  = prices.rolling(slow_window).mean()
            signal    = (sma_fast > sma_slow).astype(int).shift(1)
            log_ret   = np.log(prices / prices.shift(1))
            strat_ret = (log_ret * signal).dropna()
            bh_ret    = log_ret.loc[strat_ret.index]
            m_bh      = compute_metrics(bh_ret)
            m_strat   = compute_metrics(strat_ret)
            total_days = len(signal.dropna())
            days_long  = int(signal.sum())
            num_trades = int((signal.diff().abs() == 1).sum())
    
        # ── KPIs ───────────────────────────────────────────────────────────────────
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Sharpe",       f"{m_strat['sharpe']:.2f}",     f"{m_strat['sharpe']-m_bh['sharpe']:+.2f} vs B&H")
        c2.metric("Max Drawdown", f"{m_strat['max_dd']:.2%}",     f"{m_strat['max_dd']-m_bh['max_dd']:+.2%} vs B&H")
        c3.metric("Ann. Return",  f"{m_strat['ann_return']:.2%}", f"{m_strat['ann_return']-m_bh['ann_return']:+.2%} vs B&H")
        c4.metric("# Trades",     str(num_trades),                f"{days_long/total_days:.0%} time invested")
    
        st.markdown("<br>", unsafe_allow_html=True)
    
        # ── Chart ─────────────────────────────────────────────────────────────────
        st.markdown("<p class='section-label'>Price · equity curve · position</p>", unsafe_allow_html=True)
        fig = make_subplots(rows=3, cols=1, shared_xaxes=True,
                            row_heights=[0.5, 0.35, 0.15], vertical_spacing=0.03,
                            subplot_titles=("", "", ""))
    
        fig.add_trace(go.Scatter(x=prices.index, y=prices.values, name="SPY",
            line=dict(color="var(--qb-text)", width=1),
            hovertemplate="%{x|%Y-%m-%d}  $%{y:.2f}<extra></extra>"), row=1, col=1)
        fig.add_trace(go.Scatter(x=sma_fast.index, y=sma_fast.values, name=f"SMA {fast_window}",
            line=dict(color="#00b4ff", width=1.2, dash="dot"),
            hovertemplate=f"SMA{fast_window}: $%{{y:.2f}}<extra></extra>"), row=1, col=1)
        fig.add_trace(go.Scatter(x=sma_slow.index, y=sma_slow.values, name=f"SMA {slow_window}",
            line=dict(color="#f5c518", width=1.2, dash="dot"),
            hovertemplate=f"SMA{slow_window}: $%{{y:.2f}}<extra></extra>"), row=1, col=1)
    
        sig_aligned   = signal.reindex(prices.index).fillna(0)
        shade_y_upper = prices.where(sig_aligned == 1)
        fig.add_trace(go.Scatter(x=prices.index, y=shade_y_upper.values,
            fill="tonexty", fillcolor="rgba(0,255,136,0.05)",
            line=dict(width=0), showlegend=False, hoverinfo="skip"), row=1, col=1)
    
        fig.add_trace(go.Scatter(x=m_bh["cumulative"].index, y=m_bh["cumulative"].values,
            name="Buy & Hold", line=dict(color="var(--qb-muted)", width=1.2),
            hovertemplate="B&H: $%{y:.3f}<extra></extra>"), row=2, col=1)
        fig.add_trace(go.Scatter(x=m_strat["cumulative"].index, y=m_strat["cumulative"].values,
            name="Strategy", line=dict(color="#00ff88", width=1.5),
            hovertemplate="Strategy: $%{y:.3f}<extra></extra>"), row=2, col=1)
    
        fig.add_trace(go.Scatter(x=sig_aligned.index, y=sig_aligned.values,
            name="Position", line=dict(color="#00b4ff", width=0.8),
            fill="tozeroy", fillcolor="rgba(0,180,255,0.08)",
            hovertemplate="Position: %{y}<extra></extra>"), row=3, col=1)
    
        fig.update_layout(**PLOTLY_THEME, height=620,
                          legend=dict(orientation="h", y=1.02, x=0, font=dict(size=10), bgcolor="rgba(0,0,0,0)"),
                          hovermode="x unified")
        fig.update_yaxes(gridcolor="var(--qb-border)", row=1)
        fig.update_yaxes(gridcolor="var(--qb-border)", row=2, title_text="Growth $1")
        fig.update_yaxes(gridcolor="var(--qb-border)", tickvals=[0, 1], ticktext=["Flat", "Long"], row=3)
        fig.update_xaxes(gridcolor="var(--qb-border)")
        st.plotly_chart(fig, width="stretch")
        chart_caption(ai_insight(
            f"SMA {fast_window}/{slow_window} crossover on {strat_ticker}. "
            f"Strategy Sharpe {m_strat['sharpe']:.2f} vs buy-and-hold {m_bh['sharpe']:.2f}. "
            f"Strategy max drawdown {m_strat['max_dd']:.2%} vs B&H {m_bh['max_dd']:.2%}. "
            f"{num_trades} trades, {days_long/total_days:.0%} of time invested.",
            api_key) or
            f"The green shading shows periods when the strategy was long (invested). "
            f"The middle panel compares the strategy equity curve vs simply holding {strat_ticker} — "
            f"a Sharpe of {m_strat['sharpe']:.2f} vs {m_bh['sharpe']:.2f} means "
            f"{'better' if m_strat['sharpe'] > m_bh['sharpe'] else 'worse'} risk-adjusted returns with only {num_trades} trades over the period.")
    
        # ── Comparison table ───────────────────────────────────────────────────────
        st.markdown("<p class='section-label'>Head-to-head</p>", unsafe_allow_html=True)
        comp = pd.DataFrame({
            "Metric":     ["Ann. Return", "Ann. Vol", "Sharpe", "Max Drawdown"],
            "Buy & Hold": [f"{m_bh['ann_return']:.2%}", f"{m_bh['ann_vol']:.2%}",
                           f"{m_bh['sharpe']:.2f}", f"{m_bh['max_dd']:.2%}"],
            f"SMA {fast_window}/{slow_window}": [
                           f"{m_strat['ann_return']:.2%}", f"{m_strat['ann_vol']:.2%}",
                           f"{m_strat['sharpe']:.2f}", f"{m_strat['max_dd']:.2%}"],
            "Beat B&H?":  [
                "✓" if m_strat["ann_return"] > m_bh["ann_return"] else "✗",
                "✓" if m_strat["ann_vol"]    < m_bh["ann_vol"]    else "✗",
                "✓" if m_strat["sharpe"]     > m_bh["sharpe"]     else "✗",
                "✓" if m_strat["max_dd"]     > m_bh["max_dd"]     else "✗",
            ],
        }).set_index("Metric")
        st.dataframe(comp, width="stretch")
    
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(f"""
        <div style='font-family:JetBrains Mono;font-size:0.7rem;color:#3a4050;line-height:2;
                    border-left:2px solid var(--qb-border);padding-left:1rem;'>
        signal: long when SMA{fast_window} &gt; SMA{slow_window} · shifted +1 bar (no look-ahead bias)<br>
        trades: {num_trades} · days invested: {days_long}/{total_days} ({days_long/total_days:.0%})<br>
        no transaction costs · no slippage · cash earns 0%
        </div>
        """, unsafe_allow_html=True)
        render_bottom_nav("Phase 2 — SMA Crossover")
    
    
    # ════════════════════════════════════════════════════════════════════════════
    #  PHASE 3 — RSI MEAN REVERSION
    # ════════════════════════════════════════════════════════════════════════════
