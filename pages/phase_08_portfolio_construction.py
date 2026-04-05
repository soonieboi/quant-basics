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

def render_phase_8(START, END, selected_tickers, api_key):
        st.markdown("<span class='phase-badge' style='background:#4fc3f7;color:#0a0a0f'>Phase 8</span>", unsafe_allow_html=True)
        st.markdown("## Portfolio Construction")
        st.markdown(f"<p class='section-label'>Correlation · efficient frontier · mean-variance optimisation · {START} → {END}</p>", unsafe_allow_html=True)
    
        with st.expander("101 — Don't put all your eggs in one basket (the math)", expanded=False):
            st.markdown("""
    <div class='explainer-box'>
    <h4>Modern Portfolio Theory — Markowitz (1952)</h4>
    
    Harry Markowitz won the Nobel Prize for showing that combining assets can reduce risk
    <i>without reducing expected return</i> — as long as the assets aren't perfectly correlated.
    This is the mathematical foundation of diversification.
    
    <br>
    
    <b>Correlation: the key number</b>
    <span class='formula'>Correlation ranges from −1 to +1</span>
    <span class='rule'><b class='bad'>+1</b>: assets move in perfect lockstep. No diversification benefit.</span>
    <span class='rule'><b>0</b>: assets move independently. Maximum diversification.</span>
    <span class='rule'><b class='good'>−1</b>: assets move opposite. Combining them eliminates all risk (theoretically).</span>
    Most assets have positive correlation (they all fall in a crash), which is why diversification
    works in normal times but fails exactly when you need it most.
    
    <br>
    
    <b>The Efficient Frontier</b><br>
    For any set of assets, there's a curve of portfolios that maximise return for a given level of risk.
    Portfolios on this curve are called <b>efficient</b> — you can't do better without taking more risk.
    <span class='rule'><b>Minimum Variance Portfolio</b>: the leftmost point. Lowest possible volatility.</span>
    <span class='rule'><b>Maximum Sharpe Portfolio</b> (tangency portfolio): highest return per unit of risk.</span>
    Any portfolio inside the frontier is suboptimal — you're taking unnecessary risk.
    
    <br>
    
    <b>How optimisation works</b>
    <span class='formula'>Maximise: w · μ − λ · wᵀΣw</span>
    <span class='formula'>Subject to: Σwᵢ = 1, wᵢ ≥ 0 (no shorting)</span>
    Where w = weights, μ = expected returns vector, Σ = covariance matrix, λ = risk aversion.
    The covariance matrix captures how all assets move together — not just pairwise.
    
    <br>
    
    <b>Limitations to be aware of</b><br>
    <span class='rule'>Garbage in, garbage out: the optimiser amplifies estimation errors. Noisy return estimates → wild weights.</span>
    <span class='rule'>Concentrated portfolios: max Sharpe often puts 80%+ in one asset. Use constraints in practice.</span>
    <span class='rule'>Correlation instability: correlations spike toward 1 in crises. Your "diversified" portfolio all falls together.</span>
    <span class='rule'>In practice: many funds use equal weight or risk parity instead of mean-variance due to these issues.</span>
    
    </div>
    """, unsafe_allow_html=True)
    
        pc_tickers = st.multiselect("Assets to include", options=list(TICKER_OPTIONS.keys()),
                                     default=["SPY", "QQQ", "AAPL", "MSFT", "NVDA", "BTC-USD"],
                                     key="pc_tickers")
        if len(pc_tickers) < 2:
            st.warning("Select at least 2 assets.")
            st.stop()
    
        with st.spinner("Loading data and optimising…"):
            price_dict = {}
            for t in pc_tickers:
                p = load_prices(t, START, END)
                if len(p) > 50:
                    price_dict[t] = p
    
            prices_df = pd.DataFrame(price_dict).dropna()
            ret_df    = np.log(prices_df / prices_df.shift(1)).dropna()
            mu_vec    = ret_df.mean() * 252
            cov_mat   = ret_df.cov() * 252
            n_assets  = len(price_dict)
            labels    = list(price_dict.keys())
    
            # ── Efficient frontier via random portfolios ───────────────────────────
            np.random.seed(42)
            n_sim = 3000
            sim_ret, sim_vol, sim_sharpe, sim_weights = [], [], [], []
            for _ in range(n_sim):
                w = np.random.dirichlet(np.ones(n_assets))
                r = float(np.dot(w, mu_vec))
                v = float(np.sqrt(w @ cov_mat.values @ w))
                sim_ret.append(r); sim_vol.append(v)
                sim_sharpe.append(r / v if v > 0 else 0)
                sim_weights.append(w)
    
            # ── Optimised portfolios ───────────────────────────────────────────────
            def neg_sharpe(w):
                r = float(np.dot(w, mu_vec))
                v = float(np.sqrt(w @ cov_mat.values @ w))
                return -(r / v) if v > 0 else 0
    
            def portfolio_vol(w):
                return float(np.sqrt(w @ cov_mat.values @ w))
    
            constraints = {"type": "eq", "fun": lambda w: np.sum(w) - 1}
            bounds = [(0, 1)] * n_assets
            w0 = np.ones(n_assets) / n_assets
    
            res_sharpe = minimize(neg_sharpe, w0, method="SLSQP",
                                  bounds=bounds, constraints=constraints)
            res_minvol = minimize(portfolio_vol, w0, method="SLSQP",
                                  bounds=bounds, constraints=constraints)
    
            w_maxsh  = res_sharpe.x
            w_minvol = res_minvol.x
            w_equal  = np.ones(n_assets) / n_assets
    
            def port_metrics(w):
                r = float(np.dot(w, mu_vec))
                v = float(np.sqrt(w @ cov_mat.values @ w))
                return r, v, r/v if v > 0 else 0
    
            r_ms, v_ms, s_ms   = port_metrics(w_maxsh)
            r_mv, v_mv, s_mv   = port_metrics(w_minvol)
            r_eq, v_eq, s_eq   = port_metrics(w_equal)
    
        # ── Correlation heatmap ────────────────────────────────────────────────────
        st.markdown("<p class='section-label'>Return correlation matrix</p>", unsafe_allow_html=True)
        corr_mat = ret_df.corr()
        short_labels = [l.replace("-USD", "") for l in labels]
        fig_corr = go.Figure(go.Heatmap(
            z=corr_mat.values,
            x=short_labels, y=short_labels,
            colorscale=[[0, "#ff4466"], [0.5, "var(--qb-surface-alt)"], [1, "#00ff88"]],
            zmin=-1, zmax=1,
            text=[[f"{v:.2f}" for v in row] for row in corr_mat.values],
            texttemplate="%{text}",
            hovertemplate="%{x} vs %{y}: %{z:.2f}<extra></extra>",
            colorbar=dict(tickfont=dict(family="JetBrains Mono", size=10)),
        ))
        fig_corr.update_layout(**PLOTLY_THEME, height=max(300, n_assets * 45))
        fig_corr.update_xaxes(gridcolor="var(--qb-border)")
        fig_corr.update_yaxes(gridcolor="var(--qb-border)")
        st.plotly_chart(fig_corr, width="stretch")
        chart_caption(ai_insight(
            f"Correlation matrix for portfolio construction using {', '.join(short_labels)}. "
            f"Lowest and highest relationships are visible across {n_assets} assets from {START} to {END}.",
            api_key) or
            f"Green cells mean assets tended to move together, while darker or redder cells indicate weaker or negative relationships. "
            f"Lower correlation is what creates diversification benefit, because the portfolio is less dependent on any single asset moving well.")
    
        # ── Efficient frontier scatter ─────────────────────────────────────────────
        st.markdown("<p class='section-label'>Efficient frontier (3,000 random portfolios)</p>", unsafe_allow_html=True)
        fig_ef = go.Figure()
        fig_ef.add_trace(go.Scatter(
            x=sim_vol, y=sim_ret, mode="markers",
            marker=dict(color=sim_sharpe, colorscale=[[0,"#ff4466"],[0.5,"var(--qb-surface-alt)"],[1,"#00ff88"]],
                        size=3, opacity=0.6,
                        colorbar=dict(title="Sharpe", tickfont=dict(family="JetBrains Mono", size=9))),
            hovertemplate="Vol: %{x:.2%}  Ret: %{y:.2%}<extra></extra>",
            showlegend=False))
        # Special portfolios
        for (lbl, r, v, clr, sym) in [
            (f"Max Sharpe ({s_ms:.2f})", r_ms, v_ms, "#f5c518", "star"),
            (f"Min Vol",                  r_mv, v_mv, "#00ff88", "diamond"),
            (f"Equal Weight",             r_eq, v_eq, "#00b4ff", "circle"),
        ]:
            fig_ef.add_trace(go.Scatter(x=[v], y=[r], mode="markers+text", name=lbl,
                marker=dict(color=clr, size=14, symbol=sym,
                            line=dict(color="#0a0a0f", width=1)),
                text=[lbl], textposition="top center",
                textfont=dict(family="JetBrains Mono", size=9, color=clr)))
        # Individual assets
        for i, lbl in enumerate(labels):
            fig_ef.add_trace(go.Scatter(
                x=[float(np.sqrt(cov_mat.values[i,i]))],
                y=[float(mu_vec.iloc[i])],
                mode="markers+text", name=lbl.replace("-USD",""),
                marker=dict(color=TICKER_OPTIONS.get(lbl, "var(--qb-muted)"), size=8, symbol="x"),
                text=[lbl.replace("-USD","")], textposition="top right",
                textfont=dict(family="JetBrains Mono", size=8, color="var(--qb-muted)")))
        fig_ef.update_layout(**PLOTLY_THEME, height=440,
                             legend=dict(orientation="h", y=1.05, x=0, font=dict(size=9), bgcolor="rgba(0,0,0,0)"),
                             xaxis_title="Annualised Volatility", yaxis_title="Annualised Return")
        fig_ef.update_xaxes(tickformat=".0%")
        fig_ef.update_yaxes(tickformat=".0%")
        st.plotly_chart(fig_ef, width="stretch")
        chart_caption(ai_insight(
            f"Efficient frontier for {', '.join(short_labels)}. "
            f"Max Sharpe portfolio return {r_ms:.2%}, vol {v_ms:.2%}, Sharpe {s_ms:.2f}. "
            f"Min-vol portfolio return {r_mv:.2%}, vol {v_mv:.2%}, Sharpe {s_mv:.2f}.",
            api_key) or
            f"Each dot is a random portfolio, and the best region is the upper-left direction: higher return for lower risk. "
            f"The highlighted max-Sharpe point is the most efficient tradeoff in this sample, while min-vol is the safest mix.")
    
        # ── Portfolio weights ──────────────────────────────────────────────────────
        st.markdown("<p class='section-label'>Optimal portfolio weights</p>", unsafe_allow_html=True)
        fig_w = go.Figure()
        for w_arr, name, color in [(w_maxsh,"Max Sharpe","#f5c518"),
                                    (w_minvol,"Min Vol","#00ff88"),
                                    (w_equal,"Equal Weight","#00b4ff")]:
            fig_w.add_trace(go.Bar(name=name, x=short_labels, y=w_arr, marker_color=color,
                                   text=[f"{v:.0%}" for v in w_arr], textposition="outside"))
        fig_w.update_layout(**PLOTLY_THEME, height=320, barmode="group",
                            legend=dict(orientation="h", y=1.05, x=0, font=dict(size=10), bgcolor="rgba(0,0,0,0)"),
                            yaxis_title="Weight")
        fig_w.update_yaxes(tickformat=".0%", gridcolor="var(--qb-border)")
        st.plotly_chart(fig_w, width="stretch")
        chart_caption(ai_insight(
            f"Portfolio weights for max Sharpe, min volatility, and equal weight portfolios across {', '.join(short_labels)}. "
            f"Max Sharpe ratio is {s_ms:.2f} and min-vol ratio is {s_mv:.2f}.",
            api_key) or
            f"These bars show how the optimizer allocates capital across assets. "
            f"If one portfolio is heavily concentrated, that means the sample estimates think one asset contributes disproportionately to return or diversification.")
    
        # ── Summary table ──────────────────────────────────────────────────────────
        st.markdown("<p class='section-label'>Portfolio summary</p>", unsafe_allow_html=True)
        summ = pd.DataFrame({
            "Portfolio":   ["Max Sharpe", "Min Volatility", "Equal Weight"],
            "Ann. Return": [f"{r_ms:.2%}", f"{r_mv:.2%}", f"{r_eq:.2%}"],
            "Ann. Vol":    [f"{v_ms:.2%}", f"{v_mv:.2%}", f"{v_eq:.2%}"],
            "Sharpe":      [f"{s_ms:.2f}", f"{s_mv:.2f}", f"{s_eq:.2f}"],
        }).set_index("Portfolio")
        st.dataframe(summ, width="stretch")
        render_bottom_nav("Phase 8 — Portfolio Construction")
    
    
    # ════════════════════════════════════════════════════════════════════════════
    #  PHASE 9 — RISK MANAGEMENT
    # ════════════════════════════════════════════════════════════════════════════
