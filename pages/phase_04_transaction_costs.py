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

def render_phase_4(START, END, selected_tickers, api_key):
        st.markdown("<span class='phase-badge' style='background:#ff4466'>Phase 4</span>", unsafe_allow_html=True)
        st.markdown("## Transaction Costs & Slippage")
        st.markdown(f"<p class='section-label'>Realistic backtesting · both strategies · {START} → {END}</p>", unsafe_allow_html=True)
    
        with st.expander("101 — Why free backtests are lying to you", expanded=False):
            st.markdown("""
    <div class='explainer-box'>
    <h4>The gap between paper trading and real trading</h4>
    
    Every backtest in Phases 2 and 3 silently assumed you trade for free at the exact closing price.
    Neither is true. Here's what actually eats your returns:
    
    <br>
    
    <b>1. Bid-Ask Spread</b><br>
    Every market has two prices at once:
    <span class='rule'><b>Bid</b>: the price buyers will pay (what you get when you sell)</span>
    <span class='rule'><b>Ask</b>: the price sellers want (what you pay when you buy)</span>
    The spread is the difference. When you buy, you pay the ask. When you sell, you get the bid.
    You immediately lose half the spread each way. For SPY the spread is tiny (~0.01%). For small-cap stocks it can be 0.5%+.
    
    <br>
    
    <b>2. Slippage</b><br>
    Even after you decide to trade, your order takes time to execute. By then the price may have moved.
    If you're buying because the price is going up, everyone else is buying too — your order pushes the price up further before it fills.
    Bigger orders = more slippage. Retail traders have an advantage here: small orders don't move the market.
    
    <br>
    
    <b>3. Commission</b><br>
    Most retail brokers (Robinhood, IBKR, etc.) are now $0 commission. But institutional desks still pay. We model this as an optional add-on.
    
    <br>
    
    <b>Basis Points (bps) — the unit of cost</b>
    <span class='formula'>1 basis point = 0.01% = 0.0001</span>
    Costs are always expressed in bps. Typical ranges:
    <span class='rule'><b>SPY, QQQ</b>: ~1–3 bps total (very liquid)</span>
    <span class='rule'><b>Individual stocks (AAPL, MSFT)</b>: ~3–8 bps</span>
    <span class='rule'><b>Small caps, crypto</b>: 10–50+ bps</span>
    
    <br>
    
    <b>Why this hurts mean reversion more than trend-following</b><br>
    SMA crossover made only 3 trades in 4 years. Even at 10 bps/trade, total cost = 30 bps over 4 years. Negligible.
    RSI mean reversion can make 30–50+ trades/year. At 5 bps/trade, that's 150–250 bps/year — easily 1.5–2.5% of annual return gone.
    <b class='bad'>High-frequency strategies are especially vulnerable.</b> A strategy that looks like Sharpe 1.5 before costs
    can become Sharpe 0.3 after costs. This is why most retail "strategies" don't survive contact with reality.
    
    <br>
    
    <b>The breakeven trade frequency</b><br>
    You can work out how many trades your edge needs to survive:
    <span class='formula'>Required edge per trade (bps) &gt; Cost per trade (bps)</span>
    If your strategy makes 5 bps/trade on average but costs 8 bps/trade — it's a money-losing machine.
    
    </div>
    """, unsafe_allow_html=True)
    
        # ── Controls ───────────────────────────────────────────────────────────────
        col_t, col_c, col_s, _ = st.columns([1, 1, 1, 3])
        with col_t:
            cost_ticker = st.selectbox("Ticker", options=list(TICKER_OPTIONS.keys()), index=0, key="cost_ticker")
        with col_c:
            cost_bps = st.slider("Cost per trade (bps)", min_value=0, max_value=30, value=5,
                                 help="Spread + commission. SPY ≈ 1–3 bps. Individual stocks ≈ 5–10 bps.")
        with col_s:
            slip_bps = st.slider("Slippage (bps)", min_value=0, max_value=20, value=2,
                                 help="Execution slippage. Higher for less liquid assets.")
    
        total_bps = cost_bps + slip_bps
    
        # ── Compute ────────────────────────────────────────────────────────────────
        with st.spinner("Computing…"):
            prices   = load_prices(cost_ticker, START, END)
            log_ret  = np.log(prices / prices.shift(1))
    
            # SMA strategy
            sig_sma          = sma_signal(prices, 50, 200)
            sma_ret_gross, bh_ret = strategy_returns(prices, sig_sma)
            sma_ret_net      = apply_costs(sma_ret_gross, sig_sma.loc[sma_ret_gross.index], total_bps)
            sma_trades       = int(sig_sma.diff().abs().fillna(0).sum())
    
            # RSI strategy
            sig_rsi, _       = rsi_signal(prices, 14, 30, 70)
            rsi_ret_gross, _ = strategy_returns(prices, sig_rsi)
            rsi_ret_net      = apply_costs(rsi_ret_gross, sig_rsi.loc[rsi_ret_gross.index], total_bps)
            rsi_trades       = int(sig_rsi.diff().abs().fillna(0).sum())
    
            m_bh        = compute_metrics(bh_ret)
            m_sma_gross = compute_metrics(sma_ret_gross)
            m_sma_net   = compute_metrics(sma_ret_net)
            m_rsi_gross = compute_metrics(rsi_ret_gross)
            m_rsi_net   = compute_metrics(rsi_ret_net)
    
            sma_total_cost = sma_trades * total_bps / 100   # in %
            rsi_total_cost = rsi_trades * total_bps / 100
    
        # ── Cost summary strip ─────────────────────────────────────────────────────
        st.markdown("<br>", unsafe_allow_html=True)
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Cost per trade", f"{total_bps} bps", f"{total_bps/100:.2f}%")
        c2.metric("SMA trades", str(sma_trades), f"total cost: {sma_total_cost:.2f}%")
        c3.metric("RSI trades", str(rsi_trades), f"total cost: {rsi_total_cost:.2f}%")
        c4.metric("Cost ratio RSI/SMA", f"{rsi_trades/max(sma_trades,1):.0f}×", "more trading = more cost")
    
        st.markdown("<br>", unsafe_allow_html=True)
    
        # ── Comparison table ───────────────────────────────────────────────────────
        st.markdown("<p class='section-label'>Before vs after costs — both strategies</p>", unsafe_allow_html=True)
        comp = pd.DataFrame({
            "Metric": ["Ann. Return", "Ann. Vol", "Sharpe", "Max Drawdown"],
            "B&H": [f"{m_bh['ann_return']:.2%}", f"{m_bh['ann_vol']:.2%}",
                    f"{m_bh['sharpe']:.2f}", f"{m_bh['max_dd']:.2%}"],
            "SMA (gross)": [f"{m_sma_gross['ann_return']:.2%}", f"{m_sma_gross['ann_vol']:.2%}",
                            f"{m_sma_gross['sharpe']:.2f}", f"{m_sma_gross['max_dd']:.2%}"],
            f"SMA (−{total_bps}bps/trade)": [f"{m_sma_net['ann_return']:.2%}", f"{m_sma_net['ann_vol']:.2%}",
                            f"{m_sma_net['sharpe']:.2f}", f"{m_sma_net['max_dd']:.2%}"],
            "RSI (gross)": [f"{m_rsi_gross['ann_return']:.2%}", f"{m_rsi_gross['ann_vol']:.2%}",
                            f"{m_rsi_gross['sharpe']:.2f}", f"{m_rsi_gross['max_dd']:.2%}"],
            f"RSI (−{total_bps}bps/trade)": [f"{m_rsi_net['ann_return']:.2%}", f"{m_rsi_net['ann_vol']:.2%}",
                            f"{m_rsi_net['sharpe']:.2f}", f"{m_rsi_net['max_dd']:.2%}"],
        }).set_index("Metric")
        st.dataframe(comp, width="stretch")
    
        st.markdown("<br>", unsafe_allow_html=True)
    
        # ── Equity curves ─────────────────────────────────────────────────────────
        st.markdown("<p class='section-label'>Equity curves — gross vs net of costs</p>", unsafe_allow_html=True)
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=m_bh["cumulative"].index, y=m_bh["cumulative"].values,
            name="Buy & Hold", line=dict(color="#5a6070", width=1.2, dash="dot"),
            hovertemplate="B&H: $%{y:.3f}<extra></extra>"))
        fig.add_trace(go.Scatter(x=m_sma_gross["cumulative"].index, y=m_sma_gross["cumulative"].values,
            name="SMA gross", line=dict(color="#00ff88", width=1.2, dash="dash"),
            hovertemplate="SMA gross: $%{y:.3f}<extra></extra>"))
        fig.add_trace(go.Scatter(x=m_sma_net["cumulative"].index, y=m_sma_net["cumulative"].values,
            name="SMA net", line=dict(color="#00ff88", width=2),
            hovertemplate="SMA net: $%{y:.3f}<extra></extra>"))
        fig.add_trace(go.Scatter(x=m_rsi_gross["cumulative"].index, y=m_rsi_gross["cumulative"].values,
            name="RSI gross", line=dict(color="#00b4ff", width=1.2, dash="dash"),
            hovertemplate="RSI gross: $%{y:.3f}<extra></extra>"))
        fig.add_trace(go.Scatter(x=m_rsi_net["cumulative"].index, y=m_rsi_net["cumulative"].values,
            name="RSI net", line=dict(color="#00b4ff", width=2),
            hovertemplate="RSI net: $%{y:.3f}<extra></extra>"))
        fig.update_layout(**PLOTLY_THEME, height=400,
                          legend=dict(orientation="h", y=1.05, x=0, font=dict(size=10), bgcolor="rgba(0,0,0,0)"),
                          hovermode="x unified", yaxis_title="Growth of $1")
        st.plotly_chart(fig, width="stretch")
        chart_caption(ai_insight(
            f"Transaction cost impact on {cost_ticker}. Cost per trade: {total_bps} bps ({cost_bps} spread + {slip_bps} slippage). "
            f"SMA made {sma_trades} trades, total cost {sma_total_cost:.2f}%. Sharpe gross {m_sma_gross['sharpe']:.2f} → net {m_sma_net['sharpe']:.2f}. "
            f"RSI made {rsi_trades} trades, total cost {rsi_total_cost:.2f}%. Sharpe gross {m_rsi_gross['sharpe']:.2f} → net {m_rsi_net['sharpe']:.2f}.",
            api_key) or
            f"Dashed lines = gross (before costs), solid lines = net (after costs). "
            f"SMA made {sma_trades} trades (total friction: {sma_total_cost:.2f}%), nearly invisible on the chart. "
            f"RSI made {rsi_trades} trades (total friction: {rsi_total_cost:.2f}%) — "
            f"{'a meaningful drag' if rsi_total_cost > 0.5 else 'also modest'} on performance at {total_bps} bps/trade.")
    
        # ── Sharpe degradation bar chart ───────────────────────────────────────────
        st.markdown("<p class='section-label'>Sharpe ratio — gross vs net</p>", unsafe_allow_html=True)
        strategies = ["Buy & Hold", "SMA gross", "SMA net", "RSI gross", "RSI net"]
        sharpes    = [m_bh["sharpe"], m_sma_gross["sharpe"], m_sma_net["sharpe"],
                      m_rsi_gross["sharpe"], m_rsi_net["sharpe"]]
        colors     = ["#5a6070", "rgba(0,255,136,0.4)", "#00ff88", "rgba(0,180,255,0.4)", "#00b4ff"]
        fig2 = go.Figure(go.Bar(x=strategies, y=sharpes, marker_color=colors,
                                text=[f"{s:.2f}" for s in sharpes], textposition="outside",
                                hovertemplate="%{x}: %{y:.2f}<extra></extra>"))
        fig2.add_hline(y=m_bh["sharpe"], line=dict(color="#5a6070", dash="dot", width=1))
        fig2.update_layout(**PLOTLY_THEME, height=300, showlegend=False,
                           yaxis_title="Sharpe Ratio")
        fig2.update_yaxes(zeroline=True, zerolinecolor="#2a2d3a")
        st.plotly_chart(fig2, width="stretch")
        chart_caption(ai_insight(
            f"Sharpe comparison after transaction costs on {cost_ticker}. "
            f"Buy-and-hold Sharpe {m_bh['sharpe']:.2f}. SMA gross/net {m_sma_gross['sharpe']:.2f}/{m_sma_net['sharpe']:.2f}. "
            f"RSI gross/net {m_rsi_gross['sharpe']:.2f}/{m_rsi_net['sharpe']:.2f} at {total_bps} bps per trade.",
            api_key) or
            f"This bar chart isolates risk-adjusted performance after costs. "
            f"The gap between each gross and net bar shows how much trading friction matters, especially for RSI because it trades more often.")
        render_bottom_nav("Phase 4 — Transaction Costs")
    
    
    # ════════════════════════════════════════════════════════════════════════════
    #  PHASE 5 — COMBINING SIGNALS
    # ════════════════════════════════════════════════════════════════════════════


