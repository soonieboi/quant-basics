import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from ui.components import chart_caption, render_bottom_nav
from ui.styles import PLOTLY_THEME
from core.ai import ai_insight


def render_algo_families_page(start: str, end: str, api_key: str):
    st.markdown("<span class='phase-badge' style='background:#26c6da;color:#0a0a0f'>Atlas</span>", unsafe_allow_html=True)
    st.markdown("## Major Quant Algorithm Families")
    st.markdown(f"<p class='section-label'>Strategy taxonomy · edge source · implementation tradeoffs · {start} → {end}</p>", unsafe_allow_html=True)

    with st.expander("101 — Why strategy families matter", expanded=False):
        st.markdown("""
<div class='explainer-box'>
<h4>Not all quant strategies are trying to capture the same edge</h4>

One of the easiest beginner mistakes is to treat "quant trading" as a single style.
It isn't. Different algorithm families use different data, operate on different time horizons,
and fail for different reasons.

<br>

<b>Why this matters</b><br>
<span class='rule'><b>Trend-following</b> assumes price moves persist.</span>
<span class='rule'><b>Mean reversion</b> assumes stretched prices snap back.</span>
<span class='rule'><b>Stat arb</b> assumes relative mispricings close.</span>
<span class='rule'><b>Factor investing</b> assumes rewarded risk premia persist over years.</span>
<span class='rule'><b>Market making</b> earns spread for providing liquidity, but takes inventory and adverse-selection risk.</span>
<span class='rule'><b>Volatility / options</b> trades pricing of convexity, skew, and realized vs implied vol.</span>
<span class='rule'><b>ML / forecasting</b> tries to improve prediction quality, but usually sits on top of one of the other families rather than replacing them.</span>

<br>

<b>Three practical questions to ask of any strategy</b>
<span class='formula'>1. What data does it need?</span>
<span class='formula'>2. What market inefficiency or risk premium is it exploiting?</span>
<span class='formula'>3. What breaks it?</span>

If you can't answer those, you don't yet understand the strategy well enough to trust a backtest.

</div>
""", unsafe_allow_html=True)

    families = [
        {"Family": "Trend-Following", "Typical Holding": "Weeks to months", "Data": "Daily/weekly prices", "Edge Source": "Momentum persistence", "Turnover": 2, "Capacity": 5, "Complexity": 2, "Main Risk": "Whipsaw in sideways markets", "Examples": "SMA crossover, Donchian breakout, time-series momentum", "Best For": "Liquid futures, indices, macro portfolios", "Description": "Buy strength and cut when the trend breaks. Simple, robust, and scalable."},
        {"Family": "Mean Reversion", "Typical Holding": "Days to weeks", "Data": "Prices, indicators, spreads", "Edge Source": "Short-term overshoot reversal", "Turnover": 4, "Capacity": 3, "Complexity": 3, "Main Risk": "Catching a falling knife in persistent trends", "Examples": "RSI reversion, Bollinger bands, short-horizon reversal", "Best For": "Range-bound markets and diversified baskets", "Description": "Fade sharp moves when price gets too far from a reference level."},
        {"Family": "Cross-Sectional Momentum", "Typical Holding": "Weeks to months", "Data": "Relative returns across assets", "Edge Source": "Winners keep beating losers", "Turnover": 3, "Capacity": 4, "Complexity": 3, "Main Risk": "Violent momentum crashes during reversals", "Examples": "Rank-and-hold baskets, sector rotation, long-short momentum", "Best For": "Equities, futures, multi-asset universes", "Description": "Rank assets against each other instead of looking at one chart in isolation."},
        {"Family": "Stat Arb", "Typical Holding": "Minutes to days", "Data": "Relative prices, residuals, baskets", "Edge Source": "Temporary mispricing convergence", "Turnover": 5, "Capacity": 2, "Complexity": 5, "Main Risk": "Relationships break and spreads do not converge", "Examples": "Pairs trading, basket residual trading, ETF vs constituents", "Best For": "Large universes with strong infrastructure", "Description": "Trade relative value rather than outright direction."},
        {"Family": "Factor Investing", "Typical Holding": "Months to years", "Data": "Fundamentals, returns, quality/value metrics", "Edge Source": "Persistent risk premia", "Turnover": 1, "Capacity": 5, "Complexity": 3, "Main Risk": "Long multi-year drawdowns and crowding", "Examples": "Value, quality, low vol, size, momentum factors", "Best For": "Systematic portfolios with patient capital", "Description": "Systematically hold characteristics historically associated with excess return."},
        {"Family": "Market Making", "Typical Holding": "Seconds to minutes", "Data": "Order book, trades, queue position", "Edge Source": "Earning spread while managing inventory", "Turnover": 5, "Capacity": 4, "Complexity": 5, "Main Risk": "Adverse selection and toxic flow", "Examples": "Two-sided quoting, ETF making, options market making", "Best For": "Firms with low latency and exchange connectivity", "Description": "Provide liquidity continuously and collect spread if inventory is controlled well."},
        {"Family": "Volatility / Options", "Typical Holding": "Days to months", "Data": "Options chain, realized vol, skew, term structure", "Edge Source": "Mispricing of implied vs realized volatility", "Turnover": 3, "Capacity": 3, "Complexity": 5, "Main Risk": "Convex losses and model error", "Examples": "Short vol carry, dispersion, delta-hedged vol trades", "Best For": "Options desks with strong risk systems", "Description": "Trade the shape and price of volatility rather than just direction."},
        {"Family": "ML / Forecasting", "Typical Holding": "Varies widely", "Data": "Prices, fundamentals, alt data, microstructure", "Edge Source": "Better prediction or better ranking", "Turnover": 3, "Capacity": 3, "Complexity": 5, "Main Risk": "Overfitting and unstable feature relationships", "Examples": "Return forecasting, execution models, regime classifiers", "Best For": "Research teams with good data discipline", "Description": "Usually an enhancement layer that improves signal quality or execution."},
    ]

    family_df = pd.DataFrame(families)
    family_names = family_df["Family"].tolist()

    col_fam, col_metric, _ = st.columns([2, 1, 3])
    with col_fam:
        selected_family = st.selectbox("Strategy family", family_names, index=0, key="algo_family")
    with col_metric:
        compare_metric = st.selectbox("Compare by", ["Turnover", "Capacity", "Complexity"], index=0, key="algo_metric")

    fam_row = family_df[family_df["Family"] == selected_family].iloc[0]

    st.markdown("<br>", unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Typical Holding", fam_row["Typical Holding"])
    c2.metric("Turnover", f"{int(fam_row['Turnover'])}/5", "higher = more trading")
    c3.metric("Capacity", f"{int(fam_row['Capacity'])}/5", "higher = scales better")
    c4.metric("Complexity", f"{int(fam_row['Complexity'])}/5", "higher = harder to build")

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(f"""
<div style='background:#0d0d14;border:1px solid #1e2030;border-left:3px solid #26c6da;
            border-radius:4px;padding:1.1rem 1.2rem;margin-bottom:1rem;'>
    <div style='font-family:JetBrains Mono;font-size:0.95rem;font-weight:600;color:#e8ecf0;margin-bottom:0.5rem;'>
        {fam_row["Family"]}
    </div>
    <div style='font-family:JetBrains Mono;font-size:0.74rem;line-height:1.8;color:#4a5060;margin-bottom:0.8rem;'>
        {fam_row["Description"]}
    </div>
    <div style='font-family:JetBrains Mono;font-size:0.68rem;line-height:1.9;color:#8a9ab0;'>
        <b>Data:</b> {fam_row["Data"]}<br>
        <b>Edge Source:</b> {fam_row["Edge Source"]}<br>
        <b>Main Risk:</b> {fam_row["Main Risk"]}<br>
        <b>Examples:</b> {fam_row["Examples"]}<br>
        <b>Best For:</b> {fam_row["Best For"]}
    </div>
</div>
""", unsafe_allow_html=True)

    st.markdown(f"<p class='section-label'>{compare_metric} across strategy families</p>", unsafe_allow_html=True)
    colors = ["#26c6da" if fam == selected_family else "#3a4050" for fam in family_df["Family"]]
    fig = go.Figure(go.Bar(
        x=family_df["Family"],
        y=family_df[compare_metric],
        marker_color=colors,
        text=[f"{int(v)}/5" for v in family_df[compare_metric]],
        textposition="outside",
        hovertemplate="%{x}<br>" + compare_metric + ": %{y}/5<extra></extra>",
    ))
    fig.update_layout(**PLOTLY_THEME, height=340, showlegend=False, yaxis_title=f"{compare_metric} Score")
    fig.update_yaxes(range=[0, 5.5], dtick=1, gridcolor="#161820")
    st.plotly_chart(fig, width="stretch")
    chart_caption(ai_insight(
        f"Compare major quant algorithm families by {compare_metric}. "
        f"Selected family is {selected_family} with score {int(fam_row[compare_metric])}/5. "
        f"Turnover {int(fam_row['Turnover'])}/5, capacity {int(fam_row['Capacity'])}/5, complexity {int(fam_row['Complexity'])}/5.",
        api_key) or
        f"This chart shows that different strategy families have different engineering and trading profiles. "
        f"{selected_family} stands out mainly through its {compare_metric.lower()} profile, which affects cost sensitivity, scalability, and implementation difficulty.")

    st.markdown("<p class='section-label'>Family comparison table</p>", unsafe_allow_html=True)
    display_df = family_df[["Family", "Typical Holding", "Edge Source", "Main Risk", "Turnover", "Capacity", "Complexity"]].copy()
    for col in ["Turnover", "Capacity", "Complexity"]:
        display_df[col] = display_df[col].map(lambda v: f"{int(v)}/5")
    st.dataframe(display_df.set_index("Family"), width="stretch")

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("""
    <div style='font-family:JetBrains Mono;font-size:0.7rem;color:#3a4050;line-height:2;
                border-left:2px solid #1e2030;padding-left:1rem;'>
    rule of thumb: start with trend-following, mean reversion, and factor ideas before touching stat arb or market making<br>
    the lower the holding period, the more execution, data quality, and infrastructure matter<br>
    ML is usually a layer on top of another family, not a separate source of edge by itself
    </div>
    """, unsafe_allow_html=True)
    render_bottom_nav("◆ Quant Algo Families")


def render_about_page():
    st.markdown("<span class='phase-badge' style='background:#8a9ab0;color:#0a0a0f'>About</span>", unsafe_allow_html=True)
    st.markdown("## About the Writer")
    st.markdown("<p class='section-label'>Project intent · beliefs · contact</p>", unsafe_allow_html=True)

    st.markdown("""
<div class='explainer-box' style='border-left-color:#8a9ab0;'>
<h4 style='color:#c8cdd6 !important;'>A practical quant learning lab</h4>

I built Quant Basics to make systematic trading easier to learn in a hands-on way.
Instead of treating quant as a wall of jargon, I wanted one place where I could
start from data, build rules, test ideas honestly, understand risk, and then think
about execution.

</div>
""", unsafe_allow_html=True)

    panels = [
        ("Core Beliefs", "Honest backtests beat impressive-looking curves.<br>Simple systems understood deeply beat complex systems copied blindly.<br>Risk management, costs, and execution matter as much as signal ideas."),
        ("What This Project Emphasizes", "Technical-first learning for people who want to understand markets through systems.<br>Honest treatment of costs, walk-forward testing, drawdowns, statistical rigor, and microstructure.<br>Beginner-friendly explanations that focus on intuition, not finance gatekeeping."),
        ("Contact", "Instagram: @sherminh<br>Email: sherminh0512@gmail.com<br>GitHub: @soonieboi"),
    ]
    for title, body in panels:
        st.markdown(f"""
<div style='background:#0d0d14;border:1px solid #1e2030;border-top:2px solid #8a9ab0;
            border-radius:4px;padding:1rem 1.1rem;margin:1rem 0;'>
    <div style='font-family:JetBrains Mono;font-size:0.62rem;letter-spacing:0.18em;
                text-transform:uppercase;color:#3a4050;margin-bottom:0.45rem;'>
        {title}
    </div>
    <div style='font-family:JetBrains Mono;font-size:0.72rem;line-height:1.95;color:#4a5060;'>
        {body}
    </div>
</div>
""", unsafe_allow_html=True)

    st.markdown("""
<div style='background:#0d0d14;border:1px solid #2a2230;border-top:2px solid #d7a6ff;
            border-radius:4px;padding:1rem 1.1rem;margin:1rem 0;'>
    <div style='font-family:JetBrains Mono;font-size:0.62rem;letter-spacing:0.18em;
                text-transform:uppercase;color:#5a4f66;margin-bottom:0.45rem;'>
        Disclaimer
    </div>
    <div style='font-family:JetBrains Mono;font-size:0.72rem;line-height:1.95;color:#6f667a;'>
        This project is for learning purposes only. I am not a financial professional,
        and nothing here should be treated as financial advice, investment advice, or a
        recommendation to trade any asset. Everything in this app should be taken with a
        pinch of salt and used as educational material only.
    </div>
</div>
""", unsafe_allow_html=True)

    render_bottom_nav("◇ About the Writer")
