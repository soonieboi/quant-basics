# Quant Basics

Interactive Streamlit curriculum for learning quant trading from first principles.

## What this repo contains

- `dashboard.py`: Streamlit entrypoint, sidebar, routing
- `pages/`: page render modules
- `core/`: quant/data logic
- `ui/`: styles and reusable UI helpers
- `content/`: shared metadata and config
- `README.md`: project overview and run instructions
- `SKILL.md`: repo-local maintenance notes for future edits

The app currently includes:

- 12 numbered learning phases
- 1 separate atlas page: `◆ Quant Algo Families`
- sidebar navigation, home-page curriculum cards, and bottom next/previous navigation
- optional Anthropic-powered chart captions

## Run locally

From the repo root:

```bash
cd /Users/sherms/quant_basics
```

If you are using the local virtualenv, activate it first:

```bash
source venv/bin/activate
```

Then start the app:

```bash
streamlit run dashboard.py
```

If `streamlit` is not on your shell path, use:

```bash
./venv/bin/streamlit run dashboard.py
```

The app will usually open at `http://localhost:8501` unless that port is already in use.

## Product structure

The home page is intentionally split into three bands:

- `Learn the Path`: the 12-phase curriculum
- `Use in Real Trading`: workflow from research to deployment
- `Explore the Field`: strategy-family overview plus atlas link

The numbered phases are the curriculum. The atlas page is reference material, not part of the sequential path.

## Editing guidelines

- Keep the app as a Streamlit-first product unless there is a strong reason to split docs/frontend out later.
- Preserve the current page model:
  - numbered phases are sequential learning modules
  - `◆ Quant Algo Families` remains separate from the numbered curriculum
- Keep responsibility split by folder:
  - `dashboard.py` for app boot and route dispatch
  - `pages/` for page bodies
  - `ui/` for CSS and reusable render helpers
  - `core/` for strategies, metrics, data, and AI helpers
  - `content/` for shared metadata/constants
- When changing navigation, keep sidebar, home cards, query-param routing, and bottom nav in sync.
- When changing Plotly layouts, avoid passing duplicate `xaxis` / `yaxis` keys together with `PLOTLY_THEME`.

## Data / dependencies

Core libraries used by the app:

- `streamlit`
- `yfinance`
- `numpy`
- `pandas`
- `plotly`
- `scipy`
- `statsmodels`
- `anthropic`

Market data is loaded live from Yahoo Finance through `yfinance`.
