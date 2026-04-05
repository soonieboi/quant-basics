APP_CSS = """
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@300;400;500;700&display=swap');

.stApp, [data-testid="stSidebar"] {
    --qb-bg: transparent;
    --qb-surface: color-mix(in srgb, currentColor 3.5%, transparent);
    --qb-surface-alt: color-mix(in srgb, currentColor 6.5%, transparent);
    --qb-border: color-mix(in srgb, currentColor 14%, transparent);
    --qb-border-strong: color-mix(in srgb, currentColor 22%, transparent);
    --qb-text: currentColor;
    --qb-text-strong: currentColor;
    --qb-soft: color-mix(in srgb, currentColor 76%, transparent);
    --qb-muted: color-mix(in srgb, currentColor 60%, transparent);
    --qb-kicker: color-mix(in srgb, currentColor 46%, transparent);
    --qb-disabled: color-mix(in srgb, currentColor 28%, transparent);
    --qb-code-bg: color-mix(in srgb, currentColor 7%, transparent);
}

html, body, [class*="css"] {
    font-family: 'JetBrains Mono', monospace;
}
.stApp {
    background-image:
        radial-gradient(ellipse at 20% 50%, rgba(0,255,136,0.03) 0%, transparent 60%),
        radial-gradient(ellipse at 80% 20%, rgba(0,180,255,0.03) 0%, transparent 60%);
}
[data-testid="stSidebar"] {
    border-right: 1px solid var(--qb-border);
}
[data-testid="stSidebarNav"] {
    display: none;
}
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] div {
    color: var(--qb-muted);
}
[data-testid="stSidebar"] [role="radiogroup"] label {
    background: transparent !important;
    padding: 0.15rem 0 !important;
}
[data-testid="stSidebar"] [role="radiogroup"] label p {
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.88rem !important;
    line-height: 1.55 !important;
    color: var(--qb-text) !important;
}
[data-testid="metric-container"] {
    background-color: var(--qb-surface);
    border: 1px solid var(--qb-border);
    border-radius: 4px;
    padding: 1rem 1.2rem;
}
[data-testid="metric-container"] label {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.72rem !important;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    color: var(--qb-kicker) !important;
}
[data-testid="metric-container"] [data-testid="stMetricValue"] {
    font-family: 'JetBrains Mono', monospace;
    font-size: 1.4rem !important;
    font-weight: 500;
    color: var(--qb-text-strong) !important;
}
[data-testid="metric-container"] [data-testid="stMetricDelta"] {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.7rem !important;
}
h1, h2, h3 { font-family: 'JetBrains Mono', monospace !important; letter-spacing: -0.02em; }
h1 { color: var(--qb-text-strong) !important; font-weight: 700 !important; }
h2 { color: var(--qb-text) !important; font-weight: 500 !important; }
h3 { color: var(--qb-soft) !important; font-weight: 400 !important; }
hr { border-color: var(--qb-border) !important; }
.explainer-box {
    background: var(--qb-surface);
    border: 1px solid var(--qb-border);
    border-left: 3px solid #f5c518;
    border-radius: 4px;
    padding: 1.2rem 1.5rem;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.78rem;
    line-height: 1.9;
    color: var(--qb-soft);
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
.explainer-box b { color: var(--qb-text); }
.explainer-box code {
    background: var(--qb-code-bg);
    padding: 1px 6px;
    border-radius: 3px;
    font-size: 0.75rem;
    color: #00ff88;
}
.explainer-box .formula {
    display: block;
    background: var(--qb-code-bg);
    border: 1px solid var(--qb-border-strong);
    padding: 0.6rem 1rem;
    border-radius: 3px;
    margin: 0.6rem 0;
    color: #00b4ff;
    font-size: 0.8rem;
    letter-spacing: 0.03em;
}
.explainer-box .rule {
    display: block;
    border-left: 2px solid var(--qb-border-strong);
    padding-left: 0.8rem;
    margin: 0.4rem 0;
    color: var(--qb-soft);
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
    color: var(--qb-bg);
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
    border: 1px solid var(--qb-border-strong);
    border-radius: 2px;
    color: var(--qb-soft);
    margin-right: 6px;
}
.section-label {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.68rem;
    letter-spacing: 0.25em;
    text-transform: uppercase;
    color: var(--qb-kicker);
    margin-bottom: 0.75rem;
}
.phase-card-link {
    text-decoration: none !important;
    color: inherit !important;
    display: block;
}
.phase-card {
    background:var(--qb-surface);
    border:1px solid var(--qb-border);
    border-top-width:2px;
    border-radius:4px;
    padding:1.2rem 1.3rem 0.8rem 1.3rem;
    margin-bottom:0.75rem;
    transition:border-color 0.15s ease, transform 0.15s ease, background 0.15s ease;
}
.phase-card:hover {
    border-color:var(--qb-border-strong);
    background:var(--qb-surface-alt);
    transform:translateY(-1px);
}
.home-band {
    border: 1px solid var(--qb-border);
    border-radius: 6px;
    padding: 1.15rem 1.2rem 1.25rem 1.2rem;
    margin: 1.1rem 0 1.4rem 0;
    background:
        linear-gradient(180deg, rgba(255,255,255,0.015) 0%, rgba(255,255,255,0.0) 100%),
        var(--qb-surface);
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
    font-size: 0.7rem;
    letter-spacing: 0.22em;
    text-transform: uppercase;
    color: var(--qb-kicker);
    margin-bottom: 0.55rem;
}
.home-band-copy {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.8rem;
    line-height: 1.9;
    color: var(--qb-muted);
    max-width: 920px;
    margin-bottom: 1rem;
}
.bottom-nav {
    display: grid;
    grid-template-columns: 1fr 1.5fr 1fr;
    gap: 0.9rem;
    align-items: center;
    background: var(--qb-surface);
    border: 1px solid var(--qb-border);
    border-radius: 6px;
    padding: 0.9rem 1rem;
    margin-top: 1rem;
}
.bottom-nav-meta { text-align: center; }
.bottom-nav-kicker {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.64rem;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    color: var(--qb-kicker);
    margin-bottom: 0.2rem;
}
.bottom-nav-page {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.78rem;
    color: var(--qb-soft);
    line-height: 1.5;
}
.bottom-nav-link {
    display: block;
    text-decoration: none !important;
    border: 1px solid var(--qb-border-strong);
    border-radius: 4px;
    padding: 0.75rem 0.85rem;
    background: var(--qb-surface-alt);
    color: var(--qb-text) !important;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.76rem;
    letter-spacing: 0.04em;
    transition: border-color 0.15s ease, background 0.15s ease, transform 0.15s ease;
}
.bottom-nav-link:hover {
    border-color: var(--qb-kicker);
    background: var(--qb-surface);
    transform: translateY(-1px);
}
.bottom-nav-link.prev { text-align: left; }
.bottom-nav-link.next { text-align: right; }
.bottom-nav-link.disabled {
    color: var(--qb-disabled) !important;
    background: var(--qb-surface-alt);
    border-color: var(--qb-border);
    pointer-events: none;
}
"""

PLOTLY_THEME = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="JetBrains Mono", color="var(--qb-soft)", size=11),
    xaxis=dict(gridcolor="var(--qb-border)", zeroline=False, showline=False),
    yaxis=dict(gridcolor="var(--qb-border)", zeroline=False, showline=False),
    margin=dict(l=48, r=16, t=40, b=40),
)
