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

def render_phase_6(START, END, selected_tickers, api_key):
        st.markdown("<span class='phase-badge' style='background:#ff7043'>Phase 6</span>", unsafe_allow_html=True)
        st.markdown("## Walk-Forward Validation")
        st.markdown(f"<p class='section-label'>Out-of-sample testing · overfitting · {START} → {END}</p>", unsafe_allow_html=True)
    
        with st.expander("101 — Why backtests lie and how to catch it", expanded=False):
            st.markdown("""
    <div class='explainer-box'>
    <h4>The most dangerous trap in quant finance: overfitting</h4>
    
    You've built strategies that look great on the 2020–2024 data. But there's a problem:
    you looked at that data while building them. Consciously or not, you've been tuning
    parameters to fit what already happened. This is called <b class='bad'>overfitting</b> or <b class='bad'>data snooping</b>.
    
    <br>
    
    <b>A simple thought experiment</b><br>
    If you test 100 random SMA window combinations on the same data, some will look amazing —
    not because they capture real market structure, but because they got lucky on this particular data.
    The more parameters you test, the more likely you are to find something that "works" by chance.
    This is called the <b>multiple testing problem</b>.
    
    <br>
    
    <b>In-sample vs Out-of-sample</b>
    <span class='rule'><b class='warn'>In-sample (IS)</b>: data used to find/tune parameters. Results are optimistic — you're fitting to noise.</span>
    <span class='rule'><b class='good'>Out-of-sample (OOS)</b>: data the strategy has never seen. This is the honest test.</span>
    A strategy that works in-sample but fails out-of-sample is overfit. It learned the noise, not the signal.
    
    <br>
    
    <b>Walk-Forward Analysis</b><br>
    Instead of a single train/test split, we roll a window through time:
    <span class='formula'>Step 1: Train on months 1–12, test on month 13</span>
    <span class='formula'>Step 2: Train on months 2–13, test on month 14</span>
    <span class='formula'>Step 3: Train on months 3–14, test on month 15 … and so on</span>
    Each test period uses parameters optimized on data it hasn't seen yet.
    This is the closest you can get to simulating live trading in a backtest.
    
    <br>
    
    <b>What to look for</b>
    <span class='rule'><b class='good'>Good sign</b>: OOS Sharpe is lower than IS Sharpe, but still positive and meaningful.</span>
    <span class='rule'><b class='warn'>Warning</b>: OOS Sharpe is much lower but positive. Strategy has some edge, but IS results are inflated.</span>
    <span class='rule'><b class='bad'>Red flag</b>: OOS Sharpe is negative or near zero. The strategy found noise, not signal.</span>
    
    <br>
    
    <b>The IS/OOS Sharpe ratio</b>
    <span class='formula'>Degradation = OOS Sharpe / IS Sharpe</span>
    Industry rule of thumb: if OOS is less than 50% of IS, be very skeptical.
    A well-designed strategy typically degrades to 50–80% of its IS Sharpe out-of-sample.
    
    </div>
    """, unsafe_allow_html=True)
    
        # ── Controls ───────────────────────────────────────────────────────────────
        col_t, col_sp, col_n, _ = st.columns([1, 1, 1, 3])
        with col_t:
            wf_ticker = st.selectbox("Ticker", options=list(TICKER_OPTIONS.keys()), index=0, key="wf_ticker")
        with col_sp:
            is_pct = st.slider("In-sample %", min_value=40, max_value=80, value=70, step=5,
                               help="% of data used for training. Remaining is out-of-sample test.")
        with col_n:
            n_fast_options = [10, 20, 30, 50, 60, 80, 100]
            n_slow_options = [50, 100, 150, 200, 250, 300]
    
        # ── Compute ────────────────────────────────────────────────────────────────
        with st.spinner("Running grid search + walk-forward…"):
            prices  = load_prices(wf_ticker, START, END)
            log_ret = np.log(prices / prices.shift(1))
            n       = len(prices)
            split   = int(n * is_pct / 100)
    
            prices_is  = prices.iloc[:split]
            prices_oos = prices.iloc[split:]
            ret_is     = log_ret.iloc[:split]
            ret_oos    = log_ret.iloc[split:]
    
            # ── Grid search on in-sample ───────────────────────────────────────────
            results = []
            for fast in n_fast_options:
                for slow in n_slow_options:
                    if fast >= slow:
                        continue
                    sig = sma_signal(prices_is, fast, slow).reindex(prices_is.index).fillna(0)
                    r   = (ret_is * sig).dropna()
                    if len(r) < 50:
                        continue
                    m = compute_metrics(r)
                    results.append({"fast": fast, "slow": slow, "sharpe_is": m["sharpe"],
                                     "return_is": m["ann_return"], "dd_is": m["max_dd"]})
    
            df_grid = pd.DataFrame(results).sort_values("sharpe_is", ascending=False)
            best    = df_grid.iloc[0]
            worst   = df_grid.iloc[-1]
    
            # ── Apply best IS params to OOS ────────────────────────────────────────
            sig_best_oos  = sma_signal(prices, int(best["fast"]), int(best["slow"])).reindex(prices_oos.index).fillna(0)
            sig_worst_oos = sma_signal(prices, int(worst["fast"]), int(worst["slow"])).reindex(prices_oos.index).fillna(0)
    
            ret_best_oos,  bh_oos  = strategy_returns(prices_oos, sig_best_oos)
            ret_worst_oos, _       = strategy_returns(prices_oos, sig_worst_oos)
            ret_best_is,   bh_is   = strategy_returns(prices_is,
                sma_signal(prices_is, int(best["fast"]), int(best["slow"])).reindex(prices_is.index).fillna(0))
    
            m_bh_is   = compute_metrics(bh_is)
            m_bh_oos  = compute_metrics(bh_oos)
            m_best_is = compute_metrics(ret_best_is)
            m_best_oos  = compute_metrics(ret_best_oos)
            m_worst_oos = compute_metrics(ret_worst_oos)
    
            degradation = m_best_oos["sharpe"] / m_best_is["sharpe"] if m_best_is["sharpe"] != 0 else 0
    
        # ── KPIs ───────────────────────────────────────────────────────────────────
        st.markdown("<br>", unsafe_allow_html=True)
        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("Best params (IS)",  f"SMA {int(best['fast'])}/{int(best['slow'])}", f"IS Sharpe: {best['sharpe_is']:.2f}")
        c2.metric("IS Sharpe",         f"{m_best_is['sharpe']:.2f}",  f"IS period: {is_pct}% of data")
        c3.metric("OOS Sharpe",        f"{m_best_oos['sharpe']:.2f}", f"OOS period: {100-is_pct}% of data")
        c4.metric("Degradation",       f"{degradation:.0%}",
                  "good ≥ 50%" if degradation >= 0.5 else "⚠ suspect < 50%")
        c5.metric("Grid combos tested", str(len(df_grid)), f"best: {int(best['fast'])}/{int(best['slow'])}")
    
        st.markdown("<br>", unsafe_allow_html=True)
    
        # ── IS vs OOS equity curves ────────────────────────────────────────────────
        st.markdown("<p class='section-label'>In-sample vs out-of-sample performance</p>", unsafe_allow_html=True)
        fig = make_subplots(rows=1, cols=2,
                            subplot_titles=(f"In-Sample ({is_pct}%)", f"Out-of-Sample ({100-is_pct}%)"))
    
        # IS panel
        fig.add_trace(go.Scatter(x=m_bh_is["cumulative"].index, y=m_bh_is["cumulative"].values,
            name="B&H (IS)", line=dict(color="#5a6070", width=1.2),
            hovertemplate="B&H: $%{y:.3f}<extra></extra>"), row=1, col=1)
        fig.add_trace(go.Scatter(x=m_best_is["cumulative"].index, y=m_best_is["cumulative"].values,
            name=f"Best SMA {int(best['fast'])}/{int(best['slow'])} (IS)",
            line=dict(color="#00ff88", width=2),
            hovertemplate="Best IS: $%{y:.3f}<extra></extra>"), row=1, col=1)
    
        # OOS panel
        fig.add_trace(go.Scatter(x=m_bh_oos["cumulative"].index, y=m_bh_oos["cumulative"].values,
            name="B&H (OOS)", line=dict(color="#5a6070", width=1.2),
            hovertemplate="B&H: $%{y:.3f}<extra></extra>"), row=1, col=2)
        fig.add_trace(go.Scatter(x=m_best_oos["cumulative"].index, y=m_best_oos["cumulative"].values,
            name=f"Best params OOS", line=dict(color="#00ff88", width=2),
            hovertemplate="Best OOS: $%{y:.3f}<extra></extra>"), row=1, col=2)
        fig.add_trace(go.Scatter(x=m_worst_oos["cumulative"].index, y=m_worst_oos["cumulative"].values,
            name=f"Worst params OOS", line=dict(color="#ff4466", width=1.2, dash="dot"),
            hovertemplate="Worst OOS: $%{y:.3f}<extra></extra>"), row=1, col=2)
    
        fig.update_layout(**PLOTLY_THEME, height=380,
                          legend=dict(orientation="h", y=1.08, x=0, font=dict(size=9), bgcolor="rgba(0,0,0,0)"),
                          hovermode="x unified")
        fig.update_yaxes(gridcolor="#161820", title_text="Growth of $1", row=1, col=1)
        fig.update_yaxes(gridcolor="#161820", title_text="Growth of $1", row=1, col=2)
        fig.update_xaxes(gridcolor="#161820")
        # Add vertical split line annotation
        split_date = str(prices.index[split].date())
        fig.add_vline(x=split_date, line=dict(color="#f5c518", width=1, dash="dash"))
        st.plotly_chart(fig, width="stretch")
        chart_caption(ai_insight(
            f"Walk-forward validation on {wf_ticker}. Best in-sample params: SMA {int(best['fast'])}/{int(best['slow'])}. "
            f"In-sample Sharpe: {m_best_is['sharpe']:.2f}. Out-of-sample Sharpe: {m_best_oos['sharpe']:.2f}. "
            f"Degradation: {degradation:.0%}. Yellow dashed line marks the IS/OOS split.",
            api_key) or
            f"The yellow dashed line marks where in-sample (training) ends and out-of-sample (test) begins. "
            f"The best parameters found in-sample (SMA {int(best['fast'])}/{int(best['slow'])}, Sharpe {m_best_is['sharpe']:.2f}) "
            f"{'held up well' if degradation >= 0.6 else 'degraded significantly' if degradation < 0.4 else 'partially held up'} "
            f"out-of-sample (Sharpe {m_best_oos['sharpe']:.2f}, {degradation:.0%} retention) — "
            f"{'suggesting real edge' if degradation >= 0.6 else 'suggesting possible overfitting'}.")
    
        # ── Grid search heatmap ────────────────────────────────────────────────────
        st.markdown("<p class='section-label'>In-sample grid search — Sharpe by SMA window pair</p>", unsafe_allow_html=True)
        pivot = df_grid.pivot(index="slow", columns="fast", values="sharpe_is")
        fig3 = go.Figure(go.Heatmap(
            z=pivot.values, x=[str(c) for c in pivot.columns], y=[str(r) for r in pivot.index],
            colorscale=[[0, "#ff4466"], [0.5, "#2a2d3a"], [1, "#00ff88"]],
            text=[[f"{v:.2f}" if not np.isnan(v) else "" for v in row] for row in pivot.values],
            texttemplate="%{text}", hovertemplate="Fast: %{x}  Slow: %{y}<br>Sharpe: %{z:.2f}<extra></extra>",
            colorbar=dict(tickfont=dict(family="JetBrains Mono", size=10)),
        ))
        fig3.update_layout(**PLOTLY_THEME, height=320,
                           xaxis_title="Fast SMA", yaxis_title="Slow SMA")
        st.plotly_chart(fig3, width="stretch")
        chart_caption(ai_insight(
            f"In-sample SMA grid search heatmap on {wf_ticker}. "
            f"Best pair: {int(best['fast'])}/{int(best['slow'])} with Sharpe {best['sharpe_is']:.2f}. "
            f"Worst pair: {int(worst['fast'])}/{int(worst['slow'])} with out-of-sample Sharpe {m_worst_oos['sharpe']:.2f}.",
            api_key) or
            f"Each cell is an SMA parameter pair tested on the training sample. "
            f"Bright clusters are more robust than a single isolated hotspot, because they suggest performance is less dependent on one lucky parameter choice.")
    
        # ── Grid results table ─────────────────────────────────────────────────────
        st.markdown("<p class='section-label'>All parameter combinations ranked by in-sample Sharpe</p>", unsafe_allow_html=True)
        df_display = df_grid.copy()
        df_display["fast"]      = df_display["fast"].astype(int)
        df_display["slow"]      = df_display["slow"].astype(int)
        df_display["sharpe_is"] = df_display["sharpe_is"].map("{:.2f}".format)
        df_display["return_is"] = df_display["return_is"].map("{:.2%}".format)
        df_display["dd_is"]     = df_display["dd_is"].map("{:.2%}".format)
        df_display.columns      = ["Fast", "Slow", "IS Sharpe", "IS Return", "IS Max DD"]
        st.dataframe(df_display.set_index("Fast"), width="stretch")
        render_bottom_nav("Phase 6 — Walk-Forward Validation")
    
    # ════════════════════════════════════════════════════════════════════════════
    #  PHASE 7 — POSITION SIZING
    # ════════════════════════════════════════════════════════════════════════════


