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

def render_phase_10(START, END, selected_tickers, api_key):
        st.markdown("<span class='phase-badge' style='background:#76ff03;color:#0a0a0f'>Phase 10</span>", unsafe_allow_html=True)
        st.markdown("## Factor Models")
        st.markdown(f"<p class='section-label'>CAPM · alpha · beta · rolling exposure · {START} → {END}</p>", unsafe_allow_html=True)
    
        with st.expander("101 — What is alpha and why is it so hard to find?", expanded=False):
            st.markdown("""
    <div class='explainer-box'>
    <h4>Decomposing returns: what did you actually earn?</h4>
    
    Not all returns are equal. Some of your return comes from just riding the market up.
    The part that's <i>above and beyond</i> what the market explains is called <b>alpha</b>.
    Finding real alpha is the entire job of a quant fund — and it's extremely hard.
    
    <br>
    
    <b>CAPM: the simplest factor model</b><br>
    The Capital Asset Pricing Model (1964) says any asset's return can be decomposed as:
    <span class='formula'>Rₐ = α + β × Rₘ + ε</span>
    Where Rₐ = asset return, Rₘ = market return (SPY), ε = unexplained noise.
    <span class='rule'><b>β (beta)</b>: sensitivity to the market. β=1.2 means when SPY moves 1%, asset moves 1.2%.</span>
    <span class='rule'><b>α (alpha)</b>: the intercept. Returns you earn regardless of market direction — the true edge.</span>
    <span class='rule'><b>R²</b>: how much of the return is explained by the market. High R² = mostly market-driven.</span>
    
    <br>
    
    <b>Beta in practice</b>
    <span class='rule'><b>β &lt; 1</b>: defensive. Moves less than the market. Utilities, consumer staples.</span>
    <span class='rule'><b>β ≈ 1</b>: tracks the market closely. Large diversified ETFs.</span>
    <span class='rule'><b>β &gt; 1</b>: aggressive. Amplifies market moves. Tech stocks, leveraged ETFs.</span>
    <span class='rule'><b>β &lt; 0</b>: hedges. Moves opposite the market. Gold sometimes, some bonds.</span>
    
    <br>
    
    <b>Rolling beta</b><br>
    Beta isn't constant — it changes over time. A stock might be low-beta during bull markets
    and high-beta during crashes (exactly when you don't want it). Rolling beta shows this.
    
    <br>
    
    <b>Why most "alpha" is just hidden beta</b><br>
    A common mistake: claiming alpha when you're just exposed to a risk factor.
    <span class='rule'>Strategy returns 15%/year? Before declaring alpha, ask: did it just hold high-beta stocks in a bull market?</span>
    <span class='rule'>True alpha = positive return even after accounting for all known risk factors.</span>
    Real alpha is rare. Most professional managers don't generate it net of fees.
    The Fama-French 3-factor model adds size (small vs large) and value (cheap vs expensive) factors.
    Many strategies that looked like alpha were just small-cap or value factor exposure.
    
    </div>
    """, unsafe_allow_html=True)
    
        col_t, col_b, col_rw, _ = st.columns([1, 1, 1, 3])
        with col_t:
            fm_ticker = st.selectbox("Asset to analyse", options=list(TICKER_OPTIONS.keys()), index=4, key="fm_ticker")
        with col_b:
            benchmark = st.selectbox("Benchmark", ["SPY", "QQQ"], index=0, key="fm_bench")
        with col_rw:
            roll_win  = st.number_input("Rolling window (days)", min_value=30, max_value=252, value=63, step=21)
    
        with st.spinner("Running regressions…"):
            prices_a = load_prices(fm_ticker,  START, END)
            prices_b = load_prices(benchmark,  START, END)
            common   = prices_a.index.intersection(prices_b.index)
            ra = np.log(prices_a.loc[common] / prices_a.loc[common].shift(1)).dropna()
            rb = np.log(prices_b.loc[common] / prices_b.loc[common].shift(1)).dropna()
            common2 = ra.index.intersection(rb.index)
            ra, rb  = ra.loc[common2], rb.loc[common2]
    
            # Full-period OLS
            X   = sm.add_constant(rb)
            ols = sm.OLS(ra, X).fit()
            alpha_daily = ols.params.iloc[0]
            beta_full   = ols.params.iloc[1]
            r_squared   = ols.rsquared
            alpha_ann   = alpha_daily * 252
            t_alpha     = ols.tvalues.iloc[0]
            p_alpha     = ols.pvalues.iloc[0]
    
            # Rolling beta & alpha
            roll_beta  = pd.Series(np.nan, index=ra.index)
            roll_alpha = pd.Series(np.nan, index=ra.index)
            for i in range(roll_win, len(ra)+1):
                window_a = ra.iloc[i-roll_win:i]
                window_b = rb.iloc[i-roll_win:i]
                Xw = sm.add_constant(window_b)
                try:
                    m = sm.OLS(window_a, Xw).fit()
                    roll_beta.iloc[i-1]  = m.params.iloc[1]
                    roll_alpha.iloc[i-1] = m.params.iloc[0] * 252
                except Exception:
                    pass
    
            # Residual (alpha) cumulative return
            fitted       = alpha_daily + beta_full * rb
            residuals    = ra - fitted
            resid_cum    = (1 + residuals).cumprod()
            ra_cum       = (1 + ra).cumprod()
            rb_cum       = (1 + rb).cumprod()
    
        # ── KPIs ───────────────────────────────────────────────────────────────────
        st.markdown("<br>", unsafe_allow_html=True)
        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("Beta (β)",        f"{beta_full:.3f}",    f"vs {benchmark}")
        c2.metric("Alpha (α) ann.",  f"{alpha_ann:.2%}",    f"t={t_alpha:.2f}, p={p_alpha:.3f}")
        c3.metric("R²",              f"{r_squared:.2%}",    f"{r_squared:.0%} explained by {benchmark}")
        c4.metric("Ann. Return",     f"{ra.mean()*252:.2%}", fm_ticker.replace("-USD",""))
        c5.metric("Beta-adj. Return",f"{(ra.mean()-beta_full*rb.mean())*252:.2%}", "return beyond market beta")
    
        st.markdown("<br>", unsafe_allow_html=True)
    
        # ── Scatter: asset vs market ───────────────────────────────────────────────
        st.markdown("<p class='section-label'>Return scatter vs benchmark</p>", unsafe_allow_html=True)
        fig_sc = go.Figure()
        fig_sc.add_trace(go.Scatter(x=rb.values, y=ra.values, mode="markers",
            marker=dict(color=TICKER_OPTIONS.get(fm_ticker,"#00b4ff"), size=3, opacity=0.5),
            hovertemplate=f"{benchmark}: %{{x:.2%}}<br>{fm_ticker}: %{{y:.2%}}<extra></extra>",
            name="Daily returns"))
        x_line = np.linspace(rb.min(), rb.max(), 100)
        y_line = alpha_daily + beta_full * x_line
        fig_sc.add_trace(go.Scatter(x=x_line, y=y_line, mode="lines",
            line=dict(color="#f5c518", width=1.5), name=f"β={beta_full:.2f} fit"))
        fig_sc.add_vline(x=0, line=dict(color="#2a2d3a", width=0.8))
        fig_sc.add_hline(y=0, line=dict(color="#2a2d3a", width=0.8))
        fig_sc.update_layout(**PLOTLY_THEME, height=360,
                             xaxis_title=f"{benchmark} daily return",
                             yaxis_title=f"{fm_ticker.replace('-USD','')} daily return",
                             legend=dict(orientation="h", y=1.05, x=0, font=dict(size=10), bgcolor="rgba(0,0,0,0)"))
        fig_sc.update_xaxes(tickformat=".1%")
        fig_sc.update_yaxes(tickformat=".1%")
        st.plotly_chart(fig_sc, width="stretch")
        chart_caption(ai_insight(
            f"CAPM scatter for {fm_ticker} versus {benchmark}. "
            f"Full-period beta is {beta_full:.3f}, annualized alpha is {alpha_ann:.2%}, and R-squared is {r_squared:.2%}.",
            api_key) or
            f"The slope of the fitted line is beta: how strongly the asset tends to move with the benchmark. "
            f"If points cluster tightly around the line, most of the asset's behavior is explained by market exposure rather than unique alpha.")
    
        # ── Rolling beta ───────────────────────────────────────────────────────────
        st.markdown(f"<p class='section-label'>Rolling {roll_win}-day beta and alpha</p>", unsafe_allow_html=True)
        fig_rb = make_subplots(rows=2, cols=1, shared_xaxes=True,
                               row_heights=[0.5, 0.5], vertical_spacing=0.04)
        fig_rb.add_trace(go.Scatter(x=roll_beta.index, y=roll_beta.values,
            line=dict(color="#00b4ff", width=1.2), name="Rolling β",
            hovertemplate="β: %{y:.3f}<extra></extra>"), row=1, col=1)
        fig_rb.add_hline(y=1, line=dict(color="#2a2d3a", dash="dot", width=0.8), row=1, col=1)
        fig_rb.add_hline(y=beta_full, line=dict(color="#f5c518", dash="dot", width=1),
                         annotation_text=f"Full-period β={beta_full:.2f}",
                         annotation_font=dict(color="#f5c518", size=9), row=1, col=1)
        fig_rb.add_trace(go.Scatter(x=roll_alpha.index, y=roll_alpha.values,
            fill="tozeroy", fillcolor="rgba(0,255,136,0.07)",
            line=dict(color="#00ff88", width=1.2), name="Rolling α (ann.)",
            hovertemplate="α: %{y:.2%}<extra></extra>"), row=2, col=1)
        fig_rb.add_hline(y=0, line=dict(color="#2a2d3a", width=0.8), row=2, col=1)
        fig_rb.update_layout(**PLOTLY_THEME, height=420,
                             legend=dict(orientation="h", y=1.02, x=0, font=dict(size=10), bgcolor="rgba(0,0,0,0)"),
                             hovermode="x unified")
        fig_rb.update_yaxes(gridcolor="#161820", title_text="Beta", row=1)
        fig_rb.update_yaxes(gridcolor="#161820", tickformat=".0%", title_text="Alpha (ann.)", row=2)
        fig_rb.update_xaxes(gridcolor="#161820")
        st.plotly_chart(fig_rb, width="stretch")
        chart_caption(ai_insight(
            f"Rolling beta and alpha for {fm_ticker} relative to {benchmark} with a {roll_win}-day window. "
            f"Full-period beta is {beta_full:.3f} and annualized alpha is {alpha_ann:.2%}.",
            api_key) or
            f"Beta is not fixed, so the top panel shows whether market sensitivity rose or fell over time. "
            f"The bottom panel shows when the asset delivered returns above or below what its market exposure alone would imply.")
    
        # ── Cumulative alpha (residuals) ───────────────────────────────────────────
        st.markdown("<p class='section-label'>Cumulative alpha (returns unexplained by market)</p>", unsafe_allow_html=True)
        fig_resid = go.Figure()
        fig_resid.add_trace(go.Scatter(x=rb_cum.index, y=rb_cum.values,
            name=benchmark, line=dict(color="#5a6070", width=1.2),
            hovertemplate=f"{benchmark}: $%{{y:.3f}}<extra></extra>"))
        fig_resid.add_trace(go.Scatter(x=ra_cum.index, y=ra_cum.values,
            name=fm_ticker.replace("-USD",""), line=dict(color=TICKER_OPTIONS.get(fm_ticker,"#00b4ff"), width=1.2),
            hovertemplate=f"{fm_ticker}: $%{{y:.3f}}<extra></extra>"))
        fig_resid.add_trace(go.Scatter(x=resid_cum.index, y=resid_cum.values,
            name="Cumulative alpha (residual)", line=dict(color="#00ff88", width=2),
            hovertemplate="Alpha: $%{y:.3f}<extra></extra>"))
        fig_resid.add_hline(y=1, line=dict(color="#2a2d3a", dash="dot", width=0.8))
        fig_resid.update_layout(**PLOTLY_THEME, height=360,
                                legend=dict(orientation="h", y=1.05, x=0, font=dict(size=10), bgcolor="rgba(0,0,0,0)"),
                                hovermode="x unified", yaxis_title="Growth of $1")
        st.plotly_chart(fig_resid, width="stretch")
        chart_caption(ai_insight(
            f"Cumulative alpha decomposition for {fm_ticker} versus {benchmark}. "
            f"Annualized alpha is {alpha_ann:.2%}, beta is {beta_full:.3f}, and benchmark explained return share is {r_squared:.2%}.",
            api_key) or
            f"The residual line is the portion of return left after removing market beta. "
            f"If that line trends upward persistently, the asset delivered gains beyond simple market exposure during this sample.")
        render_bottom_nav("Phase 10 — Factor Models")
    
    
    # ════════════════════════════════════════════════════════════════════════════
    #  PHASE 11 — STATISTICAL RIGOR
    # ════════════════════════════════════════════════════════════════════════════


