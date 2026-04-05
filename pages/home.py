import streamlit as st

from content.config import (
    ABOUT_ACCENT,
    ALGO_CARDS,
    DISCLAIMER_ACCENT,
    HOME_ATLAS_ACCENT,
    HOME_PHASES,
    HOME_TRADE_ACCENT,
    WORKFLOW_STEPS,
)
from ui.components import (
    close_home_band,
    render_bottom_nav,
    render_home_band,
    render_home_info_card,
    render_home_phase_card,
    render_panel,
)


def render_home_page():
    st.markdown("""
<div style='padding: 2rem 0 1rem 0;'>
    <div style='font-family: JetBrains Mono; font-size: 0.65rem; letter-spacing: 0.3em;
                text-transform: uppercase; color: #3a4050; margin-bottom: 0.5rem;'>
        Quant Basics — Interactive Curriculum
    </div>
    <div style='font-family: JetBrains Mono; font-size: 2.8rem; font-weight: 700;
                color: #e8ecf0; line-height: 1.1; letter-spacing: -0.03em;'>
        Learn Quant Trading<br>
        <span style='color: #00ff88;'>from Scratch.</span>
    </div>
    <div style='font-family: JetBrains Mono; font-size: 0.85rem; color: #4a5060;
                margin-top: 1rem; line-height: 1.8; max-width: 620px;'>
        12 hands-on modules plus a quant strategy atlas. Real data. Live charts.
        Every concept explained
        from first principles — built for software engineers learning quant finance.
    </div>
</div>
""", unsafe_allow_html=True)
    st.markdown("""
<div style='background:#0d0d14;border:1px solid #1e2030;border-left:3px solid #00ff88;
            border-radius:4px;padding:1rem 1.1rem;margin:0.3rem 0 1.2rem 0;max-width:920px;'>
    <div style='font-family:JetBrains Mono;font-size:0.62rem;letter-spacing:0.18em;
                text-transform:uppercase;color:#3a4050;margin-bottom:0.5rem;'>
        Start Here
    </div>
    <div style='font-family:JetBrains Mono;font-size:0.76rem;line-height:1.8;color:#4a5060;'>
        The numbered phases are the learning path. The separate quant strategy atlas is reference material
        you can open anytime when you want a broader map of the field.
    </div>
</div>
""", unsafe_allow_html=True)

    render_home_band(
        "learn",
        "Learn the Path",
        "Start with the numbered phases below. They are ordered as a practical curriculum: "
        "measure markets, build signals, test honestly, size risk, then understand portfolio construction and execution.",
    )
    for row_start in range(0, len(HOME_PHASES), 3):
        cols = st.columns(3)
        for col, phase in zip(cols, HOME_PHASES[row_start:row_start + 3]):
            with col:
                render_home_phase_card(phase)

    close_home_band()
    render_home_band(
        "trade",
        "Use in Real Trading",
        "This is the bridge from a backtest to actual deployment. The workflow below is the operating loop: "
        "research, encode rules, validate, deploy small, and monitor continuously.",
    )
    for row_start in range(0, len(WORKFLOW_STEPS), 3):
        cols = st.columns(3)
        for col, (num, title, desc) in zip(cols, WORKFLOW_STEPS[row_start:row_start + 3]):
            with col:
                render_home_info_card(
                    f"Step {num}",
                    f"<span style='display:block;font-size:0.9rem;font-weight:600;color:#e8ecf0;margin-bottom:0.5rem;'>{title}</span>{desc}",
                    HOME_TRADE_ACCENT,
                )

    close_home_band()
    render_home_band(
        "field",
        "Explore the Field",
        "These are the major families of systematic trading. They are reference material, not curriculum steps, "
        "so they live in a separate atlas page rather than inside the numbered learning path.",
    )
    for row_start in range(0, len(ALGO_CARDS), 2):
        cols = st.columns(2)
        for col, (title, desc) in zip(cols, ALGO_CARDS[row_start:row_start + 2]):
            with col:
                render_home_info_card(title, desc, HOME_ATLAS_ACCENT, accent_position="left")

    render_panel(
        "Strategy Atlas",
        "Open <span style='color:#26c6da;'>◆ Quant Algo Families</span> from the sidebar for the full taxonomy, tradeoffs, and implementation notes.",
        HOME_ATLAS_ACCENT,
        accent_position="left",
        margin="0 0 0.8rem 0",
    )
    render_panel(
        "About",
        "Open <span style='color:#c8cdd6;'>◇ About the Writer</span> from the sidebar for author notes, intent behind the project, and contact details.",
        ABOUT_ACCENT,
        accent_position="left",
        margin="0 0 0.8rem 0",
    )
    close_home_band()
    render_panel(
        "Disclaimer",
        "Quant Basics is for learning purposes only. I am not a financial professional, and nothing in this app should be treated as financial advice, investment advice, or a recommendation to trade any asset. Use the material here as educational content only, and take all results with a pinch of salt.",
        DISCLAIMER_ACCENT,
        margin="1rem 0 0.8rem 0",
    )

    st.markdown("""
<div style='font-family:JetBrains Mono;font-size:0.65rem;color:#2a2d3a;
            text-align:center;padding:1rem 0 0.5rem 0;line-height:2;'>
    All computations run live on real market data via yfinance &nbsp;·&nbsp;
    Select any phase in the sidebar to begin &nbsp;·&nbsp;
    Every module includes a 101 explainer — click to expand
</div>
""", unsafe_allow_html=True)
    render_bottom_nav("▲  Home")

