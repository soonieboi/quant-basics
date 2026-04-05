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

def render_phase_9(START, END, selected_tickers, api_key):
        st.markdown("<span class='phase-badge' style='background:#ff4466'>Phase 9</span>", unsafe_allow_html=True)
        st.markdown("## Risk Management")
        st.markdown(f"<p class='section-label'>VaR · CVaR · drawdown limits · regime detection · {START} → {END}</p>", unsafe_allow_html=True)
    
        with st.expander("101 — Knowing when to stop", expanded=False):
            st.markdown("""
    <div class='explainer-box'>
    <h4>Risk management: the difference between a bad month and blowing up</h4>
    
    Every strategy will have losing periods. Risk management is the set of rules that ensure
    a losing streak doesn't turn into permanent capital loss.
    
    <br>
    
    <b>Value at Risk (VaR)</b><br>
    The most widely used risk metric in professional finance.
    <span class='formula'>VaR(95%) = the loss you expect to exceed only 5% of the time</span>
    If your daily VaR(95%) is −2%, it means on 95% of days you'll lose less than 2%.
    On the other 5% of days, losses can be anything — VaR tells you nothing about those.
    <span class='rule'>VaR is a threshold, not a worst case. It famously failed in 2008 — banks knew their VaR but not their tail risk.</span>
    
    <br>
    
    <b>Expected Shortfall (CVaR / ES)</b><br>
    Fixes VaR's blind spot: what do you lose on the <i>bad</i> days?
    <span class='formula'>CVaR(95%) = average loss on the worst 5% of days</span>
    CVaR is always worse (more negative) than VaR. The difference tells you how fat the tails are.
    A large CVaR vs VaR gap means crash risk — your losses in bad scenarios are much worse than average.
    <span class='rule'>CVaR is now preferred by regulators (Basel III) and sophisticated risk managers over VaR.</span>
    
    <br>
    
    <b>Drawdown Limits</b><br>
    Practical rule used by real funds: if your strategy drawdown hits a threshold, reduce or stop trading.
    <span class='rule'><b>Soft limit</b> (e.g. −10%): reduce position size by 50%.</span>
    <span class='rule'><b>Hard limit</b> (e.g. −20%): stop trading entirely, review the strategy.</span>
    This is not just about capital preservation — a strategy in deep drawdown may have fundamentally broken.
    The regime it was designed for may have ended.
    
    <br>
    
    <b>Regime Detection</b><br>
    Markets alternate between different regimes: trending, mean-reverting, high-vol, low-vol.
    A simple regime detector: rolling volatility.
    <span class='rule'><b class='bad'>High vol regime</b>: 30-day rolling vol > 2× long-term average. Risk-off. Reduce positions.</span>
    <span class='rule'><b class='good'>Low vol regime</b>: normal or below-average vol. Full deployment.</span>
    More sophisticated: Hidden Markov Models, regime-switching GARCH. But rolling vol alone catches most regime shifts.
    
    <br>
    
    <b>The risk manager's job</b><br>
    At a real fund, the risk manager is separate from the portfolio manager.
    The PM wants to be invested; the risk manager's job is to say no.
    As a solo trader, you have to play both roles — which is psychologically hard.
    Pre-committing to rules (written down before you start trading) is the only solution.
    
    </div>
    """, unsafe_allow_html=True)
    
        col_t, col_c, _ = st.columns([1, 1, 4])
        with col_t:
            rm_ticker = st.selectbox("Ticker", options=list(TICKER_OPTIONS.keys()), index=0, key="rm_ticker")
        with col_c:
            conf_level = st.selectbox("Confidence level", [90, 95, 99], index=1, key="rm_conf")
    
        with st.spinner("Computing risk metrics…"):
            prices   = load_prices(rm_ticker, START, END)
            log_ret  = np.log(prices / prices.shift(1)).dropna()
            alpha    = 1 - conf_level / 100
    
            # VaR and CVaR
            var_val   = float(np.percentile(log_ret, alpha * 100))
            cvar_val  = float(log_ret[log_ret <= var_val].mean())
    
            # Rolling metrics
            roll_vol  = log_ret.rolling(21).std() * np.sqrt(252)
            long_vol  = log_ret.std() * np.sqrt(252)
    
            # Drawdown series
            cum       = (1 + log_ret).cumprod()
            dd_series = (cum - cum.cummax()) / cum.cummax()
    
            # Regime: high vol = rolling vol > 1.5x long-term
            regime    = (roll_vol > 1.5 * long_vol).astype(int)
    
        # ── KPIs ───────────────────────────────────────────────────────────────────
        st.markdown("<br>", unsafe_allow_html=True)
        c1, c2, c3, c4 = st.columns(4)
        c1.metric(f"Daily VaR ({conf_level}%)",  f"{var_val:.2%}",  f"exceeded {alpha:.0%} of days")
        c2.metric(f"Daily CVaR ({conf_level}%)", f"{cvar_val:.2%}", f"{(cvar_val/var_val):.2f}× worse than VaR")
        c3.metric("Ann. VaR (approx)",           f"{var_val*np.sqrt(252):.2%}", "×√252 scaling")
        c4.metric("Max Drawdown",                f"{dd_series.min():.2%}", "all-time worst")
    
        st.markdown("<br>", unsafe_allow_html=True)
    
        # ── Return distribution ────────────────────────────────────────────────────
        st.markdown("<p class='section-label'>Daily return distribution with VaR / CVaR</p>", unsafe_allow_html=True)
        fig = go.Figure()
        fig.add_trace(go.Histogram(x=log_ret.values, nbinsx=80,
                                   marker_color="rgba(0,180,255,0.4)",
                                   marker_line=dict(color="#00b4ff", width=0.5),
                                   name="Daily returns",
                                   hovertemplate="Return: %{x:.2%}<br>Count: %{y}<extra></extra>"))
        fig.add_vline(x=var_val,  line=dict(color="#f5c518", width=1.5, dash="dash"),
                      annotation_text=f"VaR {conf_level}%", annotation_font=dict(color="#f5c518", size=10))
        fig.add_vline(x=cvar_val, line=dict(color="#ff4466", width=1.5, dash="dash"),
                      annotation_text=f"CVaR {conf_level}%", annotation_font=dict(color="#ff4466", size=10))
        fig.update_layout(**PLOTLY_THEME, height=300, showlegend=False,
                          xaxis_title="Daily Log Return", yaxis_title="Frequency")
        fig.update_xaxes(tickformat=".1%")
        st.plotly_chart(fig, width="stretch")
        chart_caption(ai_insight(
            f"Risk distribution for {rm_ticker}. Daily VaR at {conf_level}% is {var_val:.2%} and CVaR is {cvar_val:.2%}. "
            f"Maximum drawdown over the sample is {dd_series.min():.2%}.",
            api_key) or
            f"The yellow line marks the loss threshold breached only on the worst {alpha:.0%} of days, while the red line shows the average loss once you are already in that tail. "
            f"A much worse CVaR than VaR means tail losses are especially severe when things go wrong.")
    
        # ── Drawdown + regime ─────────────────────────────────────────────────────
        st.markdown("<p class='section-label'>Drawdown and volatility regime</p>", unsafe_allow_html=True)
        fig2 = make_subplots(rows=2, cols=1, shared_xaxes=True,
                             row_heights=[0.6, 0.4], vertical_spacing=0.03)
    
        fig2.add_trace(go.Scatter(x=dd_series.index, y=dd_series.values,
            fill="tozeroy", fillcolor="rgba(255,68,102,0.15)",
            line=dict(color="#ff4466", width=1), name="Drawdown",
            hovertemplate="%{x|%Y-%m-%d}: %{y:.2%}<extra></extra>"), row=1, col=1)
        fig2.add_hline(y=-0.10, line=dict(color="#f5c518", dash="dot", width=1), row=1, col=1,
                       annotation_text="−10% soft limit", annotation_font=dict(color="#f5c518", size=9))
        fig2.add_hline(y=-0.20, line=dict(color="#ff4466", dash="dot", width=1), row=1, col=1,
                       annotation_text="−20% hard limit", annotation_font=dict(color="#ff4466", size=9))
    
        fig2.add_trace(go.Scatter(x=roll_vol.index, y=roll_vol.values,
            line=dict(color="#00b4ff", width=1), name="21d Rolling Vol",
            hovertemplate="Vol: %{y:.2%}<extra></extra>"), row=2, col=1)
        fig2.add_hline(y=long_vol, line=dict(color="#5a6070", dash="dot", width=1), row=2, col=1)
        fig2.add_hline(y=1.5*long_vol, line=dict(color="#ff4466", dash="dot", width=1), row=2, col=1,
                       annotation_text="High-vol threshold", annotation_font=dict(color="#ff4466", size=9))
    
        # Shade high-vol regimes
        if (roll_vol > 1.5 * long_vol).any():
            fig2.add_trace(go.Scatter(
                x=roll_vol.index,
                y=roll_vol.where(roll_vol > 1.5 * long_vol),
                fill="tozeroy", fillcolor="rgba(255,68,102,0.1)",
                line=dict(width=0), showlegend=False, hoverinfo="skip"), row=2, col=1)
    
        fig2.update_layout(**PLOTLY_THEME, height=440,
                           legend=dict(orientation="h", y=1.02, x=0, font=dict(size=10), bgcolor="rgba(0,0,0,0)"),
                           hovermode="x unified")
        fig2.update_yaxes(tickformat=".0%", gridcolor="#161820", row=1)
        fig2.update_yaxes(tickformat=".0%", gridcolor="#161820", title_text="Ann. Vol", row=2)
        fig2.update_xaxes(gridcolor="#161820")
        st.plotly_chart(fig2, width="stretch")
        chart_caption(ai_insight(
            f"Drawdown and volatility regime for {rm_ticker}. "
            f"Max drawdown is {dd_series.min():.2%}, long-run annualized vol {long_vol:.2%}, and high-vol regime days are {int(regime.sum())} out of {len(regime.dropna())}.",
            api_key) or
            f"The top panel shows how deep losses became from prior peaks, and the bottom panel shows when volatility moved into a stressed regime. "
            f"When both are elevated at the same time, that is usually when risk controls matter most.")
    
        # ── Risk table ─────────────────────────────────────────────────────────────
        st.markdown("<p class='section-label'>Risk summary</p>", unsafe_allow_html=True)
        high_vol_days = int(regime.sum())
        total_days    = len(regime.dropna())
        risk_rows = pd.DataFrame({
            "Metric": ["Daily VaR", "Daily CVaR", "CVaR/VaR ratio", "Ann. Vol",
                       "Max Drawdown", "High-vol regime days"],
            "Value":  [f"{var_val:.3%}", f"{cvar_val:.3%}",
                       f"{cvar_val/var_val:.2f}×",
                       f"{long_vol:.2%}", f"{dd_series.min():.2%}",
                       f"{high_vol_days} / {total_days} ({high_vol_days/total_days:.0%})"],
        }).set_index("Metric")
        st.dataframe(risk_rows, width="stretch")
        render_bottom_nav("Phase 9 — Risk Management")
    
    
    # ════════════════════════════════════════════════════════════════════════════
    #  PHASE 10 — FACTOR MODELS
    # ════════════════════════════════════════════════════════════════════════════


