from pages.phase_01_asset_metrics import render_phase_1 as render_phase_1_page
from pages.phase_02_sma_crossover import render_phase_2 as render_phase_2_page
from pages.phase_03_rsi_mean_reversion import render_phase_3 as render_phase_3_page
from pages.phase_04_transaction_costs import render_phase_4 as render_phase_4_page
from pages.phase_05_combining_signals import render_phase_5 as render_phase_5_page
from pages.phase_06_walk_forward_validation import render_phase_6 as render_phase_6_page
from pages.phase_07_position_sizing import render_phase_7 as render_phase_7_page
from pages.phase_08_portfolio_construction import render_phase_8 as render_phase_8_page
from pages.phase_09_risk_management import render_phase_9 as render_phase_9_page
from pages.phase_10_factor_models import render_phase_10 as render_phase_10_page
from pages.phase_11_statistical_rigor import render_phase_11 as render_phase_11_page
from pages.phase_12_market_microstructure import render_phase_12 as render_phase_12_page


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
    return render_phase_11_page(START, END, selected_tickers, api_key)

def render_phase_12(START, END, selected_tickers, api_key):
    return render_phase_12_page(START, END, selected_tickers, api_key)

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
