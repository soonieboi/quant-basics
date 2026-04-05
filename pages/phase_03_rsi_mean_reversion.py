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

def render_phase_3(START, END, selected_tickers, api_key):
        st.markdown("<span class='phase-badge blue'>Phase 3</span>", unsafe_allow_html=True)
        st.markdown("## RSI Mean Reversion Strategy")
        st.markdown(f"<p class='section-label'>Mean reversion · buy the dip · {START} → {END}</p>", unsafe_allow_html=True)
    
        # ── 101 Explainer ──────────────────────────────────────────────────────────
        with st.expander("101 — What is RSI and mean reversion?", expanded=False):
            st.markdown("""
    <div class='explainer-box'>
    <h4>Mean reversion: the opposite of trend-following</h4>
    
    Phase 2 assumed <i>trends persist</i>. Phase 3 assumes the opposite:
    <b>prices that move too far from their average will snap back.</b>
    This is called <b>mean reversion</b>.
    
    Think of it like a rubber band — the further you stretch it, the harder it pulls back.
    In markets: a stock that drops 15% in a week due to panic selling is probably oversold,
    and buyers will step in to push it back up.
    
    <br>
    
    <b>The RSI indicator</b><br>
    RSI (Relative Strength Index) measures <b>how fast and how much</b> a price has moved recently.
    It gives a value between 0 and 100.
    <span class='formula'>Step 1: avg_gain = average of up-days over last N days (default: 14)</span>
    <span class='formula'>Step 2: avg_loss = average of down-days over last N days</span>
    <span class='formula'>Step 3: RS = avg_gain / avg_loss</span>
    <span class='formula'>Step 4: RSI = 100 − (100 / (1 + RS))</span>
    
    Interpretation:
    <span class='rule'><b class='bad'>RSI &lt; 30</b> → <b>Oversold</b>. The asset has fallen hard and fast. Mean reversion bet: buy, expecting a bounce.</span>
    <span class='rule'><b class='good'>RSI &gt; 70</b> → <b>Overbought</b>. The asset has rallied hard and fast. Mean reversion exit: sell, expecting a pullback.</span>
    <span class='rule'><b>RSI ~50</b> → Neutral. No strong signal.</span>
    
    <br>
    
    <b>The signal logic (stateful)</b><br>
    Unlike the SMA crossover which re-evaluates every day, RSI creates a <b>stateful</b> position:
    <span class='rule'>Enter long when RSI crosses <b>below 30</b> (oversold trigger).</span>
    <span class='rule'>Stay long until RSI crosses <b>above 70</b> (overbought exit).</span>
    <span class='rule'>Otherwise: hold current position.</span>
    The position is still shifted +1 day to avoid look-ahead bias.
    
    <br>
    
    <b>Trend-following vs Mean Reversion — when does each work?</b><br>
    <span class='rule'><b>Trend-following (SMA)</b>: wins in sustained directional markets (2020 recovery, 2022 crash).</span>
    <span class='rule'><b>Mean reversion (RSI)</b>: wins in choppy, range-bound markets where dips recover quickly.</span>
    They're <b>negatively correlated</b> — when one is losing, the other often profits.
    This is exactly why Phase 5 (combining signals) is so powerful.
    
    <br>
    
    <b>Why is RSI period 14 the default?</b><br>
    J. Welles Wilder, who invented RSI in 1978, found 14 days worked well empirically.
    It's roughly 2–3 trading weeks — long enough to smooth noise, short enough to be responsive.
    You can tune it — shorter (e.g. 7) = more sensitive, more trades; longer (e.g. 21) = fewer, smoother signals.
    
    </div>
    """, unsafe_allow_html=True)
    
        # ── Controls ───────────────────────────────────────────────────────────────
        col_t, col_a, col_b, col_c = st.columns([1, 1, 1, 1])
        with col_t:
            rsi_ticker = st.selectbox("Ticker", options=list(TICKER_OPTIONS.keys()), index=0, key="rsi_ticker")
        with col_a:
            rsi_period   = st.number_input("RSI Period", min_value=2, max_value=50, value=14, step=1)
        with col_b:
            oversold_lvl = st.number_input("Oversold (buy)", min_value=10, max_value=45, value=30, step=5)
        with col_c:
            overbought_lvl = st.number_input("Overbought (sell)", min_value=55, max_value=90, value=70, step=5)
    
        # ── Compute RSI ────────────────────────────────────────────────────────────
        with st.spinner("Computing…"):
            prices  = load_prices(rsi_ticker, START, END)
            delta   = prices.diff()
            gain    = delta.clip(lower=0)
            loss    = (-delta).clip(lower=0)
            avg_gain = gain.ewm(com=rsi_period - 1, min_periods=rsi_period).mean()
            avg_loss = loss.ewm(com=rsi_period - 1, min_periods=rsi_period).mean()
            rs      = avg_gain / avg_loss
            rsi     = 100 - (100 / (1 + rs))
    
            # Stateful signal: enter on oversold cross, exit on overbought cross
            position = pd.Series(np.nan, index=prices.index)
            current  = 0
            for i in range(len(rsi)):
                if np.isnan(rsi.iloc[i]):
                    position.iloc[i] = 0
                    continue
                if current == 0 and rsi.iloc[i] < oversold_lvl:
                    current = 1
                elif current == 1 and rsi.iloc[i] > overbought_lvl:
                    current = 0
                position.iloc[i] = current
    
            signal    = position.shift(1)
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
    
        # ── Charts ─────────────────────────────────────────────────────────────────
        st.markdown("<p class='section-label'>RSI · price · equity curve · position</p>", unsafe_allow_html=True)
    
        fig = make_subplots(rows=4, cols=1, shared_xaxes=True,
                            row_heights=[0.15, 0.35, 0.35, 0.15],
                            vertical_spacing=0.02,
                            subplot_titles=("", "", "", ""))
    
        # Panel 1: RSI
        fig.add_trace(go.Scatter(x=rsi.index, y=rsi.values, name="RSI",
            line=dict(color="#b48ead", width=1.2),
            hovertemplate="RSI: %{y:.1f}<extra></extra>"), row=1, col=1)
        fig.add_hline(y=oversold_lvl,   line=dict(color="#00ff88", width=0.8, dash="dot"), row=1, col=1)
        fig.add_hline(y=overbought_lvl, line=dict(color="#ff4466", width=0.8, dash="dot"), row=1, col=1)
        fig.add_hline(y=50,             line=dict(color="var(--qb-border-strong)", width=0.6),              row=1, col=1)
    
        # RSI bands shading
        fig.add_trace(go.Scatter(
            x=rsi.index, y=rsi.where(rsi < oversold_lvl).values,
            fill="tozeroy", fillcolor="rgba(0,255,136,0.06)",
            line=dict(width=0), showlegend=False, hoverinfo="skip"), row=1, col=1)
    
        # Panel 2: Price
        fig.add_trace(go.Scatter(x=prices.index, y=prices.values, name="SPY",
            line=dict(color="var(--qb-text)", width=1),
            hovertemplate="%{x|%Y-%m-%d}  $%{y:.2f}<extra></extra>"), row=2, col=1)
        sig_aligned   = signal.reindex(prices.index).fillna(0)
        shade_y_upper = prices.where(sig_aligned == 1)
        fig.add_trace(go.Scatter(x=prices.index, y=shade_y_upper.values,
            fill="tonexty", fillcolor="rgba(0,255,136,0.05)",
            line=dict(width=0), showlegend=False, hoverinfo="skip"), row=2, col=1)
    
        # Panel 3: Equity curves
        fig.add_trace(go.Scatter(x=m_bh["cumulative"].index, y=m_bh["cumulative"].values,
            name="Buy & Hold", line=dict(color="var(--qb-muted)", width=1.2),
            hovertemplate="B&H: $%{y:.3f}<extra></extra>"), row=3, col=1)
        fig.add_trace(go.Scatter(x=m_strat["cumulative"].index, y=m_strat["cumulative"].values,
            name="RSI Strategy", line=dict(color="#00b4ff", width=1.5),
            hovertemplate="RSI: $%{y:.3f}<extra></extra>"), row=3, col=1)
    
        # Panel 4: Position
        fig.add_trace(go.Scatter(x=sig_aligned.index, y=sig_aligned.values,
            name="Position", line=dict(color="#00b4ff", width=0.8),
            fill="tozeroy", fillcolor="rgba(0,180,255,0.08)",
            hovertemplate="Position: %{y}<extra></extra>"), row=4, col=1)
    
        fig.update_layout(**PLOTLY_THEME, height=720,
                          legend=dict(orientation="h", y=1.02, x=0, font=dict(size=10), bgcolor="rgba(0,0,0,0)"),
                          hovermode="x unified")
        fig.update_yaxes(gridcolor="var(--qb-border)", title_text="RSI", row=1)
        fig.update_yaxes(gridcolor="var(--qb-border)", title_text="Price", row=2)
        fig.update_yaxes(gridcolor="var(--qb-border)", title_text="Growth $1", row=3)
        fig.update_yaxes(gridcolor="var(--qb-border)", tickvals=[0, 1], ticktext=["Flat", "Long"], row=4)
        fig.update_xaxes(gridcolor="var(--qb-border)")
        st.plotly_chart(fig, width="stretch")
        chart_caption(ai_insight(
            f"RSI({rsi_period}) mean reversion on {rsi_ticker}. Buy below {oversold_lvl}, sell above {overbought_lvl}. "
            f"Strategy Sharpe {m_strat['sharpe']:.2f}, max drawdown {m_strat['max_dd']:.2%}. "
            f"Buy-and-hold Sharpe {m_bh['sharpe']:.2f}, max drawdown {m_bh['max_dd']:.2%}. "
            f"{num_trades} trades, in market {days_long/total_days:.0%} of the time.",
            api_key) or
            f"The top panel shows RSI — when it dips below {oversold_lvl} (green band) the strategy enters long; "
            f"it exits when RSI exceeds {overbought_lvl}. "
            f"With {num_trades} trades and {days_long/total_days:.0%} time invested, the strategy achieved "
            f"Sharpe {m_strat['sharpe']:.2f} vs buy-and-hold's {m_bh['sharpe']:.2f}.")
    
        # ── Comparison table ───────────────────────────────────────────────────────
        st.markdown("<p class='section-label'>Head-to-head</p>", unsafe_allow_html=True)
        comp = pd.DataFrame({
            "Metric":     ["Ann. Return", "Ann. Vol", "Sharpe", "Max Drawdown"],
            "Buy & Hold": [f"{m_bh['ann_return']:.2%}", f"{m_bh['ann_vol']:.2%}",
                           f"{m_bh['sharpe']:.2f}", f"{m_bh['max_dd']:.2%}"],
            f"RSI({rsi_period}) {oversold_lvl}/{overbought_lvl}": [
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
        signal: enter long when RSI({rsi_period}) &lt; {oversold_lvl} · exit when RSI &gt; {overbought_lvl} · shifted +1 bar<br>
        trades: {num_trades} · days invested: {days_long}/{total_days} ({days_long/total_days:.0%})<br>
        no transaction costs · no slippage · cash earns 0%
        </div>
        """, unsafe_allow_html=True)
        render_bottom_nav("Phase 3 — RSI Mean Reversion")
    
    
    # ════════════════════════════════════════════════════════════════════════════
    #  PHASE 4 — TRANSACTION COSTS
    # ════════════════════════════════════════════════════════════════════════════
