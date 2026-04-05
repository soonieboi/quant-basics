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

def render_phase_7(START, END, selected_tickers, api_key):
        st.markdown("<span class='phase-badge' style='background:#ffca28;color:#0a0a0f'>Phase 7</span>", unsafe_allow_html=True)
        st.markdown("## Position Sizing")
        st.markdown(f"<p class='section-label'>Kelly criterion · fixed fractional · {START} → {END}</p>", unsafe_allow_html=True)
    
        with st.expander("101 — How much of your capital should you bet?", expanded=False):
            st.markdown("""
    <div class='explainer-box'>
    <h4>The sizing problem: right strategy, wrong bet size</h4>
    
    You can have a genuinely profitable strategy and still blow up your account by betting too much.
    Position sizing is one of the most under-appreciated topics in trading.
    
    <br>
    
    <b>Fixed Fractional Sizing</b><br>
    The simplest rule: always risk X% of your current portfolio on each trade.
    <span class='formula'>position_size = portfolio_value × fraction</span>
    <span class='rule'>If fraction = 1.0: fully invested, no leverage — what we've been doing.</span>
    <span class='rule'>If fraction = 0.5: only half your capital is ever at risk.</span>
    <span class='rule'>If fraction = 2.0: 2× leverage — amplifies both gains and losses.</span>
    Reducing fraction lowers both returns AND volatility. The relationship isn't linear — halving
    your bet size more than halves your drawdown (because losses compound).
    
    <br>
    
    <b>The Kelly Criterion</b><br>
    Derived by John Kelly at Bell Labs in 1956, originally for information theory. It gives the
    mathematically optimal fraction to maximise long-run wealth growth.
    <span class='formula'>Kelly fraction f* = μ / σ²</span>
    Where μ = mean daily return, σ² = variance of daily returns (of the strategy, not the asset).
    <span class='rule'>Kelly maximises the geometric growth rate — equivalent to maximising log(wealth) over time.</span>
    <span class='rule'><b class='bad'>Full Kelly is extremely aggressive.</b> In practice it produces terrifying drawdowns.</span>
    <span class='rule'><b class='good'>Half Kelly (f*/2) or Quarter Kelly (f*/4)</b> is the industry standard — much smoother with ~75% of the growth.</span>
    The Kelly fraction is also the Sharpe ratio divided by the annualised vol — so a higher Sharpe
    strategy deserves a larger position. This makes intuitive sense.
    
    <br>
    
    <b>Leverage and the Kelly boundary</b><br>
    If Kelly says f* = 2.5, it means theoretically you should use 2.5× leverage.
    Most retail traders and even many funds cap at 1× (no leverage) or 1.5× max.
    Going beyond Kelly is provably suboptimal — your account will eventually go to zero.
    
    <br>
    
    <b>Why not always use Kelly?</b><br>
    Kelly assumes your return estimates are exact. They're not — they're estimated from noisy data.
    If your estimated μ is too high (overfit), full Kelly will over-bet and cause ruin.
    Half Kelly provides insurance against estimation error while capturing most of the benefit.
    
    </div>
    """, unsafe_allow_html=True)
    
        col_t, col_s, _ = st.columns([1, 1, 4])
        with col_t:
            ps_ticker = st.selectbox("Ticker", options=list(TICKER_OPTIONS.keys()), index=0, key="ps_ticker")
        with col_s:
            strategy_choice = st.selectbox("Strategy", ["SMA 50/200", "RSI 14 (30/70)", "Buy & Hold"], key="ps_strat")
    
        with st.spinner("Computing…"):
            prices  = load_prices(ps_ticker, START, END)
            log_ret = np.log(prices / prices.shift(1))
    
            if strategy_choice == "SMA 50/200":
                sig = sma_signal(prices, 50, 200).reindex(prices.index).fillna(0)
                base_ret, bh_ret = strategy_returns(prices, sig)
            elif strategy_choice == "RSI 14 (30/70)":
                sig, _ = rsi_signal(prices, 14, 30, 70)
                sig = sig.reindex(prices.index).fillna(0)
                base_ret, bh_ret = strategy_returns(prices, sig)
            else:
                base_ret = log_ret.dropna()
                bh_ret   = base_ret.copy()
    
            mu    = base_ret.mean()
            sigma2 = base_ret.var()
            kelly_f = mu / sigma2 if sigma2 > 0 else 1.0
            kelly_f_ann = kelly_f  # daily kelly
    
            fractions = [0.25, 0.5, 1.0, min(kelly_f * 0.5, 3.0), min(kelly_f, 4.0)]
            frac_labels = ["25%", "50%", "Full (1×)",
                           f"½ Kelly ({kelly_f*0.5:.2f}×)", f"Full Kelly ({kelly_f:.2f}×)"]
            colors_ps = ["var(--qb-disabled)", "var(--qb-muted)", "var(--qb-text)", "#00ff88", "#f5c518"]
    
            curves = {}
            metrics_ps = {}
            for f, lbl in zip(fractions, frac_labels):
                scaled = base_ret * f
                m = compute_metrics(scaled)
                curves[lbl] = m["cumulative"]
                metrics_ps[lbl] = m
    
        st.markdown("<br>", unsafe_allow_html=True)
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Kelly f*",         f"{kelly_f:.2f}×",        f"daily μ/σ²")
        c2.metric("½ Kelly",          f"{kelly_f*0.5:.2f}×",    "recommended in practice")
        c3.metric("Daily μ",          f"{mu*10000:.2f} bps",    f"{mu*252:.2%} ann.")
        c4.metric("Daily σ",          f"{np.sqrt(sigma2)*100:.2f}%", f"{np.sqrt(sigma2*252):.2%} ann.")
    
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("<p class='section-label'>Equity curves by position size</p>", unsafe_allow_html=True)
        fig = go.Figure()
        for (lbl, curve), color in zip(curves.items(), colors_ps):
            fig.add_trace(go.Scatter(x=curve.index, y=curve.values, name=lbl,
                line=dict(color=color, width=1.5 if "Kelly" in lbl else 1),
                hovertemplate=f"{lbl}: $%{{y:.3f}}<extra></extra>"))
        fig.update_layout(**PLOTLY_THEME, height=380,
                          legend=dict(orientation="h", y=1.05, x=0, font=dict(size=10), bgcolor="rgba(0,0,0,0)"),
                          hovermode="x unified", yaxis_title="Growth of $1")
        st.plotly_chart(fig, width="stretch")
        best_fraction = max(metrics_ps.items(), key=lambda item: item[1]["ann_return"])
        chart_caption(ai_insight(
            f"Position sizing on {ps_ticker} using {strategy_choice}. "
            f"Kelly fraction {kelly_f:.2f}x, half-Kelly {kelly_f*0.5:.2f}x. "
            f"Best ending growth came from {best_fraction[0]} with annual return {best_fraction[1]['ann_return']:.2%} and max drawdown {best_fraction[1]['max_dd']:.2%}.",
            api_key) or
            f"Each line is the same strategy with a different bet size. "
            f"Bigger sizing can raise returns fast, but it also deepens drawdowns, which is why half-Kelly is usually safer than full Kelly in practice.")
    
        st.markdown("<p class='section-label'>Return vs risk by fraction</p>", unsafe_allow_html=True)
        fig2 = make_subplots(rows=1, cols=3, subplot_titles=("Ann. Return", "Sharpe", "Max Drawdown"))
        lbls = list(metrics_ps.keys())
        clrs = colors_ps
        fig2.add_trace(go.Bar(x=lbls, y=[metrics_ps[l]["ann_return"] for l in lbls], marker_color=clrs,
                              text=[f"{metrics_ps[l]['ann_return']:.1%}" for l in lbls], textposition="outside"), row=1, col=1)
        fig2.add_trace(go.Bar(x=lbls, y=[metrics_ps[l]["sharpe"] for l in lbls], marker_color=clrs,
                              text=[f"{metrics_ps[l]['sharpe']:.2f}" for l in lbls], textposition="outside"), row=1, col=2)
        fig2.add_trace(go.Bar(x=lbls, y=[metrics_ps[l]["max_dd"] for l in lbls], marker_color=clrs,
                              text=[f"{metrics_ps[l]['max_dd']:.1%}" for l in lbls], textposition="outside"), row=1, col=3)
        fig2.update_layout(**PLOTLY_THEME, height=320, showlegend=False)
        fig2.update_yaxes(gridcolor="var(--qb-border)", tickformat=".0%", row=1, col=1)
        fig2.update_yaxes(gridcolor="var(--qb-border)", row=1, col=2)
        fig2.update_yaxes(gridcolor="var(--qb-border)", tickformat=".0%", row=1, col=3)
        st.plotly_chart(fig2, width="stretch")
        chart_caption(ai_insight(
            f"Return-risk tradeoff by position size on {ps_ticker} using {strategy_choice}. "
            f"Quarter Kelly, half Kelly, full 1x, half Kelly fraction {kelly_f*0.5:.2f}x, and full Kelly {kelly_f:.2f}x are compared.",
            api_key) or
            f"These bars show the core sizing tradeoff directly: more exposure usually lifts return, but drawdown grows quickly too. "
            f"The best practical choice is often the highest Sharpe or a near-max-return setting that still keeps drawdown tolerable.")
    
        st.markdown("<p class='section-label'>Full metrics by sizing</p>", unsafe_allow_html=True)
        rows_ps = [{"Fraction": lbl,
                    "Ann. Return": f"{m['ann_return']:.2%}",
                    "Ann. Vol":    f"{m['ann_vol']:.2%}",
                    "Sharpe":      f"{m['sharpe']:.2f}",
                    "Max DD":      f"{m['max_dd']:.2%}"}
                   for lbl, m in metrics_ps.items()]
        st.dataframe(pd.DataFrame(rows_ps).set_index("Fraction"), width="stretch")
        render_bottom_nav("Phase 7 — Position Sizing")
    
    
    # ════════════════════════════════════════════════════════════════════════════
    #  PHASE 8 — PORTFOLIO CONSTRUCTION
    # ════════════════════════════════════════════════════════════════════════════
