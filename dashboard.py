import streamlit as st
import datetime

from content.config import (
    PAGES,
    TICKER_OPTIONS,
)
from pages.home import render_home_page
from pages.phases import PHASE_RENDERERS, render_phase_page
from pages.reference import render_about_page, render_algo_families_page
from ui.styles import APP_CSS

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Quant Dashboard",
    page_icon="▲",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Styling ───────────────────────────────────────────────────────────────────
st.markdown(f"<style>{APP_CSS}</style>", unsafe_allow_html=True)


# ── Sidebar ───────────────────────────────────────────────────────────────────
_qp_page = st.query_params.get("page", "▲  Home")
if _qp_page not in PAGES:
    _qp_page = "▲  Home"
if "page" not in st.session_state:
    st.session_state["page"] = _qp_page
elif st.session_state.get("_last_query_page") != _qp_page:
    st.session_state["page"] = _qp_page
st.session_state["_last_query_page"] = _qp_page
if "anthropic_api_key" not in st.session_state:
    st.session_state["anthropic_api_key"] = ""

with st.sidebar:
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### ▲ QUANT BASICS")
    st.markdown("<p class='section-label'>Navigation</p>", unsafe_allow_html=True)

    _default_idx = PAGES.index(st.session_state.get("page", "▲  Home"))
    page = st.radio("Navigation", PAGES, index=_default_idx,
                    key="page", label_visibility="collapsed")
    st.query_params["page"] = page
    st.session_state["_last_query_page"] = page

    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown("<p class='section-label'>Benchmark to beat</p>", unsafe_allow_html=True)
    st.markdown("""
    <div style='font-family: JetBrains Mono; font-size: 0.7rem; line-height: 2; color: #4a5060;'>
    Sharpe  <span style='color:#e8ecf0; float:right'>> 0.49</span><br>
    Max DD  <span style='color:#e8ecf0; float:right'>> −35.75%</span>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown("<p class='section-label'>Universe (Phase 1)</p>", unsafe_allow_html=True)

    selected_tickers = st.multiselect(
        "Tickers",
        options=list(TICKER_OPTIONS.keys()),
        default=["SPY", "QQQ", "AAPL", "MSFT", "NVDA", "BTC-USD"],
        label_visibility="collapsed",
    )
    if not selected_tickers:
        selected_tickers = ["SPY"]

    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown("<p class='section-label'>Date range</p>", unsafe_allow_html=True)
    today = datetime.date.today()
    date_start = st.date_input("From", value=datetime.date(2020, 1, 1),
                               min_value=datetime.date(2010, 1, 1), max_value=today,
                               label_visibility="collapsed")
    date_end   = st.date_input("To",   value=today,
                               min_value=datetime.date(2010, 1, 2), max_value=today,
                               label_visibility="collapsed")
    START = str(date_start)
    END   = str(date_end)

    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown("<p class='section-label'>AI Insights (optional)</p>", unsafe_allow_html=True)
    api_key = st.text_input("Anthropic API key", type="password",
                            placeholder="sk-ant-...",
                            key="anthropic_api_key",
                            label_visibility="collapsed",
                            help="Add your Anthropic API key to get AI-generated chart summaries throughout the app.")
    if api_key:
        st.markdown("<p style='font-size:0.6rem;color:#00ff88;font-family:JetBrains Mono;'>✓ AI insights active</p>", unsafe_allow_html=True)
    else:
        st.markdown("<p style='font-size:0.6rem;color:#3a4050;font-family:JetBrains Mono;'>No key — static captions shown</p>", unsafe_allow_html=True)

# ── Session-state navigation (for clickable home cards) ───────────────────────
if page not in PAGES:
    page = "▲  Home"
    st.session_state["page"] = page
    st.query_params["page"] = page

# ════════════════════════════════════════════════════════════════════════════
#  HOME
# ════════════════════════════════════════════════════════════════════════════
if page == "▲  Home":
    render_home_page()


# ════════════════════════════════════════════════════════════════════════════
#  CURRICULUM PHASES
elif page in PHASE_RENDERERS:
    render_phase_page(page, START, END, selected_tickers, api_key)



# ════════════════════════════════════════════════════════════════════════════
#  QUANT ALGO FAMILIES
# ════════════════════════════════════════════════════════════════════════════
elif page == "◆ Quant Algo Families":
    render_algo_families_page(START, END, api_key)


# ════════════════════════════════════════════════════════════════════════════
#  ABOUT THE WRITER
# ════════════════════════════════════════════════════════════════════════════
elif page == "◇ About the Writer":
    render_about_page()
