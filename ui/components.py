from urllib.parse import quote

import streamlit as st

from content.config import (
    ABOUT_ACCENT,
    CURRICULUM_ORDER,
    DISCLAIMER_ACCENT,
    HOME_ATLAS_ACCENT,
    HOME_PHASE_ACCENT,
    HOME_TRADE_ACCENT,
    PHASE_NAV,
)


def chart_caption(text: str):
    if text:
        st.markdown(f"""
<div style='font-family:JetBrains Mono;font-size:0.76rem;color:#8f98aa;line-height:1.8;
            border-left:2px solid var(--qb-border);padding:0.4rem 0.8rem;margin:0.2rem 0 1.2rem 0;'>
{text}
</div>""", unsafe_allow_html=True)


def render_page_header(badge_html: str, title: str, section_label: str):
    st.markdown(badge_html, unsafe_allow_html=True)
    st.markdown(f"## {title}")
    st.markdown(f"<p class='section-label'>{section_label}</p>", unsafe_allow_html=True)


def render_panel(title: str, body_html: str, accent: str, *, accent_position: str = "top", margin: str = "1rem 0"):
    accent_style = f"border-left:3px solid {accent};" if accent_position == "left" else f"border-top:2px solid {accent};"
    st.markdown(f"""
<div style='background:var(--qb-surface);border:1px solid var(--qb-border);{accent_style}
            border-radius:4px;padding:1rem 1.1rem;margin:{margin};'>
    <div style='font-family:JetBrains Mono;font-size:0.62rem;letter-spacing:0.18em;
                text-transform:uppercase;color:var(--qb-kicker);margin-bottom:0.45rem;'>
        {title}
    </div>
    <div style='font-family:JetBrains Mono;font-size:0.8rem;line-height:1.9;color:var(--qb-muted);'>
        {body_html}
    </div>
</div>
""", unsafe_allow_html=True)


def render_home_band(name: str, title: str, copy: str):
    st.markdown(f"""
<div class='home-band {name}'>
<div class='home-band-title'>{title}</div>
<div class='home-band-copy'>{copy}</div>
<div>
""", unsafe_allow_html=True)


def close_home_band():
    st.markdown("</div></div>", unsafe_allow_html=True)


def render_home_phase_card(phase: dict):
    concepts_html = "".join(
        f"<span style='display:inline-block;font-size:0.6rem;padding:1px 7px;"
        f"border:1px solid var(--qb-border);border-radius:2px;color:var(--qb-kicker);"
        f"margin:2px 3px 2px 0;font-family:JetBrains Mono;'>{concept}</span>"
        for concept in phase["concepts"]
    )
    nav_target = PHASE_NAV.get(phase["num"], "▲  Home")
    nav_href = f"?page={quote(nav_target)}"
    st.markdown(f"""
<a class='phase-card-link' href='{nav_href}'>
<div class='phase-card' style='border-top-color:{HOME_PHASE_ACCENT};'>
    <div style='display:flex;align-items:center;gap:0.6rem;margin-bottom:0.7rem;'>
        <span style='font-family:JetBrains Mono;font-size:1.4rem;font-weight:700;
                     color:{HOME_PHASE_ACCENT};line-height:1;'>{phase["num"]}</span>
        <span style='font-family:JetBrains Mono;font-size:0.55rem;letter-spacing:0.2em;
                     text-transform:uppercase;color:var(--qb-soft);background:var(--qb-surface-alt);
                     padding:2px 8px;border-radius:2px;'>{phase["tag"]}</span>
    </div>
    <div style='font-family:JetBrains Mono;font-size:0.95rem;font-weight:600;
                color:var(--qb-text);margin-bottom:0.6rem;letter-spacing:-0.01em;'>
        {phase["title"]}
    </div>
    <div style='font-family:JetBrains Mono;font-size:0.79rem;color:var(--qb-muted);
                line-height:1.7;margin-bottom:0.8rem;'>
        {phase["desc"]}
    </div>
    <div>{concepts_html}</div>
    <div style='font-family:JetBrains Mono;font-size:0.66rem;color:{HOME_PHASE_ACCENT};
                margin-top:0.9rem;letter-spacing:0.08em;text-transform:uppercase;'>
        Open Phase {phase["num"]} →
    </div>
</div>
</a>
""", unsafe_allow_html=True)


def render_home_info_card(title: str, desc: str, accent: str, *, accent_position: str = "top"):
    accent_style = f"border-left:3px solid {accent};" if accent_position == "left" else f"border-top:2px solid {accent};"
    st.markdown(f"""
<div style='background:var(--qb-surface);border:1px solid var(--qb-border);{accent_style}
            border-radius:4px;padding:1rem 1.1rem;margin-bottom:0.85rem;height:100%;'>
    <div style='font-family:JetBrains Mono;font-size:0.85rem;font-weight:600;
                color:var(--qb-text);margin-bottom:0.45rem;'>
        {title}
    </div>
    <div style='font-family:JetBrains Mono;font-size:0.78rem;line-height:1.8;color:var(--qb-muted);'>
        {desc}
    </div>
</div>
""", unsafe_allow_html=True)


def render_bottom_nav(current_page: str):
    if current_page not in CURRICULUM_ORDER:
        return
    idx = CURRICULUM_ORDER.index(current_page)
    prev_page = CURRICULUM_ORDER[idx - 1] if idx > 0 else None
    next_page = CURRICULUM_ORDER[idx + 1] if idx < len(CURRICULUM_ORDER) - 1 else None
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("<hr>", unsafe_allow_html=True)
    prev_label = "← Home" if prev_page == "▲  Home" else (f"← {prev_page.split(' — ', 1)[-1]}" if prev_page else "")
    if next_page == "◆ Quant Algo Families":
        next_label = "Atlas →"
    elif next_page == "◇ About the Writer":
        next_label = "About →"
    else:
        next_label = f"{next_page.split(' — ', 1)[-1]} →" if next_page else ""
    prev_href = f"?page={quote(prev_page)}" if prev_page else "#"
    next_href = f"?page={quote(next_page)}" if next_page else "#"
    prev_class = "bottom-nav-link prev" + ("" if prev_page else " disabled")
    next_class = "bottom-nav-link next" + ("" if next_page else " disabled")
    st.markdown(f"""
<div class='bottom-nav'>
    <a class='{prev_class}' href='{prev_href}'>{prev_label or "&nbsp;"}</a>
    <div class='bottom-nav-meta'>
        <div class='bottom-nav-kicker'>Navigation</div>
        <div class='bottom-nav-page'>{current_page}</div>
    </div>
    <a class='{next_class}' href='{next_href}'>{next_label or "&nbsp;"}</a>
</div>
""", unsafe_allow_html=True)
