PAGES = [
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
    "◇ About the Writer",
]

CURRICULUM_ORDER = PAGES

TICKER_OPTIONS = {
    "SPY": "#00ff88",
    "QQQ": "#00b4ff",
    "DIA": "#7ec8e3",
    "IWM": "#5a8a6a",
    "AAPL": "#f5c518",
    "MSFT": "#4fc3f7",
    "NVDA": "#76ff03",
    "GOOGL": "#ff7043",
    "AMZN": "#ffca28",
    "META": "#7986cb",
    "TSLA": "#ef5350",
    "BTC-USD": "#f7931a",
    "ETH-USD": "#627eea",
}

HOME_PHASE_ACCENT = "#f5c518"
HOME_ATLAS_ACCENT = "#26c6da"
HOME_TRADE_ACCENT = "#00ff88"
ABOUT_ACCENT = "#8a9ab0"
DISCLAIMER_ACCENT = "#d7a6ff"

PHASE_NAV = {
    "01": "Phase 1 — Asset Metrics",
    "02": "Phase 2 — SMA Crossover",
    "03": "Phase 3 — RSI Mean Reversion",
    "04": "Phase 4 — Transaction Costs",
    "05": "Phase 5 — Combining Signals",
    "06": "Phase 6 — Walk-Forward Validation",
    "07": "Phase 7 — Position Sizing",
    "08": "Phase 8 — Portfolio Construction",
    "09": "Phase 9 — Risk Management",
    "10": "Phase 10 — Factor Models",
    "11": "Phase 11 — Statistical Rigor",
    "12": "Phase 12 — Market Microstructure",
}

HOME_PHASES = [
    {
        "num": "01", "title": "Asset Metrics", "tag": "FOUNDATIONS",
        "desc": "Pull SPY, QQQ, BTC data via yfinance. Compute annualised return, volatility, Sharpe ratio, and max drawdown. Establish your baseline to beat.",
        "concepts": ["Log returns", "Sharpe ratio", "Max drawdown", "Annualisation"],
    },
    {
        "num": "02", "title": "SMA Crossover", "tag": "STRATEGY",
        "desc": "Build a trend-following strategy using golden cross / death cross signals. Introduces look-ahead bias — the most common backtest trap.",
        "concepts": ["Moving averages", "Trend-following", "Look-ahead bias", "Signal generation"],
    },
    {
        "num": "03", "title": "RSI Mean Reversion", "tag": "STRATEGY",
        "desc": "The opposite paradigm: buy oversold dips, sell overbought rallies. Learn why trend-following and mean reversion complement each other.",
        "concepts": ["RSI indicator", "Mean reversion", "Overbought/oversold", "Stateful signals"],
    },
    {
        "num": "04", "title": "Transaction Costs", "tag": "BACKTESTING",
        "desc": "Why strategies that look great on paper often fail in reality. Model bid-ask spread and slippage. See how trade frequency determines cost sensitivity.",
        "concepts": ["Basis points", "Bid-ask spread", "Slippage", "Cost-adjusted Sharpe"],
    },
    {
        "num": "05", "title": "Combining Signals", "tag": "BACKTESTING",
        "desc": "Run both SMA and RSI simultaneously. Combine them with AND, OR, and fractional averaging. Diversification of signals — not just assets.",
        "concepts": ["Signal ensembles", "AND/OR logic", "Fractional sizing", "Signal correlation"],
    },
    {
        "num": "06", "title": "Walk-Forward Validation", "tag": "BACKTESTING",
        "desc": "The honest test. Grid-search parameters in-sample, apply them out-of-sample. See the gap between fitted performance and real performance.",
        "concepts": ["Overfitting", "In-sample / OOS", "Parameter grid search", "Degradation ratio"],
    },
    {
        "num": "07", "title": "Position Sizing", "tag": "EXECUTION",
        "desc": "Right strategy, wrong bet size = blown account. Learn the Kelly criterion — the mathematically optimal fraction — and why half-Kelly is safer.",
        "concepts": ["Kelly criterion", "Fixed fractional", "Geometric growth", "Leverage limits"],
    },
    {
        "num": "08", "title": "Portfolio Construction", "tag": "PORTFOLIO",
        "desc": "Combine multiple assets optimally. Build the efficient frontier with 3,000 simulated portfolios. Find max Sharpe and minimum volatility allocations.",
        "concepts": ["Correlation matrix", "Efficient frontier", "Mean-variance optimisation", "Markowitz"],
    },
    {
        "num": "09", "title": "Risk Management", "tag": "PORTFOLIO",
        "desc": "Know when to stop. Model Value at Risk (VaR), Expected Shortfall, drawdown circuit breakers, and volatility-regime detection.",
        "concepts": ["VaR", "CVaR / Expected Shortfall", "Drawdown limits", "Regime detection"],
    },
    {
        "num": "10", "title": "Factor Models", "tag": "ADVANCED",
        "desc": "Decompose returns into alpha and beta. Measure true market-independent edge via CAPM regression. See rolling beta shift over time.",
        "concepts": ["CAPM", "Alpha", "Beta", "Rolling OLS regression"],
    },
    {
        "num": "11", "title": "Statistical Rigor", "tag": "ADVANCED",
        "desc": "A Sharpe of 0.8 is not a fact — it's an estimate with a confidence interval. Bootstrap your Sharpe, correct for multiple testing, compute minimum backtest length.",
        "concepts": ["Bootstrap CI", "Multiple testing", "Bonferroni correction", "Min backtest length"],
    },
    {
        "num": "12", "title": "Market Microstructure", "tag": "ADVANCED",
        "desc": "What actually happens when you click Buy. Order types, spread dynamics, intraday patterns, return autocorrelation, and seasonality.",
        "concepts": ["Order book", "Market vs limit orders", "Autocorrelation", "Seasonality"],
    },
]

WORKFLOW_STEPS = [
    ("01", "Research", "Pick markets with enough liquidity, acceptable drawdown, and behavior you can actually explain."),
    ("02", "Encode Rules", "Turn an idea into precise entry, exit, and sizing logic with no discretion hidden in the backtest."),
    ("03", "Reality Check", "Apply costs, out-of-sample testing, and statistical checks to see if the edge survives contact with reality."),
    ("04", "Deploy Small", "Trade tiny size first or paper trade, then compare live slippage and behavior against the historical model."),
    ("05", "Monitor", "Track drawdown, beta, regime shifts, and execution drift. If the live edge breaks, reduce or stop."),
]

ALGO_CARDS = [
    ("Trend-Following", "Ride persistent moves. SMA crossovers, breakout systems, time-series momentum."),
    ("Mean Reversion", "Bet that stretched prices snap back. RSI, z-score bands, pairs reversion."),
    ("Cross-Sectional Momentum", "Rank assets and own the relative winners while avoiding laggards."),
    ("Stat Arb", "Exploit short-lived pricing dislocations across related instruments or baskets."),
    ("Factor Investing", "Systematically target exposures like value, momentum, quality, and size."),
    ("Market Making", "Quote both sides of the market and earn spread while controlling inventory risk."),
    ("Volatility / Options", "Trade implied vs realized vol, skew, convexity, and hedging dynamics."),
    ("ML / Forecasting", "Use features and models to predict returns, risk, or execution quality."),
]
