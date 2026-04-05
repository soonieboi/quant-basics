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
from pages.phase_06_walk_forward_validation import render_phase_6 as render_phase_6_page
from pages.phase_05_combining_signals import render_phase_5 as render_phase_5_page
from pages.phase_04_transaction_costs import render_phase_4 as render_phase_4_page
from pages.phase_03_rsi_mean_reversion import render_phase_3 as render_phase_3_page
from pages.phase_02_sma_crossover import render_phase_2 as render_phase_2_page
from pages.phase_01_asset_metrics import render_phase_1 as render_phase_1_page


def render_phase_1(START, END, selected_tickers, api_key):
    return render_phase_1_page(START, END, selected_tickers, api_key)

def render_phase_2(START, END, selected_tickers, api_key):
    return render_phase_2_page(START, END, selected_tickers, api_key)

def render_phase_3(START, END, selected_tickers, api_key):
    return render_phase_3_page(START, END, selected_tickers, api_key)

def render_phase_4(START, END, selected_tickers, api_key):
    return render_phase_4_page(START, END, selected_tickers, api_key)

def render_phase_5(START, END, selected_tickers, api_key):
    return render_phase_5_page(START, END, selected_tickers, api_key)

def render_phase_6(START, END, selected_tickers, api_key):
    return render_phase_6_page(START, END, selected_tickers, api_key)

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
            colors_ps = ["#3a4050", "#5a6070", "#c8cdd6", "#00ff88", "#f5c518"]
    
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
        fig2.update_yaxes(gridcolor="#161820", tickformat=".0%", row=1, col=1)
        fig2.update_yaxes(gridcolor="#161820", row=1, col=2)
        fig2.update_yaxes(gridcolor="#161820", tickformat=".0%", row=1, col=3)
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
            colorscale=[[0, "#ff4466"], [0.5, "#161820"], [1, "#00ff88"]],
            zmin=-1, zmax=1,
            text=[[f"{v:.2f}" for v in row] for row in corr_mat.values],
            texttemplate="%{text}",
            hovertemplate="%{x} vs %{y}: %{z:.2f}<extra></extra>",
            colorbar=dict(tickfont=dict(family="JetBrains Mono", size=10)),
        ))
        fig_corr.update_layout(**PLOTLY_THEME, height=max(300, n_assets * 45))
        fig_corr.update_xaxes(gridcolor="#161820")
        fig_corr.update_yaxes(gridcolor="#161820")
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
            marker=dict(color=sim_sharpe, colorscale=[[0,"#ff4466"],[0.5,"#2a2d3a"],[1,"#00ff88"]],
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
                marker=dict(color=TICKER_OPTIONS.get(lbl, "#5a6070"), size=8, symbol="x"),
                text=[lbl.replace("-USD","")], textposition="top right",
                textfont=dict(family="JetBrains Mono", size=8, color="#5a6070")))
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
        fig_w.update_yaxes(tickformat=".0%", gridcolor="#161820")
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


