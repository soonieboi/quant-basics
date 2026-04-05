APP_CSS = """
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
.bottom-nav {
    display: grid;
    grid-template-columns: 1fr 1.5fr 1fr;
    gap: 0.9rem;
    align-items: center;
    background: #0d0d14;
    border: 1px solid #1e2030;
    border-radius: 6px;
    padding: 0.9rem 1rem;
    margin-top: 1rem;
}
.bottom-nav-meta { text-align: center; }
.bottom-nav-kicker {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.58rem;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    color: #3a4050;
    margin-bottom: 0.2rem;
}
.bottom-nav-page {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.72rem;
    color: #8a9ab0;
    line-height: 1.5;
}
.bottom-nav-link {
    display: block;
    text-decoration: none !important;
    border: 1px solid #2a2d3a;
    border-radius: 4px;
    padding: 0.75rem 0.85rem;
    background: #11131b;
    color: #c8cdd6 !important;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.7rem;
    letter-spacing: 0.04em;
    transition: border-color 0.15s ease, background 0.15s ease, transform 0.15s ease;
}
.bottom-nav-link:hover {
    border-color: #4a5060;
    background: #141826;
    transform: translateY(-1px);
}
.bottom-nav-link.prev { text-align: left; }
.bottom-nav-link.next { text-align: right; }
.bottom-nav-link.disabled {
    color: #3a4050 !important;
    background: #0f1118;
    border-color: #1a1d28;
    pointer-events: none;
}
"""

PLOTLY_THEME = dict(
    paper_bgcolor="#0a0a0f",
    plot_bgcolor="#0d0d14",
    font=dict(family="JetBrains Mono", color="#5a6070", size=11),
    xaxis=dict(gridcolor="#161820", zeroline=False, showline=False),
    yaxis=dict(gridcolor="#161820", zeroline=False, showline=False),
    margin=dict(l=48, r=16, t=40, b=40),
)

