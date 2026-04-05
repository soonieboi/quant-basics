import streamlit as st
import yfinance as yf
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from scipy.optimize import minimize
import statsmodels.api as sm
import anthropic
from urllib.parse import quote

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Quant Dashboard",
    page_icon="▲",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Styling ───────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@300;400;500;700&display=swap');

html, body, [class*="css"] {
    font-family: 'JetBrains Mono', monospace;
    background-color: #0a0a0f;
    color: #c8cdd6;
}
.stApp {
    background-color: #0a0a0f;
    background-image:
        radial-gradient(ellipse at 20% 50%, rgba(0,255,136,0.03) 0%, transparent 60%),
        radial-gradient(ellipse at 80% 20%, rgba(0,180,255,0.03) 0%, transparent 60%);
}
[data-testid="stSidebar"] {
    background-color: #0d0d14;
    border-right: 1px solid #1e2030;
}
[data-testid="metric-container"] {
    background-color: #0f0f18;
    border: 1px solid #1e2030;
    border-radius: 4px;
    padding: 1rem 1.2rem;
}
[data-testid="metric-container"] label {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.65rem !important;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    color: #4a5060 !important;
}
[data-testid="metric-container"] [data-testid="stMetricValue"] {
    font-family: 'JetBrains Mono', monospace;
    font-size: 1.4rem !important;
    font-weight: 500;
    color: #e8ecf0 !important;
}
[data-testid="metric-container"] [data-testid="stMetricDelta"] {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.7rem !important;
}
h1, h2, h3 { font-family: 'JetBrains Mono', monospace !important; letter-spacing: -0.02em; }
h1 { color: #e8ecf0 !important; font-weight: 700 !important; }
h2 { color: #b0b8c8 !important; font-weight: 500 !important; }
h3 { color: #7a8494 !important; font-weight: 400 !important; }
hr { border-color: #1e2030 !important; }

/* 101 explainer box */
.explainer-box {
    background: #0d0d14;
    border: 1px solid #1e2030;
    border-left: 3px solid #f5c518;
    border-radius: 4px;
    padding: 1.2rem 1.5rem;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.78rem;
    line-height: 1.9;
    color: #8a9ab0;
    margin-bottom: 1rem;
}
.explainer-box h4 {
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.7rem !important;
    letter-spacing: 0.2em;
    text-transform: uppercase;
    color: #f5c518 !important;
    margin-bottom: 0.8rem;
    font-weight: 600 !important;
}
.explainer-box b { color: #c8cdd6; }
.explainer-box code {
    background: #161820;
    padding: 1px 6px;
    border-radius: 3px;
    font-size: 0.75rem;
    color: #00ff88;
}
.explainer-box .formula {
    display: block;
    background: #161820;
    border: 1px solid #2a2d3a;
    padding: 0.6rem 1rem;
    border-radius: 3px;
    margin: 0.6rem 0;
    color: #00b4ff;
    font-size: 0.8rem;
    letter-spacing: 0.03em;
}
.explainer-box .rule {
    display: block;
    border-left: 2px solid #2a2d3a;
    padding-left: 0.8rem;
    margin: 0.4rem 0;
    color: #7a8494;
}
.explainer-box .good { color: #00ff88; }
.explainer-box .warn { color: #f5c518; }
.explainer-box .bad  { color: #ff4466; }

.phase-badge {
    display: inline-block;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.6rem;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    padding: 3px 10px;
    border-radius: 2px;
    background: #00ff88;
    color: #0a0a0f;
    font-weight: 700;
    margin-bottom: 0.5rem;
}
.phase-badge.yellow { background: #f5c518; }
.phase-badge.blue   { background: #00b4ff; }

.ticker-chip {
    display: inline-block;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.7rem;
    padding: 2px 8px;
    border: 1px solid #2a2d3a;
    border-radius: 2px;
    color: #7a8494;
    margin-right: 6px;
}
.section-label {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.6rem;
    letter-spacing: 0.25em;
    text-transform: uppercase;
    color: #3a4050;
    margin-bottom: 0.75rem;
}
.phase-card-link {
    text-decoration: none !important;
    color: inherit !important;
    display: block;
}
.phase-card {
    background:#0d0d14;
    border:1px solid #1e2030;
    border-top-width:2px;
    border-radius:4px;
    padding:1.2rem 1.3rem 0.8rem 1.3rem;
    margin-bottom:0.75rem;
    transition:border-color 0.15s ease, transform 0.15s ease, background 0.15s ease;
}
.phase-card:hover {
    border-color:#2a2d3a;
    background:#11131b;
    transform:translateY(-1px);
}
.home-band {
    border: 1px solid #1e2030;
    border-radius: 6px;
    padding: 1.15rem 1.2rem 1.25rem 1.2rem;
    margin: 1.1rem 0 1.4rem 0;
    background:
        linear-gradient(180deg, rgba(255,255,255,0.015) 0%, rgba(255,255,255,0.0) 100%),
        #0c0d14;
}
.home-band.learn {
    border-top: 2px solid #f5c518;
    box-shadow: inset 0 1px 0 rgba(245,197,24,0.08);
}
.home-band.trade {
    border-top: 2px solid #00ff88;
    box-shadow: inset 0 1px 0 rgba(0,255,136,0.08);
}
.home-band.field {
    border-top: 2px solid #26c6da;
    box-shadow: inset 0 1px 0 rgba(38,198,218,0.08);
}
.home-band-title {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.62rem;
    letter-spacing: 0.22em;
    text-transform: uppercase;
    color: #3a4050;
    margin-bottom: 0.55rem;
}
.home-band-copy {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.72rem;
    line-height: 1.9;
    color: #4a5060;
    max-width: 920px;
    margin-bottom: 1rem;
}
</style>
""", unsafe_allow_html=True)


# ── Helpers ───────────────────────────────────────────────────────────────────
@st.cache_data(show_spinner=False)
def load_prices(ticker, start="2020-01-01", end="2024-01-01"):
    df = yf.download(ticker, start=start, end=end, progress=False)
    return df["Close"].squeeze()


def compute_metrics(returns):
    ann_return  = returns.mean() * 252
    ann_vol     = returns.std() * np.sqrt(252)
    sharpe      = ann_return / ann_vol
    cumulative  = (1 + returns).cumprod()
    rolling_max = cumulative.cummax()
    max_dd      = ((cumulative - rolling_max) / rolling_max).min()
    return dict(ann_return=ann_return, ann_vol=ann_vol,
                sharpe=sharpe, max_dd=max_dd, cumulative=cumulative)


def hex_to_rgba(hex_color, alpha=0.08):
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"rgba({r},{g},{b},{alpha})"


def sma_signal(prices, fast, slow):
    """Returns daily 0/1 signal (shifted to avoid look-ahead bias)."""
    return (prices.rolling(fast).mean() > prices.rolling(slow).mean()).astype(int).shift(1)


def rsi_signal(prices, period=14, oversold=30, overbought=70):
    """Returns stateful 0/1 RSI signal (shifted)."""
    delta    = prices.diff()
    avg_gain = delta.clip(lower=0).ewm(com=period-1, min_periods=period).mean()
    avg_loss = (-delta).clip(lower=0).ewm(com=period-1, min_periods=period).mean()
    rsi      = 100 - (100 / (1 + avg_gain / avg_loss))
    pos, cur = pd.Series(0.0, index=prices.index), 0
    for i in range(len(rsi)):
        if np.isnan(rsi.iloc[i]):
            pos.iloc[i] = 0; continue
        if cur == 0 and rsi.iloc[i] < oversold:  cur = 1
        elif cur == 1 and rsi.iloc[i] > overbought: cur = 0
        pos.iloc[i] = cur
    return pos.shift(1), rsi


def apply_costs(log_returns, signal, cost_bps):
    """Subtract cost_bps on every trade (signal transition)."""
    trades = signal.diff().abs().fillna(0)
    return log_returns - trades * (cost_bps / 10000)


def strategy_returns(prices, sig):
    log_ret = np.log(prices / prices.shift(1))
    strat   = (log_ret * sig).dropna()
    bh      = log_ret.loc[strat.index]
    return strat, bh


PLOTLY_THEME = dict(
    paper_bgcolor="#0a0a0f",
    plot_bgcolor="#0d0d14",
    font=dict(family="JetBrains Mono", color="#5a6070", size=11),
    xaxis=dict(gridcolor="#161820", zeroline=False, showline=False),
    yaxis=dict(gridcolor="#161820", zeroline=False, showline=False),
    margin=dict(l=48, r=16, t=40, b=40),
)


# ── AI insight helper ─────────────────────────────────────────────────────────
@st.cache_data(show_spinner=False)
def ai_insight(prompt: str, api_key: str) -> str:
    """Call Claude Haiku to generate a 2-sentence plain-English chart insight."""
    if not api_key:
        return ""
    try:
        client = anthropic.Anthropic(api_key=api_key)
        msg = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=120,
            messages=[{"role": "user", "content":
                f"You are a quant finance tutor. In exactly 2 plain-English sentences, "
                f"explain what these results mean for a beginner learning quant trading. "
                f"Be specific about the numbers. No jargon without explanation. "
                f"Context: {prompt}"}],
        )
        return msg.content[0].text.strip()
    except Exception:
        return ""


def chart_caption(text: str):
    """Render a small styled caption below a chart."""
    if text:
        st.markdown(f"""
<div style='font-family:JetBrains Mono;font-size:0.7rem;color:#4a5060;line-height:1.7;
            border-left:2px solid #1e2030;padding:0.4rem 0.8rem;margin:0.2rem 0 1.2rem 0;'>
{text}
</div>""", unsafe_allow_html=True)


CURRICULUM_ORDER = [
    "▲  Home",
    "Phase 1 — Asset Metrics",
    "Phase 2 — SMA Crossover",
    "Phase 3 — RSI Mean Reversion",
    "Phase 4 — Transaction Costs",
    "Phase 5 — Combining Signals",
    "Phase 6 — Walk-Forward Validation",
    "Phase 7 — Position Sizing",
    "Phase 8 — Portfolio Construction",
    "Phase 9 — Risk Management",
    "Phase 10 — Factor Models",
    "Phase 11 — Statistical Rigor",
    "Phase 12 — Market Microstructure",
    "◆ Quant Algo Families",
]


def render_bottom_nav(current_page: str):
    if current_page not in CURRICULUM_ORDER:
        return

    idx = CURRICULUM_ORDER.index(current_page)
    prev_page = CURRICULUM_ORDER[idx - 1] if idx > 0 else None
    next_page = CURRICULUM_ORDER[idx + 1] if idx < len(CURRICULUM_ORDER) - 1 else None

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("<hr>", unsafe_allow_html=True)
    left, center, right = st.columns([1.2, 2.2, 1.2])

    with left:
        if prev_page:
            prev_label = "← Home" if prev_page == "▲  Home" else f"← {prev_page.split(' — ', 1)[-1]}"
            if st.button(prev_label, key=f"nav_prev_{idx}", use_container_width=True):
                st.query_params["page"] = prev_page
                st.rerun()

    with center:
        st.markdown(f"""
<div style='text-align:center;padding-top:0.45rem;'>
    <div style='font-family:JetBrains Mono;font-size:0.6rem;letter-spacing:0.18em;
                text-transform:uppercase;color:#3a4050;margin-bottom:0.2rem;'>
        Navigation
    </div>
    <div style='font-family:JetBrains Mono;font-size:0.72rem;color:#4a5060;line-height:1.6;'>
        {current_page}
    </div>
</div>
""", unsafe_allow_html=True)

    with right:
        if next_page:
            next_label = "Atlas →" if next_page == "◆ Quant Algo Families" else f"{next_page.split(' — ', 1)[-1]} →"
            if st.button(next_label, key=f"nav_next_{idx}", use_container_width=True):
                st.query_params["page"] = next_page
                st.rerun()


# ── Sidebar ───────────────────────────────────────────────────────────────────
_all_pages = ["▲  Home","Phase 1 — Asset Metrics","Phase 2 — SMA Crossover",
              "Phase 3 — RSI Mean Reversion","Phase 4 — Transaction Costs",
              "Phase 5 — Combining Signals","Phase 6 — Walk-Forward Validation",
              "Phase 7 — Position Sizing","Phase 8 — Portfolio Construction",
              "Phase 9 — Risk Management","Phase 10 — Factor Models",
              "Phase 11 — Statistical Rigor","Phase 12 — Market Microstructure",
              "◆ Quant Algo Families"]
_qp_page = st.query_params.get("page", "▲  Home")
if _qp_page not in _all_pages:
    _qp_page = "▲  Home"
if st.session_state.get("page") != _qp_page:
    st.session_state["page"] = _qp_page
if "anthropic_api_key" not in st.session_state:
    st.session_state["anthropic_api_key"] = ""

with st.sidebar:
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### ▲ QUANT BASICS")
    st.markdown("<p class='section-label'>Navigation</p>", unsafe_allow_html=True)

    _default_idx = _all_pages.index(st.session_state.get("page", "▲  Home"))
    page = st.radio("Navigation", _all_pages, index=_default_idx,
                    key="page", label_visibility="collapsed")
    st.query_params["page"] = page

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

    TICKER_OPTIONS = {
        # Indices
        "SPY":    "#00ff88",
        "QQQ":    "#00b4ff",
        "DIA":    "#7ec8e3",
        "IWM":    "#5a8a6a",
        # Tech
        "AAPL":   "#f5c518",
        "MSFT":   "#4fc3f7",
        "NVDA":   "#76ff03",
        "GOOGL":  "#ff7043",
        "AMZN":   "#ffca28",
        "META":   "#7986cb",
        "TSLA":   "#ef5350",
        # Crypto
        "BTC-USD": "#f7931a",
        "ETH-USD": "#627eea",
    }

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
    import datetime
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
PAGES = ["▲  Home","Phase 1 — Asset Metrics","Phase 2 — SMA Crossover",
         "Phase 3 — RSI Mean Reversion","Phase 4 — Transaction Costs",
         "Phase 5 — Combining Signals","Phase 6 — Walk-Forward Validation",
         "Phase 7 — Position Sizing","Phase 8 — Portfolio Construction",
         "Phase 9 — Risk Management","Phase 10 — Factor Models",
         "Phase 11 — Statistical Rigor","Phase 12 — Market Microstructure",
         "◆ Quant Algo Families"]
if page not in PAGES:
    page = "▲  Home"
    st.session_state["page"] = page
    st.query_params["page"] = page

# ════════════════════════════════════════════════════════════════════════════
#  HOME
# ════════════════════════════════════════════════════════════════════════════
if page == "▲  Home":

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
    st.markdown("""
<div class='home-band learn'>
<div class='home-band-title'>Learn the Path</div>
<div class='home-band-copy'>
    Start with the numbered phases below. They are ordered as a practical curriculum:
    measure markets, build signals, test honestly, size risk, then understand portfolio construction and execution.
</div>
<div>
""", unsafe_allow_html=True)

    PHASES = [
        {
            "num": "01", "badge": "#f5c518", "title": "Asset Metrics",
            "tag": "FOUNDATIONS",
            "desc": "Pull SPY, QQQ, BTC data via yfinance. Compute annualised return, volatility, Sharpe ratio, and max drawdown. Establish your baseline to beat.",
            "concepts": ["Log returns", "Sharpe ratio", "Max drawdown", "Annualisation"],
        },
        {
            "num": "02", "badge": "#00ff88", "title": "SMA Crossover",
            "tag": "STRATEGY",
            "desc": "Build a trend-following strategy using golden cross / death cross signals. Introduces look-ahead bias — the most common backtest trap.",
            "concepts": ["Moving averages", "Trend-following", "Look-ahead bias", "Signal generation"],
        },
        {
            "num": "03", "badge": "#00b4ff", "title": "RSI Mean Reversion",
            "tag": "STRATEGY",
            "desc": "The opposite paradigm: buy oversold dips, sell overbought rallies. Learn why trend-following and mean reversion complement each other.",
            "concepts": ["RSI indicator", "Mean reversion", "Overbought/oversold", "Stateful signals"],
        },
        {
            "num": "04", "badge": "#ff4466", "title": "Transaction Costs",
            "tag": "BACKTESTING",
            "desc": "Why strategies that look great on paper often fail in reality. Model bid-ask spread and slippage. See how trade frequency determines cost sensitivity.",
            "concepts": ["Basis points", "Bid-ask spread", "Slippage", "Cost-adjusted Sharpe"],
        },
        {
            "num": "05", "badge": "#b48ead", "title": "Combining Signals",
            "tag": "BACKTESTING",
            "desc": "Run both SMA and RSI simultaneously. Combine them with AND, OR, and fractional averaging. Diversification of signals — not just assets.",
            "concepts": ["Signal ensembles", "AND/OR logic", "Fractional sizing", "Signal correlation"],
        },
        {
            "num": "06", "badge": "#ff7043", "title": "Walk-Forward Validation",
            "tag": "BACKTESTING",
            "desc": "The honest test. Grid-search parameters in-sample, apply them out-of-sample. See the gap between fitted performance and real performance.",
            "concepts": ["Overfitting", "In-sample / OOS", "Parameter grid search", "Degradation ratio"],
        },
        {
            "num": "07", "badge": "#ffca28", "title": "Position Sizing",
            "tag": "EXECUTION",
            "desc": "Right strategy, wrong bet size = blown account. Learn the Kelly criterion — the mathematically optimal fraction — and why half-Kelly is safer.",
            "concepts": ["Kelly criterion", "Fixed fractional", "Geometric growth", "Leverage limits"],
        },
        {
            "num": "08", "badge": "#4fc3f7", "title": "Portfolio Construction",
            "tag": "PORTFOLIO",
            "desc": "Combine multiple assets optimally. Build the efficient frontier with 3,000 simulated portfolios. Find max Sharpe and minimum volatility allocations.",
            "concepts": ["Correlation matrix", "Efficient frontier", "Mean-variance optimisation", "Markowitz"],
        },
        {
            "num": "09", "badge": "#ff4466", "title": "Risk Management",
            "tag": "PORTFOLIO",
            "desc": "Know when to stop. Model Value at Risk (VaR), Expected Shortfall, drawdown circuit breakers, and volatility-regime detection.",
            "concepts": ["VaR", "CVaR / Expected Shortfall", "Drawdown limits", "Regime detection"],
        },
        {
            "num": "10", "badge": "#76ff03", "title": "Factor Models",
            "tag": "ADVANCED",
            "desc": "Decompose returns into alpha and beta. Measure true market-independent edge via CAPM regression. See rolling beta shift over time.",
            "concepts": ["CAPM", "Alpha", "Beta", "Rolling OLS regression"],
        },
        {
            "num": "11", "badge": "#b48ead", "title": "Statistical Rigor",
            "tag": "ADVANCED",
            "desc": "A Sharpe of 0.8 is not a fact — it's an estimate with a confidence interval. Bootstrap your Sharpe, correct for multiple testing, compute minimum backtest length.",
            "concepts": ["Bootstrap CI", "Multiple testing", "Bonferroni correction", "Min backtest length"],
        },
        {
            "num": "12", "badge": "#ff7043", "title": "Market Microstructure",
            "tag": "ADVANCED",
            "desc": "What actually happens when you click Buy. Order types, spread dynamics, intraday patterns, return autocorrelation, and seasonality.",
            "concepts": ["Order book", "Market vs limit orders", "Autocorrelation", "Seasonality"],
        },
    ]

    TAG_COLORS = {
        "FOUNDATIONS": "#f5c518",
        "STRATEGY":    "#00ff88",
        "BACKTESTING": "#ff7043",
        "EXECUTION":   "#ffca28",
        "PORTFOLIO":   "#00b4ff",
        "ADVANCED":    "#b48ead",
    }

    # Phase → nav page name mapping
    PHASE_NAV = {
        "01": "Phase 1 — Asset Metrics",   "02": "Phase 2 — SMA Crossover",
        "03": "Phase 3 — RSI Mean Reversion", "04": "Phase 4 — Transaction Costs",
        "05": "Phase 5 — Combining Signals",  "06": "Phase 6 — Walk-Forward Validation",
        "07": "Phase 7 — Position Sizing",    "08": "Phase 8 — Portfolio Construction",
        "09": "Phase 9 — Risk Management",    "10": "Phase 10 — Factor Models",
        "11": "Phase 11 — Statistical Rigor", "12": "Phase 12 — Market Microstructure",
    }

    # render 3 cards per row
    for row_start in range(0, len(PHASES), 3):
        cols = st.columns(3)
        for col, phase in zip(cols, PHASES[row_start:row_start+3]):
            tag_color = TAG_COLORS.get(phase["tag"], "#5a6070")
            concepts_html = "".join(
                f"<span style='display:inline-block;font-size:0.6rem;padding:1px 7px;"
                f"border:1px solid #1e2030;border-radius:2px;color:#4a5060;"
                f"margin:2px 3px 2px 0;font-family:JetBrains Mono;'>{c}</span>"
                for c in phase["concepts"]
            )
            with col:
                nav_target = PHASE_NAV.get(phase["num"], "▲  Home")
                nav_href = f"?page={quote(nav_target)}"
                st.markdown(f"""
<a class='phase-card-link' href='{nav_href}'>
<div class='phase-card' style='border-top-color:{phase["badge"]};'>
    <div style='display:flex;align-items:center;gap:0.6rem;margin-bottom:0.7rem;'>
        <span style='font-family:JetBrains Mono;font-size:1.4rem;font-weight:700;
                     color:{phase["badge"]};line-height:1;'>{phase["num"]}</span>
        <span style='font-family:JetBrains Mono;font-size:0.55rem;letter-spacing:0.2em;
                     text-transform:uppercase;color:{tag_color};background:{tag_color}18;
                     padding:2px 8px;border-radius:2px;'>{phase["tag"]}</span>
    </div>
    <div style='font-family:JetBrains Mono;font-size:0.95rem;font-weight:600;
                color:#c8cdd6;margin-bottom:0.6rem;letter-spacing:-0.01em;'>
        {phase["title"]}
    </div>
    <div style='font-family:JetBrains Mono;font-size:0.72rem;color:#4a5060;
                line-height:1.7;margin-bottom:0.8rem;'>
        {phase["desc"]}
    </div>
    <div>{concepts_html}</div>
    <div style='font-family:JetBrains Mono;font-size:0.66rem;color:{phase["badge"]};
                margin-top:0.9rem;letter-spacing:0.08em;text-transform:uppercase;'>
        Open Phase {phase["num"]} →
    </div>
</div>
</a>
""", unsafe_allow_html=True)

    st.markdown("</div></div>", unsafe_allow_html=True)
    st.markdown("""
<div class='home-band trade'>
<div class='home-band-title'>Use in Real Trading</div>
<div class='home-band-copy'>
    This is the bridge from a backtest to actual deployment. The workflow below is the operating loop:
    research, encode rules, validate, deploy small, and monitor continuously.
</div>
<div>
""", unsafe_allow_html=True)
    workflow_steps = [
        ("01", "Research", "Pick markets with enough liquidity, acceptable drawdown, and behavior you can actually explain."),
        ("02", "Encode Rules", "Turn an idea into precise entry, exit, and sizing logic with no discretion hidden in the backtest."),
        ("03", "Reality Check", "Apply costs, out-of-sample testing, and statistical checks to see if the edge survives contact with reality."),
        ("04", "Deploy Small", "Trade tiny size first or paper trade, then compare live slippage and behavior against the historical model."),
        ("05", "Monitor", "Track drawdown, beta, regime shifts, and execution drift. If the live edge breaks, reduce or stop."),
    ]
    for row_start in range(0, len(workflow_steps), 3):
        cols = st.columns(3)
        for col, (num, title, desc) in zip(cols, workflow_steps[row_start:row_start+3]):
            with col:
                st.markdown(f"""
<div style='background:#0d0d14;border:1px solid #1e2030;border-top:2px solid #00ff88;
            border-radius:4px;padding:1rem 1rem 0.9rem 1rem;margin-bottom:0.85rem;height:100%;'>
    <div style='font-family:JetBrains Mono;font-size:0.62rem;letter-spacing:0.18em;
                text-transform:uppercase;color:#3a4050;margin-bottom:0.55rem;'>
        Step {num}
    </div>
    <div style='font-family:JetBrains Mono;font-size:0.9rem;font-weight:600;
                color:#e8ecf0;margin-bottom:0.5rem;'>
        {title}
    </div>
    <div style='font-family:JetBrains Mono;font-size:0.7rem;line-height:1.7;color:#4a5060;'>
        {desc}
                </div>
</div>
""", unsafe_allow_html=True)

    st.markdown("</div></div>", unsafe_allow_html=True)
    st.markdown("""
<div class='home-band field'>
<div class='home-band-title'>Explore the Field</div>
<div class='home-band-copy'>
    These are the major families of systematic trading. They are reference material, not curriculum steps,
    so they live in a separate atlas page rather than inside the numbered learning path.
</div>
<div>
""", unsafe_allow_html=True)
    algo_cards = [
        ("Trend-Following", "#00ff88", "Ride persistent moves. SMA crossovers, breakout systems, time-series momentum."),
        ("Mean Reversion", "#00b4ff", "Bet that stretched prices snap back. RSI, z-score bands, pairs reversion."),
        ("Cross-Sectional Momentum", "#f5c518", "Rank assets and own the relative winners while avoiding laggards."),
        ("Stat Arb", "#ff4466", "Exploit short-lived pricing dislocations across related instruments or baskets."),
        ("Factor Investing", "#76ff03", "Systematically target exposures like value, momentum, quality, and size."),
        ("Market Making", "#ff7043", "Quote both sides of the market and earn spread while controlling inventory risk."),
        ("Volatility / Options", "#b48ead", "Trade implied vs realized vol, skew, convexity, and hedging dynamics."),
        ("ML / Forecasting", "#4fc3f7", "Use features and models to predict returns, risk, or execution quality."),
    ]
    for row_start in range(0, len(algo_cards), 2):
        cols = st.columns(2)
        for col, (title, color, desc) in zip(cols, algo_cards[row_start:row_start+2]):
            with col:
                st.markdown(f"""
<div style='background:#0d0d14;border:1px solid #1e2030;border-left:3px solid {color};
            border-radius:4px;padding:1rem 1.1rem;margin-bottom:0.85rem;'>
    <div style='font-family:JetBrains Mono;font-size:0.85rem;font-weight:600;
                color:#c8cdd6;margin-bottom:0.45rem;'>
        {title}
    </div>
    <div style='font-family:JetBrains Mono;font-size:0.7rem;line-height:1.7;color:#4a5060;'>
        {desc}
    </div>
</div>
""", unsafe_allow_html=True)

    st.markdown("""
<div style='background:#0d0d14;border:1px solid #1e2030;border-left:3px solid #26c6da;
            border-radius:4px;padding:0.95rem 1.1rem;margin-bottom:0.8rem;max-width:920px;'>
    <div style='font-family:JetBrains Mono;font-size:0.7rem;line-height:1.8;color:#4a5060;'>
        <span style='display:block;font-size:0.62rem;letter-spacing:0.18em;text-transform:uppercase;color:#3a4050;margin-bottom:0.35rem;'>
            Strategy Atlas
        </span>
        Open <span style='color:#26c6da;'>◆ Quant Algo Families</span> from the sidebar for the full taxonomy,
        tradeoffs, and implementation notes.
    </div>
</div>
""", unsafe_allow_html=True)
    st.markdown("</div></div>", unsafe_allow_html=True)

    st.markdown("""
<div style='font-family:JetBrains Mono;font-size:0.65rem;color:#2a2d3a;
            text-align:center;padding:1rem 0 0.5rem 0;line-height:2;'>
    All computations run live on real market data via yfinance &nbsp;·&nbsp;
    Select any phase in the sidebar to begin &nbsp;·&nbsp;
    Every module includes a 101 explainer — click to expand
</div>
""", unsafe_allow_html=True)
    render_bottom_nav("▲  Home")


# ════════════════════════════════════════════════════════════════════════════
#  PHASE 1 — ASSET METRICS
# ════════════════════════════════════════════════════════════════════════════
elif page == "Phase 1 — Asset Metrics":

    st.markdown("<span class='phase-badge yellow'>Phase 1</span>", unsafe_allow_html=True)
    st.markdown("## Asset Universe Metrics")
    st.markdown(f"<p class='section-label'>Annualised · log returns · {START} → {END}</p>", unsafe_allow_html=True)

    # ── 101 Explainer ──────────────────────────────────────────────────────────
    with st.expander("101 — What are we measuring and why?", expanded=False):
        st.markdown("""
<div class='explainer-box'>
<h4>The four metrics every quant lives by</h4>

Before building any strategy, you need to understand what you're measuring.
Think of these as the "unit tests" for financial performance.

<br>

<b>1. Returns — but why log returns?</b><br>
You might expect us to use simple returns: <code>(price_today - price_yesterday) / price_yesterday</code>.
We use <b>log returns</b> instead: <code>log(price_today / price_yesterday)</code>.
<br>
Why? Two reasons:
<span class='rule'>They're <b>additive over time</b>. A 3-day log return = day1 + day2 + day3. Simple returns multiply, which is harder to work with mathematically.</span>
<span class='rule'>They're <b>symmetric</b>. A +50% gain followed by a -50% loss in simple returns doesn't get you back to 1.0. Log returns behave consistently.</span>

<br>

<b>2. Annualised Return</b>
<span class='formula'>Ann. Return = mean(daily_log_returns) × 252</span>
There are ~252 trading days in a year. We scale daily average returns up to get a yearly figure.
<span class='rule'>SPY gave <b class='good'>+11.1%/year</b> over this period. That's the passive "do nothing" baseline.</span>

<br>

<b>3. Volatility (Risk)</b>
<span class='formula'>Ann. Vol = std(daily_log_returns) × √252</span>
Volatility is the standard deviation of returns — it measures how much prices jump around.
High volatility = risky. We multiply by √252 to annualise it (standard stats rule for scaling std dev over time).
<span class='rule'>SPY: <b>22.7%</b> vol. BTC: much higher — it moves wildly. High vol isn't always bad, but you need to be paid for the risk.</span>

<br>

<b>4. Sharpe Ratio — the core risk-adjusted metric</b>
<span class='formula'>Sharpe = Ann. Return / Ann. Volatility</span>
The Sharpe ratio asks: <b>how much return are you getting per unit of risk?</b>
It's return divided by risk. Higher is better. It lets you compare strategies fairly — a 5% return with tiny volatility beats a 20% return with huge swings.
<span class='rule'><b class='bad'>< 0.5</b> — poor. Taking too much risk for the return.</span>
<span class='rule'><b class='warn'>0.5 – 1.0</b> — acceptable. Most passive indices live here.</span>
<span class='rule'><b class='good'>> 1.0</b> — good. Hedge funds aim for this.</span>
<span class='rule'><b class='good'>> 2.0</b> — exceptional. Very rare in practice.</span>
Note: In real life you'd subtract the risk-free rate (e.g. T-bill yield) from the return first. We're ignoring that here for simplicity.

<br>

<b>5. Max Drawdown — the gut-punch metric</b>
<span class='formula'>Drawdown(t) = (cumulative_return(t) - peak_so_far) / peak_so_far</span>
<span class='formula'>Max Drawdown = min(Drawdown) over all time</span>
This answers: <b>what was the worst loss from a peak to a trough?</b>
If you invested $100 and it fell to $64.25 before recovering, your max drawdown is -35.75%.
<span class='rule'>SPY: <b class='warn'>-35.75%</b> (COVID crash 2020). Could you hold without selling? Most people can't.</span>
<span class='rule'>BTC: <b class='bad'>-83.72%</b>. It recovered — but you need extreme conviction to not panic-sell.</span>
Max drawdown is important because strategies that look great on paper can destroy you psychologically if the drawdown is too deep.

</div>
""", unsafe_allow_html=True)

    # ── Data ───────────────────────────────────────────────────────────────────
    tickers = {t: TICKER_OPTIONS[t] for t in selected_tickers}
    rows = []
    cumulative_map = {}
    with st.spinner("Pulling data…"):
        for ticker in tickers:
            prices  = load_prices(ticker, START, END)
            returns = np.log(prices / prices.shift(1)).dropna()
            m       = compute_metrics(returns)
            rows.append({
                "Ticker":       ticker.replace("-USD", ""),
                "Ann. Return":  m["ann_return"],
                "Ann. Vol":     m["ann_vol"],
                "Sharpe":       m["sharpe"],
                "Max Drawdown": m["max_dd"],
            })
            cumulative_map[ticker] = m["cumulative"]

    # ── KPI strip ─────────────────────────────────────────────────────────────
    baseline = selected_tickers[0].replace("-USD", "")
    cols = st.columns(4)
    kpi_labels = ["Ann. Return", "Ann. Vol", "Sharpe", "Max Drawdown"]
    for col, lbl in zip(cols, kpi_labels):
        with col:
            vals = {r["Ticker"]: r[lbl] for r in rows}
            fmt  = "{:.2f}" if lbl == "Sharpe" else "{:.2%}"
            st.metric(label=lbl,
                      value=fmt.format(vals[baseline]),
                      delta=f"{baseline} baseline")

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Table ─────────────────────────────────────────────────────────────────
    st.markdown("<p class='section-label'>Full breakdown</p>", unsafe_allow_html=True)
    df_table = pd.DataFrame(rows).set_index("Ticker")
    df_table["Ann. Return"]  = df_table["Ann. Return"].map("{:.2%}".format)
    df_table["Ann. Vol"]     = df_table["Ann. Vol"].map("{:.2%}".format)
    df_table["Sharpe"]       = df_table["Sharpe"].map("{:.2f}".format)
    df_table["Max Drawdown"] = df_table["Max Drawdown"].map("{:.2%}".format)
    st.dataframe(df_table, width="stretch")

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Equity curves ─────────────────────────────────────────────────────────
    st.markdown("<p class='section-label'>Growth of $1</p>", unsafe_allow_html=True)
    fig = go.Figure()
    for ticker, color in tickers.items():
        curve = cumulative_map[ticker]
        lbl   = ticker.replace("-USD", "")
        fig.add_trace(go.Scatter(
            x=curve.index, y=curve.values, name=lbl,
            line=dict(color=color, width=1.5),
            hovertemplate=f"<b>{lbl}</b><br>%{{x|%Y-%m-%d}}<br>$%{{y:.3f}}<extra></extra>",
        ))
    fig.update_layout(**PLOTLY_THEME, height=340,
                      legend=dict(orientation="h", y=1.08, x=0, font=dict(size=10)),
                      yaxis_title="Growth of $1", hovermode="x unified")
    st.plotly_chart(fig, width="stretch")
    best_row = max(rows, key=lambda r: r["Sharpe"])
    chart_caption(ai_insight(
        f"Equity curves for {', '.join(r['Ticker'] for r in rows)} from {START} to {END}. "
        f"Best Sharpe: {best_row['Ticker']} at {best_row['Sharpe']:.2f}. "
        f"SPY annualised return: {rows[0]['Ann. Return']:.2%}, vol: {rows[0]['Ann. Vol']:.2%}.",
        api_key) or
        f"Each line shows how $1 invested grew over time. "
        f"The steeper and smoother the curve, the better the risk-adjusted performance. "
        f"{best_row['Ticker']} had the highest Sharpe ratio ({best_row['Sharpe']:.2f}) in this period.")

    # ── Drawdown chart ─────────────────────────────────────────────────────────
    st.markdown("<p class='section-label'>Drawdown</p>", unsafe_allow_html=True)
    fig2 = go.Figure()
    for ticker, color in tickers.items():
        prices  = load_prices(ticker)
        returns = np.log(prices / prices.shift(1)).dropna()
        cum     = (1 + returns).cumprod()
        dd      = (cum - cum.cummax()) / cum.cummax()
        lbl     = ticker.replace("-USD", "")
        fig2.add_trace(go.Scatter(
            x=dd.index, y=dd.values, name=lbl,
            fill="tozeroy", line=dict(color=color, width=1),
            fillcolor=hex_to_rgba(color, 0.08),
            hovertemplate=f"<b>{lbl}</b><br>%{{x|%Y-%m-%d}}<br>%{{y:.2%}}<extra></extra>",
        ))
    fig2.update_layout(**PLOTLY_THEME, height=260,
                       legend=dict(orientation="h", y=1.08, x=0, font=dict(size=10)),
                       hovermode="x unified")
    fig2.update_yaxes(tickformat=".0%", zeroline=True, zerolinecolor="#2a2d3a")
    st.plotly_chart(fig2, width="stretch")
    worst_dd = min(rows, key=lambda r: r["Max Drawdown"])
    chart_caption(ai_insight(
        f"Drawdown chart for {', '.join(r['Ticker'] for r in rows)}. "
        f"Worst max drawdown: {worst_dd['Ticker']} at {worst_dd['Max Drawdown']:.2%}. "
        f"SPY max drawdown: {rows[0]['Max Drawdown']:.2%}.",
        api_key) or
        f"Drawdown measures how far each asset fell from its previous peak. "
        f"{worst_dd['Ticker']} had the deepest drawdown at {worst_dd['Max Drawdown']:.2%} — "
        f"meaning if you bought at the top, you'd have been down that much at the worst point.")
    render_bottom_nav("Phase 1 — Asset Metrics")


# ════════════════════════════════════════════════════════════════════════════
#  PHASE 2 — SMA CROSSOVER
# ════════════════════════════════════════════════════════════════════════════
elif page == "Phase 2 — SMA Crossover":

    st.markdown("<span class='phase-badge'>Phase 2</span>", unsafe_allow_html=True)
    st.markdown("## SMA Crossover Strategy")
    st.markdown(f"<p class='section-label'>Trend-following · Golden cross / death cross · {START} → {END}</p>", unsafe_allow_html=True)

    # ── 101 Explainer ──────────────────────────────────────────────────────────
    with st.expander("101 — How does this strategy work?", expanded=False):
        st.markdown("""
<div class='explainer-box'>
<h4>Trend-following with moving average crossovers</h4>

<b>What is a Moving Average?</b><br>
A Simple Moving Average (SMA) smooths out day-to-day price noise by averaging the last N closing prices.
<code>SMA(50)</code> = average of the last 50 closing prices, updated daily.
The longer the window, the smoother (and slower) it is.

<br>

<b>Why two moving averages?</b><br>
<span class='rule'><b>Fast SMA</b> (e.g. 50-day): reacts quickly to recent price changes.</span>
<span class='rule'><b>Slow SMA</b> (e.g. 200-day): represents the long-term trend.</span>
When the fast SMA crosses <b>above</b> the slow SMA, recent prices are higher than the long-term average — the market is trending up. This is called a <b class='good'>Golden Cross</b>.
When the fast SMA crosses <b>below</b> the slow SMA, the trend has reversed. This is a <b class='bad'>Death Cross</b>.

<br>

<b>The signal logic</b>
<span class='formula'>signal = 1 (long) if SMA_fast > SMA_slow, else 0 (flat/cash)</span>
We are either fully in (100% long SPY) or fully out (holding cash). No shorting, no leverage.

<br>

<b>The most important implementation detail: .shift(1)</b><br>
We shift the signal forward by 1 day. Why? Because you calculate today's SMA using today's closing price — and you can't trade at that price. You trade the <i>next day</i>.
Forgetting this shift is called <b class='bad'>look-ahead bias</b> — your backtest secretly "knows the future" and produces unrealistically good results. A common beginner trap.

<br>

<b>What kind of strategy is this?</b><br>
This is a <b>trend-following</b> strategy. The core assumption: <i>markets that are going up tend to keep going up</i> (momentum). You get in when the trend starts and get out when it breaks.
<span class='rule'><b class='good'>Works well in</b>: sustained bull or bear markets (clear trends).</span>
<span class='rule'><b class='bad'>Fails in</b>: choppy, sideways markets — you get lots of false signals and whipsaws.</span>

<br>

<b>Why did this beat buy-and-hold in 2020–2024?</b><br>
The 2022 bear market. The death cross hit in early 2022, taking us to cash before the worst of the decline. We missed the drawdown while buy-and-hold investors sat through -35.75%.
The cost: we were in cash 41% of the time and missed some upside. But the Sharpe nearly doubled because our volatility was much lower.

<br>

<b>The honest caveats</b><br>
<span class='rule'>Only 3 trades in 4 years — tiny sample size. Hard to be confident.</span>
<span class='rule'>No transaction costs or slippage modelled (Phase 4 fixes this).</span>
<span class='rule'>Cash earns 0% — in reality you'd earn T-bill rates (~5% in 2023).</span>
<span class='rule'>Past regime may not repeat — SMA crossover can fail badly in other periods.</span>

</div>
""", unsafe_allow_html=True)

    # ── Controls ───────────────────────────────────────────────────────────────
    col_t, col_a, col_b, _ = st.columns([1, 1, 1, 3])
    with col_t:
        strat_ticker = st.selectbox("Ticker", options=list(TICKER_OPTIONS.keys()), index=0)
    with col_a:
        fast_window = st.number_input("Fast SMA", min_value=5, max_value=100, value=50, step=5)
    with col_b:
        slow_window = st.number_input("Slow SMA", min_value=20, max_value=400, value=200, step=10)

    if fast_window >= slow_window:
        st.warning("Fast window must be smaller than slow window.")
        st.stop()

    # ── Compute ────────────────────────────────────────────────────────────────
    with st.spinner("Computing…"):
        prices    = load_prices(strat_ticker, START, END)
        sma_fast  = prices.rolling(fast_window).mean()
        sma_slow  = prices.rolling(slow_window).mean()
        signal    = (sma_fast > sma_slow).astype(int).shift(1)
        log_ret   = np.log(prices / prices.shift(1))
        strat_ret = (log_ret * signal).dropna()
        bh_ret    = log_ret.loc[strat_ret.index]
        m_bh      = compute_metrics(bh_ret)
        m_strat   = compute_metrics(strat_ret)
        total_days = len(signal.dropna())
        days_long  = int(signal.sum())
        num_trades = int((signal.diff().abs() == 1).sum())

    # ── KPIs ───────────────────────────────────────────────────────────────────
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Sharpe",       f"{m_strat['sharpe']:.2f}",     f"{m_strat['sharpe']-m_bh['sharpe']:+.2f} vs B&H")
    c2.metric("Max Drawdown", f"{m_strat['max_dd']:.2%}",     f"{m_strat['max_dd']-m_bh['max_dd']:+.2%} vs B&H")
    c3.metric("Ann. Return",  f"{m_strat['ann_return']:.2%}", f"{m_strat['ann_return']-m_bh['ann_return']:+.2%} vs B&H")
    c4.metric("# Trades",     str(num_trades),                f"{days_long/total_days:.0%} time invested")

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Chart ─────────────────────────────────────────────────────────────────
    st.markdown("<p class='section-label'>Price · equity curve · position</p>", unsafe_allow_html=True)
    fig = make_subplots(rows=3, cols=1, shared_xaxes=True,
                        row_heights=[0.5, 0.35, 0.15], vertical_spacing=0.03,
                        subplot_titles=("", "", ""))

    fig.add_trace(go.Scatter(x=prices.index, y=prices.values, name="SPY",
        line=dict(color="#c8cdd6", width=1),
        hovertemplate="%{x|%Y-%m-%d}  $%{y:.2f}<extra></extra>"), row=1, col=1)
    fig.add_trace(go.Scatter(x=sma_fast.index, y=sma_fast.values, name=f"SMA {fast_window}",
        line=dict(color="#00b4ff", width=1.2, dash="dot"),
        hovertemplate=f"SMA{fast_window}: $%{{y:.2f}}<extra></extra>"), row=1, col=1)
    fig.add_trace(go.Scatter(x=sma_slow.index, y=sma_slow.values, name=f"SMA {slow_window}",
        line=dict(color="#f5c518", width=1.2, dash="dot"),
        hovertemplate=f"SMA{slow_window}: $%{{y:.2f}}<extra></extra>"), row=1, col=1)

    sig_aligned   = signal.reindex(prices.index).fillna(0)
    shade_y_upper = prices.where(sig_aligned == 1)
    fig.add_trace(go.Scatter(x=prices.index, y=shade_y_upper.values,
        fill="tonexty", fillcolor="rgba(0,255,136,0.05)",
        line=dict(width=0), showlegend=False, hoverinfo="skip"), row=1, col=1)

    fig.add_trace(go.Scatter(x=m_bh["cumulative"].index, y=m_bh["cumulative"].values,
        name="Buy & Hold", line=dict(color="#5a6070", width=1.2),
        hovertemplate="B&H: $%{y:.3f}<extra></extra>"), row=2, col=1)
    fig.add_trace(go.Scatter(x=m_strat["cumulative"].index, y=m_strat["cumulative"].values,
        name="Strategy", line=dict(color="#00ff88", width=1.5),
        hovertemplate="Strategy: $%{y:.3f}<extra></extra>"), row=2, col=1)

    fig.add_trace(go.Scatter(x=sig_aligned.index, y=sig_aligned.values,
        name="Position", line=dict(color="#00b4ff", width=0.8),
        fill="tozeroy", fillcolor="rgba(0,180,255,0.08)",
        hovertemplate="Position: %{y}<extra></extra>"), row=3, col=1)

    fig.update_layout(**PLOTLY_THEME, height=620,
                      legend=dict(orientation="h", y=1.02, x=0, font=dict(size=10), bgcolor="rgba(0,0,0,0)"),
                      hovermode="x unified")
    fig.update_yaxes(gridcolor="#161820", row=1)
    fig.update_yaxes(gridcolor="#161820", row=2, title_text="Growth $1")
    fig.update_yaxes(gridcolor="#161820", tickvals=[0, 1], ticktext=["Flat", "Long"], row=3)
    fig.update_xaxes(gridcolor="#161820")
    st.plotly_chart(fig, width="stretch")
    chart_caption(ai_insight(
        f"SMA {fast_window}/{slow_window} crossover on {strat_ticker}. "
        f"Strategy Sharpe {m_strat['sharpe']:.2f} vs buy-and-hold {m_bh['sharpe']:.2f}. "
        f"Strategy max drawdown {m_strat['max_dd']:.2%} vs B&H {m_bh['max_dd']:.2%}. "
        f"{num_trades} trades, {days_long/total_days:.0%} of time invested.",
        api_key) or
        f"The green shading shows periods when the strategy was long (invested). "
        f"The middle panel compares the strategy equity curve vs simply holding {strat_ticker} — "
        f"a Sharpe of {m_strat['sharpe']:.2f} vs {m_bh['sharpe']:.2f} means "
        f"{'better' if m_strat['sharpe'] > m_bh['sharpe'] else 'worse'} risk-adjusted returns with only {num_trades} trades over the period.")

    # ── Comparison table ───────────────────────────────────────────────────────
    st.markdown("<p class='section-label'>Head-to-head</p>", unsafe_allow_html=True)
    comp = pd.DataFrame({
        "Metric":     ["Ann. Return", "Ann. Vol", "Sharpe", "Max Drawdown"],
        "Buy & Hold": [f"{m_bh['ann_return']:.2%}", f"{m_bh['ann_vol']:.2%}",
                       f"{m_bh['sharpe']:.2f}", f"{m_bh['max_dd']:.2%}"],
        f"SMA {fast_window}/{slow_window}": [
                       f"{m_strat['ann_return']:.2%}", f"{m_strat['ann_vol']:.2%}",
                       f"{m_strat['sharpe']:.2f}", f"{m_strat['max_dd']:.2%}"],
        "Beat B&H?":  [
            "✓" if m_strat["ann_return"] > m_bh["ann_return"] else "✗",
            "✓" if m_strat["ann_vol"]    < m_bh["ann_vol"]    else "✗",
            "✓" if m_strat["sharpe"]     > m_bh["sharpe"]     else "✗",
            "✓" if m_strat["max_dd"]     > m_bh["max_dd"]     else "✗",
        ],
    }).set_index("Metric")
    st.dataframe(comp, width="stretch")

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(f"""
    <div style='font-family:JetBrains Mono;font-size:0.7rem;color:#3a4050;line-height:2;
                border-left:2px solid #1e2030;padding-left:1rem;'>
    signal: long when SMA{fast_window} &gt; SMA{slow_window} · shifted +1 bar (no look-ahead bias)<br>
    trades: {num_trades} · days invested: {days_long}/{total_days} ({days_long/total_days:.0%})<br>
    no transaction costs · no slippage · cash earns 0%
    </div>
    """, unsafe_allow_html=True)
    render_bottom_nav("Phase 2 — SMA Crossover")


# ════════════════════════════════════════════════════════════════════════════
#  PHASE 3 — RSI MEAN REVERSION
# ════════════════════════════════════════════════════════════════════════════
elif page == "Phase 3 — RSI Mean Reversion":

    st.markdown("<span class='phase-badge blue'>Phase 3</span>", unsafe_allow_html=True)
    st.markdown("## RSI Mean Reversion Strategy")
    st.markdown(f"<p class='section-label'>Mean reversion · buy the dip · {START} → {END}</p>", unsafe_allow_html=True)

    # ── 101 Explainer ──────────────────────────────────────────────────────────
    with st.expander("101 — What is RSI and mean reversion?", expanded=False):
        st.markdown("""
<div class='explainer-box'>
<h4>Mean reversion: the opposite of trend-following</h4>

Phase 2 assumed <i>trends persist</i>. Phase 3 assumes the opposite:
<b>prices that move too far from their average will snap back.</b>
This is called <b>mean reversion</b>.

Think of it like a rubber band — the further you stretch it, the harder it pulls back.
In markets: a stock that drops 15% in a week due to panic selling is probably oversold,
and buyers will step in to push it back up.

<br>

<b>The RSI indicator</b><br>
RSI (Relative Strength Index) measures <b>how fast and how much</b> a price has moved recently.
It gives a value between 0 and 100.
<span class='formula'>Step 1: avg_gain = average of up-days over last N days (default: 14)</span>
<span class='formula'>Step 2: avg_loss = average of down-days over last N days</span>
<span class='formula'>Step 3: RS = avg_gain / avg_loss</span>
<span class='formula'>Step 4: RSI = 100 − (100 / (1 + RS))</span>

Interpretation:
<span class='rule'><b class='bad'>RSI &lt; 30</b> → <b>Oversold</b>. The asset has fallen hard and fast. Mean reversion bet: buy, expecting a bounce.</span>
<span class='rule'><b class='good'>RSI &gt; 70</b> → <b>Overbought</b>. The asset has rallied hard and fast. Mean reversion exit: sell, expecting a pullback.</span>
<span class='rule'><b>RSI ~50</b> → Neutral. No strong signal.</span>

<br>

<b>The signal logic (stateful)</b><br>
Unlike the SMA crossover which re-evaluates every day, RSI creates a <b>stateful</b> position:
<span class='rule'>Enter long when RSI crosses <b>below 30</b> (oversold trigger).</span>
<span class='rule'>Stay long until RSI crosses <b>above 70</b> (overbought exit).</span>
<span class='rule'>Otherwise: hold current position.</span>
The position is still shifted +1 day to avoid look-ahead bias.

<br>

<b>Trend-following vs Mean Reversion — when does each work?</b><br>
<span class='rule'><b>Trend-following (SMA)</b>: wins in sustained directional markets (2020 recovery, 2022 crash).</span>
<span class='rule'><b>Mean reversion (RSI)</b>: wins in choppy, range-bound markets where dips recover quickly.</span>
They're <b>negatively correlated</b> — when one is losing, the other often profits.
This is exactly why Phase 5 (combining signals) is so powerful.

<br>

<b>Why is RSI period 14 the default?</b><br>
J. Welles Wilder, who invented RSI in 1978, found 14 days worked well empirically.
It's roughly 2–3 trading weeks — long enough to smooth noise, short enough to be responsive.
You can tune it — shorter (e.g. 7) = more sensitive, more trades; longer (e.g. 21) = fewer, smoother signals.

</div>
""", unsafe_allow_html=True)

    # ── Controls ───────────────────────────────────────────────────────────────
    col_t, col_a, col_b, col_c = st.columns([1, 1, 1, 1])
    with col_t:
        rsi_ticker = st.selectbox("Ticker", options=list(TICKER_OPTIONS.keys()), index=0, key="rsi_ticker")
    with col_a:
        rsi_period   = st.number_input("RSI Period", min_value=2, max_value=50, value=14, step=1)
    with col_b:
        oversold_lvl = st.number_input("Oversold (buy)", min_value=10, max_value=45, value=30, step=5)
    with col_c:
        overbought_lvl = st.number_input("Overbought (sell)", min_value=55, max_value=90, value=70, step=5)

    # ── Compute RSI ────────────────────────────────────────────────────────────
    with st.spinner("Computing…"):
        prices  = load_prices(rsi_ticker, START, END)
        delta   = prices.diff()
        gain    = delta.clip(lower=0)
        loss    = (-delta).clip(lower=0)
        avg_gain = gain.ewm(com=rsi_period - 1, min_periods=rsi_period).mean()
        avg_loss = loss.ewm(com=rsi_period - 1, min_periods=rsi_period).mean()
        rs      = avg_gain / avg_loss
        rsi     = 100 - (100 / (1 + rs))

        # Stateful signal: enter on oversold cross, exit on overbought cross
        position = pd.Series(np.nan, index=prices.index)
        current  = 0
        for i in range(len(rsi)):
            if np.isnan(rsi.iloc[i]):
                position.iloc[i] = 0
                continue
            if current == 0 and rsi.iloc[i] < oversold_lvl:
                current = 1
            elif current == 1 and rsi.iloc[i] > overbought_lvl:
                current = 0
            position.iloc[i] = current

        signal    = position.shift(1)
        log_ret   = np.log(prices / prices.shift(1))
        strat_ret = (log_ret * signal).dropna()
        bh_ret    = log_ret.loc[strat_ret.index]
        m_bh      = compute_metrics(bh_ret)
        m_strat   = compute_metrics(strat_ret)
        total_days = len(signal.dropna())
        days_long  = int(signal.sum())
        num_trades = int((signal.diff().abs() == 1).sum())

    # ── KPIs ───────────────────────────────────────────────────────────────────
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Sharpe",       f"{m_strat['sharpe']:.2f}",     f"{m_strat['sharpe']-m_bh['sharpe']:+.2f} vs B&H")
    c2.metric("Max Drawdown", f"{m_strat['max_dd']:.2%}",     f"{m_strat['max_dd']-m_bh['max_dd']:+.2%} vs B&H")
    c3.metric("Ann. Return",  f"{m_strat['ann_return']:.2%}", f"{m_strat['ann_return']-m_bh['ann_return']:+.2%} vs B&H")
    c4.metric("# Trades",     str(num_trades),                f"{days_long/total_days:.0%} time invested")

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Charts ─────────────────────────────────────────────────────────────────
    st.markdown("<p class='section-label'>RSI · price · equity curve · position</p>", unsafe_allow_html=True)

    fig = make_subplots(rows=4, cols=1, shared_xaxes=True,
                        row_heights=[0.15, 0.35, 0.35, 0.15],
                        vertical_spacing=0.02,
                        subplot_titles=("", "", "", ""))

    # Panel 1: RSI
    fig.add_trace(go.Scatter(x=rsi.index, y=rsi.values, name="RSI",
        line=dict(color="#b48ead", width=1.2),
        hovertemplate="RSI: %{y:.1f}<extra></extra>"), row=1, col=1)
    fig.add_hline(y=oversold_lvl,   line=dict(color="#00ff88", width=0.8, dash="dot"), row=1, col=1)
    fig.add_hline(y=overbought_lvl, line=dict(color="#ff4466", width=0.8, dash="dot"), row=1, col=1)
    fig.add_hline(y=50,             line=dict(color="#2a2d3a", width=0.6),              row=1, col=1)

    # RSI bands shading
    fig.add_trace(go.Scatter(
        x=rsi.index, y=rsi.where(rsi < oversold_lvl).values,
        fill="tozeroy", fillcolor="rgba(0,255,136,0.06)",
        line=dict(width=0), showlegend=False, hoverinfo="skip"), row=1, col=1)

    # Panel 2: Price
    fig.add_trace(go.Scatter(x=prices.index, y=prices.values, name="SPY",
        line=dict(color="#c8cdd6", width=1),
        hovertemplate="%{x|%Y-%m-%d}  $%{y:.2f}<extra></extra>"), row=2, col=1)
    sig_aligned   = signal.reindex(prices.index).fillna(0)
    shade_y_upper = prices.where(sig_aligned == 1)
    fig.add_trace(go.Scatter(x=prices.index, y=shade_y_upper.values,
        fill="tonexty", fillcolor="rgba(0,255,136,0.05)",
        line=dict(width=0), showlegend=False, hoverinfo="skip"), row=2, col=1)

    # Panel 3: Equity curves
    fig.add_trace(go.Scatter(x=m_bh["cumulative"].index, y=m_bh["cumulative"].values,
        name="Buy & Hold", line=dict(color="#5a6070", width=1.2),
        hovertemplate="B&H: $%{y:.3f}<extra></extra>"), row=3, col=1)
    fig.add_trace(go.Scatter(x=m_strat["cumulative"].index, y=m_strat["cumulative"].values,
        name="RSI Strategy", line=dict(color="#00b4ff", width=1.5),
        hovertemplate="RSI: $%{y:.3f}<extra></extra>"), row=3, col=1)

    # Panel 4: Position
    fig.add_trace(go.Scatter(x=sig_aligned.index, y=sig_aligned.values,
        name="Position", line=dict(color="#00b4ff", width=0.8),
        fill="tozeroy", fillcolor="rgba(0,180,255,0.08)",
        hovertemplate="Position: %{y}<extra></extra>"), row=4, col=1)

    fig.update_layout(**PLOTLY_THEME, height=720,
                      legend=dict(orientation="h", y=1.02, x=0, font=dict(size=10), bgcolor="rgba(0,0,0,0)"),
                      hovermode="x unified")
    fig.update_yaxes(gridcolor="#161820", title_text="RSI", row=1)
    fig.update_yaxes(gridcolor="#161820", title_text="Price", row=2)
    fig.update_yaxes(gridcolor="#161820", title_text="Growth $1", row=3)
    fig.update_yaxes(gridcolor="#161820", tickvals=[0, 1], ticktext=["Flat", "Long"], row=4)
    fig.update_xaxes(gridcolor="#161820")
    st.plotly_chart(fig, width="stretch")
    chart_caption(ai_insight(
        f"RSI({rsi_period}) mean reversion on {rsi_ticker}. Buy below {oversold_lvl}, sell above {overbought_lvl}. "
        f"Strategy Sharpe {m_strat['sharpe']:.2f}, max drawdown {m_strat['max_dd']:.2%}. "
        f"Buy-and-hold Sharpe {m_bh['sharpe']:.2f}, max drawdown {m_bh['max_dd']:.2%}. "
        f"{num_trades} trades, in market {days_long/total_days:.0%} of the time.",
        api_key) or
        f"The top panel shows RSI — when it dips below {oversold_lvl} (green band) the strategy enters long; "
        f"it exits when RSI exceeds {overbought_lvl}. "
        f"With {num_trades} trades and {days_long/total_days:.0%} time invested, the strategy achieved "
        f"Sharpe {m_strat['sharpe']:.2f} vs buy-and-hold's {m_bh['sharpe']:.2f}.")

    # ── Comparison table ───────────────────────────────────────────────────────
    st.markdown("<p class='section-label'>Head-to-head</p>", unsafe_allow_html=True)
    comp = pd.DataFrame({
        "Metric":     ["Ann. Return", "Ann. Vol", "Sharpe", "Max Drawdown"],
        "Buy & Hold": [f"{m_bh['ann_return']:.2%}", f"{m_bh['ann_vol']:.2%}",
                       f"{m_bh['sharpe']:.2f}", f"{m_bh['max_dd']:.2%}"],
        f"RSI({rsi_period}) {oversold_lvl}/{overbought_lvl}": [
                       f"{m_strat['ann_return']:.2%}", f"{m_strat['ann_vol']:.2%}",
                       f"{m_strat['sharpe']:.2f}", f"{m_strat['max_dd']:.2%}"],
        "Beat B&H?":  [
            "✓" if m_strat["ann_return"] > m_bh["ann_return"] else "✗",
            "✓" if m_strat["ann_vol"]    < m_bh["ann_vol"]    else "✗",
            "✓" if m_strat["sharpe"]     > m_bh["sharpe"]     else "✗",
            "✓" if m_strat["max_dd"]     > m_bh["max_dd"]     else "✗",
        ],
    }).set_index("Metric")
    st.dataframe(comp, width="stretch")

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(f"""
    <div style='font-family:JetBrains Mono;font-size:0.7rem;color:#3a4050;line-height:2;
                border-left:2px solid #1e2030;padding-left:1rem;'>
    signal: enter long when RSI({rsi_period}) &lt; {oversold_lvl} · exit when RSI &gt; {overbought_lvl} · shifted +1 bar<br>
    trades: {num_trades} · days invested: {days_long}/{total_days} ({days_long/total_days:.0%})<br>
    no transaction costs · no slippage · cash earns 0%
    </div>
    """, unsafe_allow_html=True)
    render_bottom_nav("Phase 3 — RSI Mean Reversion")


# ════════════════════════════════════════════════════════════════════════════
#  PHASE 4 — TRANSACTION COSTS
# ════════════════════════════════════════════════════════════════════════════
elif page == "Phase 4 — Transaction Costs":

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
elif page == "Phase 5 — Combining Signals":

    st.markdown("<span class='phase-badge' style='background:#b48ead'>Phase 5</span>", unsafe_allow_html=True)
    st.markdown("## Combining Signals")
    st.markdown(f"<p class='section-label'>Ensemble methods · SMA + RSI · {START} → {END}</p>", unsafe_allow_html=True)

    with st.expander("101 — Why combine signals?", expanded=False):
        st.markdown("""
<div class='explainer-box'>
<h4>Diversification applies to signals, not just assets</h4>

You've seen two very different strategies:
<span class='rule'><b>SMA crossover</b>: trend-following. Wins when markets trend strongly in one direction.</span>
<span class='rule'><b>RSI mean reversion</b>: buy the dip. Wins when markets oscillate around a range.</span>

These regimes alternate. Sometimes markets trend for months (2020 recovery, 2022 crash).
Other times they chop sideways for months (much of 2023). One strategy shines while the other suffers.

<b>The key insight</b>: if two strategies are <b>negatively correlated</b> — one wins when the other loses —
combining them produces a smoother, more consistent equity curve with a better Sharpe ratio.
This is the same math as portfolio diversification, applied to signals.

<br>

<b>Three ways to combine</b><br>
<span class='rule'><b>AND logic</b>: only go long when <i>both</i> signals agree. Very selective. Fewer trades, higher conviction.</span>
<span class='rule'><b>OR logic</b>: go long when <i>either</i> signal fires. More aggressive. More time invested.</span>
<span class='rule'><b>AVG (fractional)</b>: position = (SMA signal + RSI signal) / 2. Can be 0, 0.5, or 1. Continuous sizing.</span>

None is universally better — it depends on the regime. BUT the combined Sharpe is often
higher than either individual strategy, even if the combined return isn't the max.

<br>

<b>Signal correlation matters</b><br>
If two signals are perfectly correlated (always agree), combining them adds nothing.
If they're perfectly anti-correlated, the combined signal is flat and earns nothing.
The sweet spot is low-but-positive correlation — you get diversification without cancellation.

<br>

<b>This is the foundation of systematic multi-strategy funds</b><br>
Real quant funds (Two Sigma, Renaissance, D.E. Shaw) run hundreds of uncorrelated signals
and combine them. No single signal is amazing. The combination is robust.
The more uncorrelated signals you have, the more your Sharpe scales with √N.

</div>
""", unsafe_allow_html=True)

    # ── Controls ───────────────────────────────────────────────────────────────
    col_t, col_f, col_s, col_r, _ = st.columns([1, 1, 1, 1, 2])
    with col_t:
        comb_ticker  = st.selectbox("Ticker", options=list(TICKER_OPTIONS.keys()), index=0, key="comb_ticker")
    with col_f:
        fast_w = st.number_input("Fast SMA", min_value=5, max_value=100, value=50, step=5, key="c_fast")
    with col_s:
        slow_w = st.number_input("Slow SMA", min_value=20, max_value=400, value=200, step=10, key="c_slow")
    with col_r:
        rsi_p  = st.number_input("RSI Period", min_value=5, max_value=30, value=14, step=1, key="c_rsi")

    # ── Compute ────────────────────────────────────────────────────────────────
    with st.spinner("Computing…"):
        prices   = load_prices(comb_ticker, START, END)
        log_ret  = np.log(prices / prices.shift(1))

        sig_sma            = sma_signal(prices, fast_w, slow_w).reindex(prices.index).fillna(0)
        sig_rsi, _         = rsi_signal(prices, rsi_p, 30, 70)
        sig_rsi            = sig_rsi.reindex(prices.index).fillna(0)

        sig_and  = ((sig_sma == 1) & (sig_rsi == 1)).astype(float)
        sig_or   = ((sig_sma == 1) | (sig_rsi == 1)).astype(float)
        sig_avg  = (sig_sma + sig_rsi) / 2

        def ret_from_sig(sig):
            r = (log_ret * sig).dropna()
            return r, log_ret.loc[r.index]

        sma_ret,  bh_ret  = ret_from_sig(sig_sma)
        rsi_ret,  _       = ret_from_sig(sig_rsi)
        and_ret,  _       = ret_from_sig(sig_and)
        or_ret,   _       = ret_from_sig(sig_or)
        avg_ret,  _       = ret_from_sig(sig_avg)

        m_bh  = compute_metrics(bh_ret)
        m_sma = compute_metrics(sma_ret)
        m_rsi = compute_metrics(rsi_ret)
        m_and = compute_metrics(and_ret)
        m_or  = compute_metrics(or_ret)
        m_avg = compute_metrics(avg_ret)

        # Signal correlation
        common = sig_sma.dropna().index.intersection(sig_rsi.dropna().index)
        corr   = sig_sma.loc[common].corr(sig_rsi.loc[common])

        pct_long = {
            "SMA":  sig_sma.mean(), "RSI": sig_rsi.mean(),
            "AND":  sig_and.mean(), "OR":  sig_or.mean(), "AVG": sig_avg.mean(),
        }

    # ── KPIs ───────────────────────────────────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    cols = st.columns(6)
    for col, (name, m) in zip(cols, [("B&H", m_bh), ("SMA", m_sma), ("RSI", m_rsi),
                                      ("AND", m_and), ("OR", m_or),  ("AVG", m_avg)]):
        col.metric(f"Sharpe · {name}", f"{m['sharpe']:.2f}",
                   f"DD: {m['max_dd']:.1%}")

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(f"<p class='section-label'>Signal correlation: {corr:.2f} &nbsp;·&nbsp; "
                f"SMA long {pct_long['SMA']:.0%} · RSI long {pct_long['RSI']:.0%} · "
                f"AND long {pct_long['AND']:.0%} · OR long {pct_long['OR']:.0%}</p>",
                unsafe_allow_html=True)

    # ── Equity curves ─────────────────────────────────────────────────────────
    st.markdown("<p class='section-label'>Equity curves — all five strategies</p>", unsafe_allow_html=True)
    palette = {"B&H": "#5a6070", "SMA": "#00ff88", "RSI": "#00b4ff",
               "AND": "#f5c518", "OR": "#ff4466", "AVG": "#b48ead"}
    fig = go.Figure()
    for name, m in [("B&H", m_bh), ("SMA", m_sma), ("RSI", m_rsi),
                    ("AND", m_and), ("OR", m_or), ("AVG", m_avg)]:
        lw = 2 if name in ("AND", "OR", "AVG") else 1.2
        fig.add_trace(go.Scatter(x=m["cumulative"].index, y=m["cumulative"].values,
            name=name, line=dict(color=palette[name], width=lw),
            hovertemplate=f"{name}: $%{{y:.3f}}<extra></extra>"))
    fig.update_layout(**PLOTLY_THEME, height=400,
                      legend=dict(orientation="h", y=1.05, x=0, font=dict(size=10), bgcolor="rgba(0,0,0,0)"),
                      hovermode="x unified", yaxis_title="Growth of $1")
    st.plotly_chart(fig, width="stretch")
    best_combo = max([("AND",m_and),("OR",m_or),("AVG",m_avg)], key=lambda x: x[1]["sharpe"])
    chart_caption(ai_insight(
        f"Signal combination on {comb_ticker}. SMA Sharpe {m_sma['sharpe']:.2f}, RSI Sharpe {m_rsi['sharpe']:.2f}. "
        f"AND combo Sharpe {m_and['sharpe']:.2f}, OR combo {m_or['sharpe']:.2f}, AVG combo {m_avg['sharpe']:.2f}. "
        f"Signal correlation: {corr:.2f}.",
        api_key) or
        f"The {best_combo[0]} combination had the best Sharpe ({best_combo[1]['sharpe']:.2f}) by requiring {'both signals to agree' if best_combo[0]=='AND' else 'either signal' if best_combo[0]=='OR' else 'averaging both signals'}. "
        f"Signal correlation of {corr:.2f} means the two strategies {'often agree' if corr > 0.5 else 'frequently diverge' if corr < 0.2 else 'partially overlap'} — {'less diversification benefit' if corr > 0.5 else 'good diversification potential'}.")

    # ── Sharpe & drawdown bars ─────────────────────────────────────────────────
    st.markdown("<p class='section-label'>Sharpe and max drawdown comparison</p>", unsafe_allow_html=True)
    fig2 = make_subplots(rows=1, cols=2, subplot_titles=("Sharpe Ratio", "Max Drawdown"))
    names   = ["B&H", "SMA", "RSI", "AND", "OR", "AVG"]
    sharpes = [m_bh["sharpe"], m_sma["sharpe"], m_rsi["sharpe"],
               m_and["sharpe"], m_or["sharpe"], m_avg["sharpe"]]
    dds     = [m_bh["max_dd"], m_sma["max_dd"], m_rsi["max_dd"],
               m_and["max_dd"], m_or["max_dd"], m_avg["max_dd"]]
    clrs    = [palette[n] for n in names]
    fig2.add_trace(go.Bar(x=names, y=sharpes, marker_color=clrs,
                          text=[f"{s:.2f}" for s in sharpes], textposition="outside"), row=1, col=1)
    fig2.add_trace(go.Bar(x=names, y=dds, marker_color=clrs,
                          text=[f"{d:.1%}" for d in dds], textposition="outside"), row=1, col=2)
    fig2.update_layout(**PLOTLY_THEME, height=340, showlegend=False)
    fig2.update_yaxes(gridcolor="#161820", row=1, col=1)
    fig2.update_yaxes(gridcolor="#161820", tickformat=".0%", row=1, col=2)
    st.plotly_chart(fig2, width="stretch")
    chart_caption(ai_insight(
        f"Sharpe and max drawdown comparison for combined signals on {comb_ticker}. "
        f"Buy-and-hold Sharpe {m_bh['sharpe']:.2f}, SMA {m_sma['sharpe']:.2f}, RSI {m_rsi['sharpe']:.2f}, "
        f"AND {m_and['sharpe']:.2f}, OR {m_or['sharpe']:.2f}, AVG {m_avg['sharpe']:.2f}.",
        api_key) or
        f"The left bars compare return per unit of risk, while the right bars show worst peak-to-trough loss. "
        f"You want bars that are high on Sharpe and less negative on drawdown, which is why combinations can beat either signal alone.")

    # ── Full table ─────────────────────────────────────────────────────────────
    st.markdown("<p class='section-label'>Full metrics table</p>", unsafe_allow_html=True)
    rows_data = []
    for name, m in [("Buy & Hold", m_bh), ("SMA", m_sma), ("RSI", m_rsi),
                    ("AND (both)", m_and), ("OR (either)", m_or), ("AVG (fractional)", m_avg)]:
        rows_data.append({
            "Strategy":    name,
            "Ann. Return": f"{m['ann_return']:.2%}",
            "Ann. Vol":    f"{m['ann_vol']:.2%}",
            "Sharpe":      f"{m['sharpe']:.2f}",
            "Max DD":      f"{m['max_dd']:.2%}",
            "% Long":      f"{pct_long.get(name.split()[0], 1.0):.0%}",
        })
    st.dataframe(pd.DataFrame(rows_data).set_index("Strategy"), width="stretch")
    render_bottom_nav("Phase 5 — Combining Signals")


# ════════════════════════════════════════════════════════════════════════════
#  PHASE 6 — WALK-FORWARD VALIDATION
# ════════════════════════════════════════════════════════════════════════════
elif page == "Phase 6 — Walk-Forward Validation":

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
elif page == "Phase 7 — Position Sizing":

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
elif page == "Phase 8 — Portfolio Construction":

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
elif page == "Phase 9 — Risk Management":

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
elif page == "Phase 10 — Factor Models":

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
elif page == "Phase 11 — Statistical Rigor":

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
elif page == "Phase 12 — Market Microstructure":

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
elif page == "◆ Quant Algo Families":

    st.markdown("<span class='phase-badge' style='background:#26c6da;color:#0a0a0f'>Atlas</span>", unsafe_allow_html=True)
    st.markdown("## Major Quant Algorithm Families")
    st.markdown(f"<p class='section-label'>Strategy taxonomy · edge source · implementation tradeoffs · {START} → {END}</p>", unsafe_allow_html=True)

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
        {
            "Family": "Trend-Following",
            "Typical Holding": "Weeks to months",
            "Data": "Daily/weekly prices",
            "Edge Source": "Momentum persistence",
            "Turnover": 2,
            "Capacity": 5,
            "Complexity": 2,
            "Main Risk": "Whipsaw in sideways markets",
            "Examples": "SMA crossover, Donchian breakout, time-series momentum",
            "Best For": "Liquid futures, indices, macro portfolios",
            "Description": "Buy strength and cut when the trend breaks. Simple, robust, and scalable.",
        },
        {
            "Family": "Mean Reversion",
            "Typical Holding": "Days to weeks",
            "Data": "Prices, indicators, spreads",
            "Edge Source": "Short-term overshoot reversal",
            "Turnover": 4,
            "Capacity": 3,
            "Complexity": 3,
            "Main Risk": "Catching a falling knife in persistent trends",
            "Examples": "RSI reversion, Bollinger bands, short-horizon reversal",
            "Best For": "Range-bound markets and diversified baskets",
            "Description": "Fade sharp moves when price gets too far from a reference level.",
        },
        {
            "Family": "Cross-Sectional Momentum",
            "Typical Holding": "Weeks to months",
            "Data": "Relative returns across assets",
            "Edge Source": "Winners keep beating losers",
            "Turnover": 3,
            "Capacity": 4,
            "Complexity": 3,
            "Main Risk": "Violent momentum crashes during reversals",
            "Examples": "Rank-and-hold baskets, sector rotation, long-short momentum",
            "Best For": "Equities, futures, multi-asset universes",
            "Description": "Rank assets against each other instead of looking at one chart in isolation.",
        },
        {
            "Family": "Stat Arb",
            "Typical Holding": "Minutes to days",
            "Data": "Relative prices, residuals, baskets",
            "Edge Source": "Temporary mispricing convergence",
            "Turnover": 5,
            "Capacity": 2,
            "Complexity": 5,
            "Main Risk": "Relationships break and spreads do not converge",
            "Examples": "Pairs trading, basket residual trading, ETF vs constituents",
            "Best For": "Large universes with strong infrastructure",
            "Description": "Trade relative value rather than outright direction.",
        },
        {
            "Family": "Factor Investing",
            "Typical Holding": "Months to years",
            "Data": "Fundamentals, returns, quality/value metrics",
            "Edge Source": "Persistent risk premia",
            "Turnover": 1,
            "Capacity": 5,
            "Complexity": 3,
            "Main Risk": "Long multi-year drawdowns and crowding",
            "Examples": "Value, quality, low vol, size, momentum factors",
            "Best For": "Systematic portfolios with patient capital",
            "Description": "Systematically hold characteristics historically associated with excess return.",
        },
        {
            "Family": "Market Making",
            "Typical Holding": "Seconds to minutes",
            "Data": "Order book, trades, queue position",
            "Edge Source": "Earning spread while managing inventory",
            "Turnover": 5,
            "Capacity": 4,
            "Complexity": 5,
            "Main Risk": "Adverse selection and toxic flow",
            "Examples": "Two-sided quoting, ETF making, options market making",
            "Best For": "Firms with low latency and exchange connectivity",
            "Description": "Provide liquidity continuously and collect spread if inventory is controlled well.",
        },
        {
            "Family": "Volatility / Options",
            "Typical Holding": "Days to months",
            "Data": "Options chain, realized vol, skew, term structure",
            "Edge Source": "Mispricing of implied vs realized volatility",
            "Turnover": 3,
            "Capacity": 3,
            "Complexity": 5,
            "Main Risk": "Convex losses and model error",
            "Examples": "Short vol carry, dispersion, delta-hedged vol trades",
            "Best For": "Options desks with strong risk systems",
            "Description": "Trade the shape and price of volatility rather than just direction.",
        },
        {
            "Family": "ML / Forecasting",
            "Typical Holding": "Varies widely",
            "Data": "Prices, fundamentals, alt data, microstructure",
            "Edge Source": "Better prediction or better ranking",
            "Turnover": 3,
            "Capacity": 3,
            "Complexity": 5,
            "Main Risk": "Overfitting and unstable feature relationships",
            "Examples": "Return forecasting, execution models, regime classifiers",
            "Best For": "Research teams with good data discipline",
            "Description": "Usually an enhancement layer that improves signal quality or execution.",
        },
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
    display_df = family_df[[
        "Family", "Typical Holding", "Edge Source", "Main Risk", "Turnover", "Capacity", "Complexity"
    ]].copy()
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