def render_phase_11(START, END, selected_tickers, api_key):
        st.markdown("<span class='phase-badge' style='background:#b48ead'>Phase 11</span>", unsafe_allow_html=True)
        st.markdown("## Statistical Rigor")
        st.markdown(f"<p class='section-label'>Bootstrap · Sharpe confidence intervals · multiple testing · {START} → {END}</p>", unsafe_allow_html=True)
    
        with st.expander("101 — How confident should you actually be?", expanded=False):
            st.markdown("""
    <div class='explainer-box'>
    <h4>A Sharpe of 0.8 doesn't mean what you think it means</h4>
    
    You've computed Sharpe ratios throughout this course. But a single number hides enormous uncertainty.
    With 4 years of daily data (~1000 observations), your Sharpe estimate has a wide confidence interval.
    
    <br>
    
    <b>Standard Error of the Sharpe Ratio</b><br>
    The Sharpe ratio is estimated from a sample. Like any sample statistic, it has uncertainty.
    <span class='formula'>SE(Sharpe) ≈ √((1 + Sharpe²/2) / T)</span>
    Where T = number of observations. For T=1000 and Sharpe=0.8:
    <span class='formula'>SE ≈ √((1 + 0.32) / 1000) ≈ 0.036</span>
    95% CI ≈ 0.8 ± 1.96 × 0.036 = [0.73, 0.87]. That's actually tight.
    But annualised from daily data, with only 252 data points per year, it widens considerably.
    
    <br>
    
    <b>Bootstrap Confidence Intervals</b><br>
    A more robust approach: resample your returns with replacement thousands of times,
    compute the Sharpe each time, and look at the distribution.
    <span class='formula'>Bootstrap CI = [5th percentile, 95th percentile] of 10,000 bootstrap Sharpes</span>
    No assumptions about normality. Works even if returns are fat-tailed (they always are).
    
    <br>
    
    <b>The Multiple Testing Problem</b><br>
    Suppose you test 50 SMA window combinations. At 5% significance, you expect 2–3
    to look significant just by chance — even if none have real edge.
    <span class='formula'>P(at least one false positive) = 1 − (1 − 0.05)^50 ≈ 92%</span>
    This is why a single backtest proving "significance" is nearly meaningless.
    
    Corrections:
    <span class='rule'><b>Bonferroni</b>: divide significance threshold by number of tests. 5% / 50 tests = 0.1% required per test.</span>
    <span class='rule'><b>Minimum backtest length</b>: the more parameters you search, the longer your backtest needs to be to have any confidence.</span>
    
    <br>
    
    <b>Minimum Backtest Length (Bailey & de Prado, 2014)</b>
    <span class='formula'>Min years = (0.44 + 0.99 × Sharpe²) × log(n_trials) / Sharpe</span>
    If you tested 100 parameter combinations and found Sharpe = 0.8, you need roughly 2–3 years
    of backtest data just to have a 5% chance of rejecting the null. Less data = not credible.
    
    <br>
    
    <b>The bottom line</b><br>
    Statistical tests can only tell you if a result is unlikely by chance.
    They can't confirm your strategy has real edge — only that the data is consistent with it.
    Real confidence comes from: economic intuition for <i>why</i> the strategy should work,
    out-of-sample testing, and live paper trading before committing real capital.
    
    </div>
    """, unsafe_allow_html=True)
    
        col_t, col_s, col_b, _ = st.columns([1, 1, 1, 3])
        with col_t:
            sr_ticker = st.selectbox("Ticker", options=list(TICKER_OPTIONS.keys()), index=0, key="sr_ticker")
        with col_s:
            sr_strat  = st.selectbox("Strategy", ["Buy & Hold", "SMA 50/200", "RSI 14"], key="sr_strat")
        with col_b:
            n_boot    = st.number_input("Bootstrap samples", min_value=1000, max_value=20000, value=5000, step=1000)
    
        with st.spinner("Bootstrapping…"):
            prices   = load_prices(sr_ticker, START, END)
            log_ret  = np.log(prices / prices.shift(1)).dropna()
    
            if sr_strat == "SMA 50/200":
                sig = sma_signal(prices, 50, 200).reindex(prices.index).fillna(0)
                ret, _ = strategy_returns(prices, sig)
            elif sr_strat == "RSI 14":
                sig, _ = rsi_signal(prices, 14, 30, 70)
                sig = sig.reindex(prices.index).fillna(0)
                ret, _ = strategy_returns(prices, sig)
            else:
                ret = log_ret.copy()
    
            T     = len(ret)
            sharpe_obs = ret.mean() / ret.std() * np.sqrt(252)
    
            # Analytical SE
            se_analytical = float(np.sqrt((1 + sharpe_obs**2 / 2) / T))
            ci_low_a  = sharpe_obs - 1.96 * se_analytical * np.sqrt(252)
            ci_high_a = sharpe_obs + 1.96 * se_analytical * np.sqrt(252)
    
            # Bootstrap
            np.random.seed(0)
            boot_sharpes = []
            ret_vals = ret.values
            for _ in range(int(n_boot)):
                sample = np.random.choice(ret_vals, size=T, replace=True)
                s = sample.mean() / sample.std() * np.sqrt(252) if sample.std() > 0 else 0
                boot_sharpes.append(s)
            boot_sharpes = np.array(boot_sharpes)
            ci_low_b  = float(np.percentile(boot_sharpes, 2.5))
            ci_high_b = float(np.percentile(boot_sharpes, 97.5))
            p_positive = float((boot_sharpes > 0).mean())
    
            # Multiple testing: Bonferroni for grid of SMA params
            n_trials_grid = len([1 for f in [10,20,30,50,60,80,100]
                                 for s in [50,100,150,200,250,300] if f < s])
            bonferroni_threshold = 0.05 / n_trials_grid
    
            # Min backtest length
            if sharpe_obs > 0:
                min_years = (0.44 + 0.99 * sharpe_obs**2) * np.log(n_trials_grid) / sharpe_obs
            else:
                min_years = float("inf")
    
        # ── KPIs ───────────────────────────────────────────────────────────────────
        st.markdown("<br>", unsafe_allow_html=True)
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Observed Sharpe",      f"{sharpe_obs:.2f}", f"T={T} days")
        c2.metric("95% CI (bootstrap)",   f"[{ci_low_b:.2f}, {ci_high_b:.2f}]", f"width: {ci_high_b-ci_low_b:.2f}")
        c3.metric("P(Sharpe > 0)",        f"{p_positive:.1%}", "bootstrap probability")
        c4.metric("Min backtest needed",   f"{min_years:.1f} yrs",
                  f"for {n_trials_grid} trials tested")
    
        st.markdown("<br>", unsafe_allow_html=True)
    
        # ── Bootstrap distribution ────────────────────────────────────────────────
        st.markdown("<p class='section-label'>Bootstrap distribution of Sharpe ratio</p>", unsafe_allow_html=True)
        fig = go.Figure()
        fig.add_trace(go.Histogram(x=boot_sharpes, nbinsx=80,
                                   marker_color="rgba(180,142,173,0.4)",
                                   marker_line=dict(color="#b48ead", width=0.5),
                                   name="Bootstrap Sharpes",
                                   hovertemplate="Sharpe: %{x:.2f}<br>Count: %{y}<extra></extra>"))
        fig.add_vline(x=sharpe_obs, line=dict(color="#f5c518", width=2),
                      annotation_text=f"Observed: {sharpe_obs:.2f}",
                      annotation_font=dict(color="#f5c518", size=10))
        fig.add_vline(x=ci_low_b,  line=dict(color="#00b4ff", width=1, dash="dash"),
                      annotation_text=f"2.5%: {ci_low_b:.2f}",
                      annotation_font=dict(color="#00b4ff", size=9))
        fig.add_vline(x=ci_high_b, line=dict(color="#00b4ff", width=1, dash="dash"),
                      annotation_text=f"97.5%: {ci_high_b:.2f}",
                      annotation_font=dict(color="#00b4ff", size=9))
        fig.add_vline(x=0, line=dict(color="#ff4466", width=1, dash="dot"))
        fig.update_layout(**PLOTLY_THEME, height=320, showlegend=False,
                          xaxis_title="Annualised Sharpe Ratio", yaxis_title="Frequency")
        st.plotly_chart(fig, width="stretch")
        chart_caption(ai_insight(
            f"Bootstrap Sharpe distribution for {sr_strat} on {sr_ticker}. "
            f"Observed Sharpe is {sharpe_obs:.2f}, 95% bootstrap interval is [{ci_low_b:.2f}, {ci_high_b:.2f}], and probability Sharpe > 0 is {p_positive:.1%}.",
            api_key) or
            f"The yellow line is the observed Sharpe and the dashed blue lines show the range you would plausibly expect from resampling the same data. "
            f"If that interval is wide or crosses zero, your apparent edge is much less certain than the single observed Sharpe suggests.")
    
        # ── Multiple testing table ─────────────────────────────────────────────────
        st.markdown("<p class='section-label'>Multiple testing correction</p>", unsafe_allow_html=True)
        mt_rows = pd.DataFrame({
            "Scenario": [
                "Single test (no correction)",
                f"Grid search ({n_trials_grid} combos) — Bonferroni",
                "100 strategies tested — Bonferroni",
                "1000 strategies tested — Bonferroni",
            ],
            "Required p-value": [
                "< 0.050",
                f"< {0.05/n_trials_grid:.4f}",
                "< 0.0005",
                "< 0.00005",
            ],
            "Interpretation": [
                "Default significance threshold",
                "Adjusted for our SMA grid search",
                "Used by most systematic funds",
                "High-frequency strategy research",
            ],
        }).set_index("Scenario")
        st.dataframe(mt_rows, width="stretch")
    
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(f"""
        <div style='font-family:JetBrains Mono;font-size:0.7rem;color:#3a4050;line-height:2;
                    border-left:2px solid #1e2030;padding-left:1rem;'>
        bootstrap samples: {int(n_boot):,} · 95% CI: [{ci_low_b:.2f}, {ci_high_b:.2f}]<br>
        analytical CI (assumes normality): [{ci_low_a:.2f}, {ci_high_a:.2f}]<br>
        P(Sharpe &gt; 0): {p_positive:.1%} · min backtest for {n_trials_grid} trials: {min_years:.1f} years
        </div>
        """, unsafe_allow_html=True)
        render_bottom_nav("Phase 11 — Statistical Rigor")
    
    
    # ════════════════════════════════════════════════════════════════════════════
    #  PHASE 12 — MARKET MICROSTRUCTURE
    # ════════════════════════════════════════════════════════════════════════════


