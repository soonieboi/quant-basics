---
name: quant-basics-repo
description: Use when modifying the Quant Basics Streamlit app in this repository. Covers page structure, navigation conventions, and safe editing rules for dashboard.py.
---

# Quant Basics Repo

This repo is a single-app Streamlit project. The maintained entrypoint is `dashboard.py`.

## Core workflow

1. Treat `dashboard.py` as the source of truth.
2. Preserve the distinction between:
   - numbered curriculum phases
   - `◆ Quant Algo Families` atlas page
3. Keep navigation consistent across:
   - sidebar radio
   - query param `page`
   - home-page cards
   - bottom next/previous navigation
4. After edits, run:

```bash
python -m py_compile dashboard.py
```

## App structure

- Top of file:
  - imports
  - CSS/theme
  - shared helpers
- Mid file:
  - sidebar and page-routing setup
  - home page
- Lower file:
  - phase pages in numeric order
  - atlas page at the end

## Navigation rules

- `page` is controlled by query params and synced into session state before the sidebar radio is created.
- Do not assign to `st.session_state["page"]` after the radio widget with key `page` exists.
- For button-based navigation after widget creation, update `st.query_params["page"]` and rerun.

## Plotly rules

- `PLOTLY_THEME` already defines `xaxis` and `yaxis`.
- Do not pass duplicate `xaxis=` or `yaxis=` into `update_layout(**PLOTLY_THEME, ...)`.
- Prefer `update_xaxes(...)` / `update_yaxes(...)` for per-chart overrides.

## Home page rules

The home page has three deliberate bands:

- `Learn the Path`
- `Use in Real Trading`
- `Explore the Field`

Keep the first visible actionable section focused on the 12 curriculum phases.

## Content rules

- Numbered phases are curriculum steps.
- The atlas is reference material and should not be renamed into a numbered phase again unless the product structure changes deliberately.
- If adding a new curriculum phase, update:
  - sidebar page list
  - `PAGES`
  - `PHASES`
  - `PHASE_NAV`
  - `CURRICULUM_ORDER`
  - bottom-nav coverage

## Cleanup rules

- Remove obsolete one-off scripts instead of maintaining parallel prototypes.
- Keep top-level repo files minimal and focused.
