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
from pages.phase_10_factor_models import render_phase_10 as render_phase_10_page
from pages.phase_09_risk_management import render_phase_9 as render_phase_9_page
from pages.phase_08_portfolio_construction import render_phase_8 as render_phase_8_page
from pages.phase_07_position_sizing import render_phase_7 as render_phase_7_page
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
    return render_phase_7_page(START, END, selected_tickers, api_key)

def render_phase_8(START, END, selected_tickers, api_key):
    return render_phase_8_page(START, END, selected_tickers, api_key)

def render_phase_9(START, END, selected_tickers, api_key):
    return render_phase_9_page(START, END, selected_tickers, api_key)

def render_phase_10(START, END, selected_tickers, api_key):
    return render_phase_10_page(START, END, selected_tickers, api_key)

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