def render_phase_12(START, END, selected_tickers, api_key):
        st.markdown("<span class='phase-badge' style='background:#ff7043;color:#0a0a0f'>Phase 12</span>", unsafe_allow_html=True)
        st.markdown("## Market Microstructure")
        st.markdown(f"<p class='section-label'>Order book · spread · impact · intraday patterns · {START} → {END}</p>", unsafe_allow_html=True)
    
        with st.expander("101 — How markets actually work at the microscopic level", expanded=False):
            st.markdown("""
    <div class='explainer-box'>
    <h4>Inside the exchange: what happens when you click "Buy"</h4>
    
    Everything we've built assumes you trade at the closing price. In reality, markets are
    continuous two-sided auctions. Understanding this is essential to knowing what's achievable.
    
    <br>
    
    <b>The Order Book</b><br>
    At any moment, an exchange maintains two lists:
    <span class='rule'><b>Bids</b>: people wanting to buy, ranked by price descending. The highest bid is the "best bid".</span>
    <span class='rule'><b>Asks</b>: people wanting to sell, ranked by price ascending. The lowest ask is the "best ask".</span>
    The gap between best bid and best ask is the <b>bid-ask spread</b>.
    
    <br>
    
    <b>Order Types</b>
    <span class='rule'><b class='warn'>Market order</b>: execute immediately at whatever price is available. Guaranteed fill, uncertain price. You pay the spread.</span>
    <span class='rule'><b class='good'>Limit order</b>: execute only at your specified price or better. No spread cost, but may not fill. You <i>earn</i> the spread if patient.</span>
    <span class='rule'><b>Stop order</b>: triggers a market order when price hits a level. Used for stop-losses. Can fill at a much worse price in fast markets ("slippage").</span>
    
    <br>
    
    <b>Market Impact</b><br>
    Large orders move the price against you. If you need to buy $10M of a stock with $500K average daily volume,
    your buying pressure will push the price up before you finish. This is why institutional trading is hard.
    Retail traders with small orders have zero market impact — a genuine edge over large funds.
    
    <br>
    
    <b>Intraday Patterns</b><br>
    Markets aren't uniform throughout the day:
    <span class='rule'><b>Open (9:30–10:00 ET)</b>: highest volume, highest volatility, widest spreads. Overnight news gets digested.</span>
    <span class='rule'><b>Midday (12:00–14:00 ET)</b>: lowest volume, tightest spreads, drift-prone.</span>
    <span class='rule'><b>Close (15:30–16:00 ET)</b>: second highest volume. Index rebalancing, closing auctions.</span>
    Daily strategies using closing prices implicitly trade at the most liquid time — which is realistic.
    
    <br>
    
    <b>What this means for your strategies</b>
    <span class='rule'>Our SMA/RSI strategies trade end-of-day. This is realistic and implementable — SPY at close is very liquid.</span>
    <span class='rule'>Shorter time frames (hourly, minute) face much larger effective spreads and impact costs.</span>
    <span class='rule'>The strategies built in this course are "low frequency" — one signal per day or less. This is where retail alpha is most accessible.</span>
    
    <br>
    
    <b>The VWAP benchmark</b><br>
    Volume-Weighted Average Price — the average price weighted by volume throughout the day.
    Institutional traders measure execution quality against VWAP: did you beat or miss the average?
    Beating VWAP consistently is extremely hard. Retail traders don't need to worry about this.
    
    </div>
    """, unsafe_allow_html=True)
    
        col_t, _ = st.columns([1, 5])
        with col_t:
            ms_ticker = st.selectbox("Ticker", options=list(TICKER_OPTIONS.keys()), index=0, key="ms_ticker")
    
        with st.spinner("Loading…"):
            prices   = load_prices(ms_ticker, START, END)
            log_ret  = np.log(prices / prices.shift(1)).dropna()
    
            # Simulate bid-ask spread model based on volatility
            # Spread ≈ k × daily_vol (market maker model)
            daily_vol    = log_ret.rolling(21).std()
            sim_spread   = daily_vol * 0.15 * 10000  # in bps, rough proxy
            sim_spread   = sim_spread.clip(lower=0.5, upper=30)
    
            # Rolling metrics
            roll_vol_30  = log_ret.rolling(30).std() * np.sqrt(252)
            roll_vol_5   = log_ret.rolling(5).std()  * np.sqrt(252)
    
            # Return autocorrelation (mean reversion signal)
            lags   = range(1, 21)
            autocorrs = [log_ret.autocorr(lag=l) for l in lags]
    
            # Day-of-week effect
            ret_with_day = log_ret.copy()
            ret_with_day.index = pd.to_datetime(ret_with_day.index)
            dow_returns  = ret_with_day.groupby(ret_with_day.index.day_name()).mean() * 252
            dow_order    = ["Monday","Tuesday","Wednesday","Thursday","Friday"]
            dow_returns  = dow_returns.reindex([d for d in dow_order if d in dow_returns.index])
    
            # Monthly seasonality
            monthly_ret  = ret_with_day.groupby(ret_with_day.index.month).mean() * 252
            month_names  = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
            monthly_ret.index = [month_names[i-1] for i in monthly_ret.index]
    
        # ── Spread simulation ──────────────────────────────────────────────────────
        st.markdown("<br>", unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        typical_spread = float(sim_spread.median())
        c1.metric("Typical spread (simulated)", f"{typical_spread:.1f} bps",
                  f"{typical_spread/100:.3%} per round trip")
        c2.metric("Vol-adjusted spread (high-vol)", f"{float(sim_spread.quantile(0.9)):.1f} bps",
                  "90th pct during stress")
        c3.metric("Annual drag (10 trades)",
                  f"{typical_spread * 10 / 100:.2%}",
                  f"at {typical_spread:.1f} bps/trade")
    
        st.markdown("<br>", unsafe_allow_html=True)
    
        # ── Simulated spread over time ─────────────────────────────────────────────
        st.markdown("<p class='section-label'>Simulated bid-ask spread over time (proxy: vol-scaled)</p>", unsafe_allow_html=True)
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True,
                            row_heights=[0.5, 0.5], vertical_spacing=0.04)
        fig.add_trace(go.Scatter(x=prices.index, y=prices.values,
            line=dict(color="#c8cdd6", width=1), name="Price",
            hovertemplate="$%{y:.2f}<extra></extra>"), row=1, col=1)
        fig.add_trace(go.Scatter(x=sim_spread.index, y=sim_spread.values,
            fill="tozeroy", fillcolor="rgba(245,197,24,0.1)",
            line=dict(color="#f5c518", width=1), name="Est. Spread (bps)",
            hovertemplate="%{y:.1f} bps<extra></extra>"), row=2, col=1)
        fig.update_layout(**PLOTLY_THEME, height=400, hovermode="x unified",
                          legend=dict(orientation="h", y=1.02, x=0, font=dict(size=10), bgcolor="rgba(0,0,0,0)"))
        fig.update_yaxes(gridcolor="#161820", title_text="Price", row=1)
        fig.update_yaxes(gridcolor="#161820", title_text="Spread (bps)", row=2)
        fig.update_xaxes(gridcolor="#161820")
        st.plotly_chart(fig, width="stretch")
        chart_caption(ai_insight(
            f"Microstructure spread proxy for {ms_ticker}. "
            f"Typical simulated spread is {typical_spread:.1f} bps and the 90th percentile is {float(sim_spread.quantile(0.9)):.1f} bps. "
            f"Model scales spread with rolling volatility.",
            api_key) or
            f"The lower panel estimates how trading costs widen when volatility rises. "
            f"That means execution is most expensive exactly when markets are stressed, which is why backtests often understate real-world friction.")
    
        # ── Autocorrelation ────────────────────────────────────────────────────────
        st.markdown("<p class='section-label'>Return autocorrelation by lag — mean reversion or momentum?</p>", unsafe_allow_html=True)
        colors_ac = ["#00ff88" if a > 0 else "#ff4466" for a in autocorrs]
        fig_ac = go.Figure(go.Bar(x=list(lags), y=autocorrs, marker_color=colors_ac,
                                  text=[f"{a:.3f}" for a in autocorrs], textposition="outside",
                                  hovertemplate="Lag %{x}: %{y:.3f}<extra></extra>"))
        fig_ac.add_hline(y=0, line=dict(color="#2a2d3a", width=1))
        # 95% significance bands: ±1.96/√T
        sig_band = 1.96 / np.sqrt(len(log_ret))
        fig_ac.add_hline(y=sig_band,  line=dict(color="#5a6070", dash="dot", width=0.8),
                         annotation_text="95% significance", annotation_font=dict(color="#5a6070", size=9))
        fig_ac.add_hline(y=-sig_band, line=dict(color="#5a6070", dash="dot", width=0.8))
        fig_ac.update_layout(**PLOTLY_THEME, height=300, showlegend=False,
                             xaxis_title="Lag (days)", yaxis_title="Autocorrelation")
        fig_ac.update_yaxes(gridcolor="#161820")
        st.plotly_chart(fig_ac, width="stretch")
        chart_caption(ai_insight(
            f"Return autocorrelation for {ms_ticker} across lags 1 to 20. "
            f"Significance band is ±{sig_band:.3f}, and the strongest lag signal is {max(autocorrs, key=lambda x: abs(x)):.3f}.",
            api_key) or
            f"Bars above zero suggest momentum and bars below zero suggest mean reversion. "
            f"Only bars outside the significance bands are strong enough to treat as potentially real rather than noise.")
    
        # ── Seasonality ────────────────────────────────────────────────────────────
        col_d, col_m = st.columns(2)
        with col_d:
            st.markdown("<p class='section-label'>Day-of-week effect</p>", unsafe_allow_html=True)
            clrs_dow = ["#00ff88" if v > 0 else "#ff4466" for v in dow_returns.values]
            fig_dow = go.Figure(go.Bar(x=dow_returns.index, y=dow_returns.values,
                                       marker_color=clrs_dow,
                                       text=[f"{v:.1%}" for v in dow_returns.values],
                                       textposition="outside",
                                       hovertemplate="%{x}: %{y:.2%}<extra></extra>"))
            fig_dow.add_hline(y=0, line=dict(color="#2a2d3a", width=0.8))
            fig_dow.update_layout(**PLOTLY_THEME, height=280, showlegend=False,
                                  yaxis_title="Ann. avg return")
            fig_dow.update_yaxes(tickformat=".0%", gridcolor="#161820")
            st.plotly_chart(fig_dow, width="stretch")
            best_dow = dow_returns.idxmax()
            chart_caption(ai_insight(
                f"Day-of-week seasonality for {ms_ticker}. "
                f"Best day is {best_dow} at {dow_returns.max():.2%} annualized average return and worst day is {dow_returns.idxmin()} at {dow_returns.min():.2%}.",
                api_key) or
                f"This chart averages returns by weekday, which can reveal small calendar effects. "
                f"Treat these patterns carefully because they are usually weak and can disappear out of sample.")
        with col_m:
            st.markdown("<p class='section-label'>Monthly seasonality</p>", unsafe_allow_html=True)
            clrs_m = ["#00ff88" if v > 0 else "#ff4466" for v in monthly_ret.values]
            fig_mon = go.Figure(go.Bar(x=monthly_ret.index, y=monthly_ret.values,
                                       marker_color=clrs_m,
                                       text=[f"{v:.1%}" for v in monthly_ret.values],
                                       textposition="outside",
                                       hovertemplate="%{x}: %{y:.2%}<extra></extra>"))
            fig_mon.add_hline(y=0, line=dict(color="#2a2d3a", width=0.8))
            fig_mon.update_layout(**PLOTLY_THEME, height=280, showlegend=False,
                                  yaxis_title="Ann. avg return")
            fig_mon.update_yaxes(tickformat=".0%", gridcolor="#161820")
            st.plotly_chart(fig_mon, width="stretch")
            best_month = monthly_ret.idxmax()
            chart_caption(ai_insight(
                f"Monthly seasonality for {ms_ticker}. "
                f"Best month is {best_month} at {monthly_ret.max():.2%} annualized average return and worst month is {monthly_ret.idxmin()} at {monthly_ret.min():.2%}.",
                api_key) or
                f"This chart groups returns by calendar month to look for seasonal tendencies. "
                f"Useful for exploration, but not strong enough on its own to justify a trading strategy without more evidence.")
    
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("""
        <div style='font-family:JetBrains Mono;font-size:0.7rem;color:#3a4050;line-height:2;
                    border-left:2px solid #1e2030;padding-left:1rem;'>
        spread model: proportional to 21-day rolling vol (simplified market maker model)<br>
        autocorrelation: bars outside ±grey bands are statistically significant at 95%<br>
        seasonality: annualised average returns — small sample, treat as exploratory only
        </div>
        """, unsafe_allow_html=True)
        render_bottom_nav("Phase 12 — Market Microstructure")
    
    
    # ════════════════════════════════════════════════════════════════════════════
    #  QUANT ALGO FAMILIES
    # ════════════════════════════════════════════════════════════════════════════

PHASE_RENDERERS = {
    "Phase 1 — Asset Metrics": render_phase_1,
    "Phase 2 — SMA Crossover": render_phase_2,
    "Phase 3 — RSI Mean Reversion": render_phase_3,
    "Phase 4 — Transaction Costs": render_phase_4,
    "Phase 5 — Combining Signals": render_phase_5,
    "Phase 6 — Walk-Forward Validation": render_phase_6,
    "Phase 7 — Position Sizing": render_phase_7,
    "Phase 8 — Portfolio Construction": render_phase_8,
    "Phase 9 — Risk Management": render_phase_9,
    "Phase 10 — Factor Models": render_phase_10,
    "Phase 11 — Statistical Rigor": render_phase_11,
    "Phase 12 — Market Microstructure": render_phase_12,
}


def render_phase_page(page: str, START: str, END: str, selected_tickers, api_key: str):
    PHASE_RENDERERS[page](START, END, selected_tickers, api_key)
