"""
components/theme.py

Central place for FindBack AI's visual identity: one CSS injection plus a
handful of small render helpers (badges, score bars, status pills).

This module renders markup only - it never touches the database, the AI
providers, or business logic. That keeps it safe to import from any page
without creating circular imports or hidden side effects.
"""

from __future__ import annotations

import streamlit as st

# ---------------------------------------------------------------------------
# Design tokens
# ---------------------------------------------------------------------------

_PRIMARY = "#4F46E5"        # indigo-600
_PRIMARY_DARK = "#3730A3"
_BORDER = "#E2E8F0"
_SUCCESS_BG = "#DCFCE7"
_SUCCESS_TEXT = "#15803D"
_WARNING_BG = "#FEF3C7"
_WARNING_TEXT = "#B45309"
_DANGER_BG = "#FEE2E2"
_DANGER_TEXT = "#B91C1C"
_MUTED_BG = "#F1F5F9"
_MUTED_TEXT = "#475569"


def inject_css() -> None:
    """Inject the FindBack AI SaaS theme once per session.

    Safe to call on every page/render - Streamlit de-dupes identical
    <style> blocks visually, but we also guard with session_state so the
    (small) markdown call only runs once per session.
    """
    if st.session_state.get("_css_injected"):
        return
    st.session_state["_css_injected"] = True

    st.markdown(
        f"""
        <style>
        /* ---- Global type & spacing ---- */
        html, body, [class*="css"] {{
            font-family: -apple-system, "Segoe UI", Roboto, Inter, sans-serif;
        }}
        .block-container {{ padding-top: 2rem; }}

        /* ---- Card container ---- */
        .fb-card {{
            border: 1px solid {_BORDER};
            border-radius: 12px;
            padding: 1.1rem 1.3rem;
            margin-bottom: 0.9rem;
            background: #FFFFFF;
            box-shadow: 0 1px 3px rgba(15, 23, 42, 0.06);
        }}
        .fb-card:hover {{
            box-shadow: 0 4px 14px rgba(15, 23, 42, 0.09);
            transition: box-shadow 0.15s ease-in-out;
        }}

        /* ---- Pills / badges ---- */
        .fb-pill {{
            display: inline-block;
            padding: 0.18rem 0.75rem;
            border-radius: 999px;
            font-size: 0.80rem;
            font-weight: 600;
            letter-spacing: 0.01em;
        }}
        .fb-pill-strong  {{ background: {_SUCCESS_BG}; color: {_SUCCESS_TEXT}; }}
        .fb-pill-possible {{ background: {_WARNING_BG}; color: {_WARNING_TEXT}; }}
        .fb-pill-weak     {{ background: {_DANGER_BG}; color: {_DANGER_TEXT}; }}
        .fb-pill-muted    {{ background: {_MUTED_BG}; color: {_MUTED_TEXT}; }}

        /* ---- Score bar ---- */
        .fb-score-row {{ margin-bottom: 0.35rem; }}
        .fb-score-label {{
            font-size: 0.78rem;
            color: {_MUTED_TEXT};
            display: flex;
            justify-content: space-between;
            margin-bottom: 2px;
        }}
        .fb-score-track {{
            background: {_MUTED_BG};
            border-radius: 6px;
            height: 8px;
            width: 100%;
            overflow: hidden;
        }}
        .fb-score-fill {{
            height: 100%;
            border-radius: 6px;
            background: linear-gradient(90deg, {_PRIMARY}, {_PRIMARY_DARK});
        }}

        /* ==================== SIDEBAR ==================== */
        [data-testid="stSidebar"] {{
            background: linear-gradient(180deg, #FAFAFF 0%, #F5F5FC 100%);
            border-right: 1px solid {_BORDER};
            box-shadow: inset -1px 0 0 rgba(148, 163, 184, 0.12);
        }}
        [data-testid="stSidebar"] .block-container {{
            padding-top: 1.2rem;
            padding-left: 0.9rem;
            padding-right: 0.9rem;
        }}

        /* ---- Brand header ---- */
        .fb-brand-row {{
            display: flex;
            align-items: center;
            gap: 10px;
            margin-bottom: 0.3rem;
        }}
        .fb-brand-icon {{
            height: 38px; width: 38px;
            border-radius: 10px;
            background: linear-gradient(135deg, {_PRIMARY}, {_PRIMARY_DARK});
            display: flex; align-items: center; justify-content: center;
            font-size: 1.15rem;
            box-shadow: 0 2px 6px rgba(79, 70, 229, 0.35);
            flex-shrink: 0;
        }}
        .fb-brand-text {{ line-height: 1.15; }}
        .fb-brand-title {{
            font-size: 1.12rem;
            font-weight: 700;
            color: #1E1B4B;
        }}
        .fb-brand-subtitle {{
            font-size: 0.72rem;
            color: {_MUTED_TEXT};
            font-weight: 500;
            letter-spacing: 0.02em;
        }}

        /* ---- Navigation buttons (stable, single design from first render onward) ---- */
        [data-testid="stSidebar"] .stButton {{
            margin-bottom: 0.28rem;
        }}
        [data-testid="stSidebar"] .stButton > button {{
            width: 100%;
            justify-content: center;
            border-radius: 10px;
            border: 1px solid rgba(148, 163, 184, 0.30);
            background: rgba(255, 255, 255, 0.55);
            color: #334155;
            font-weight: 600;
            padding: 0.72rem 0.8rem;
            box-shadow: none;
            transition: all 0.14s ease-in-out;
        }}
        [data-testid="stSidebar"] .stButton > button:hover {{
            border-color: rgba(79, 70, 229, 0.25);
            background: rgba(79, 70, 229, 0.06);
            transform: translateY(-1px);
        }}
        [data-testid="stSidebar"] .stButton > button[kind="primary"] {{
            background: linear-gradient(90deg, {_PRIMARY}, {_PRIMARY_DARK});
            border-color: transparent;
            color: #FFFFFF;
            box-shadow: 0 8px 18px rgba(79, 70, 229, 0.18);
        }}
        [data-testid="stSidebar"] .stButton > button[kind="secondary"] {{
            background: rgba(255, 255, 255, 0.55);
            color: #334155;
        }}

        /* ---- Provider status chip ---- */
        .fb-status {{
            font-size: 0.80rem;
            font-weight: 500;
            display: flex;
            align-items: center;
            gap: 7px;
            padding: 0.4rem 0.7rem;
            border-radius: 8px;
            background: #FFFFFF;
            border: 1px solid {_BORDER};
        }}
        .fb-dot {{
            height: 8px; width: 8px; border-radius: 50%; display: inline-block;
            flex-shrink: 0;
        }}
        .fb-dot-on  {{ background: #22C55E; box-shadow: 0 0 0 3px rgba(34,197,94,0.15); }}
        .fb-dot-off {{ background: #CBD5E1; }}

        /* ---- Notification cards ---- */
        .fb-notif-unread {{
            border-left: 4px solid {_PRIMARY};
            background: #F8F8FF;
        }}
        .fb-notif-read {{
            border-left: 4px solid {_BORDER};
            opacity: 0.82;
        }}
        .fb-notif-title {{
            font-weight: 700;
            font-size: 0.96rem;
            color: #1E1B4B;
            margin-bottom: 0.25rem;
        }}
        .fb-notif-new-tag {{
            display: inline-block;
            margin-left: 0.4rem;
            font-size: 0.66rem;
            font-weight: 700;
            letter-spacing: 0.03em;
            color: {_PRIMARY_DARK};
            background: #E0E7FF;
            padding: 0.05rem 0.5rem;
            border-radius: 999px;
            vertical-align: middle;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def inject_login_css() -> None:
    """Inject the standalone, professional-looking login page theme.

    Kept separate from `inject_css()` so it never leaks into the main app
    shell - it hides Streamlit chrome (menu/footer/header) and narrows the
    layout to a centered auth card, which is only appropriate on the
    sign-in screen.
    """
    st.markdown(
        f"""
        <style>
        #MainMenu {{ visibility: hidden; }}
        footer {{ visibility: hidden; }}
        header {{ visibility: hidden; }}

        .stApp {{
            background: linear-gradient(180deg, #F7F8FB 0%, #EEF2F8 100%);
        }}
        .block-container {{
            max-width: 520px;
            padding-top: 3.2rem;
            padding-bottom: 2.5rem;
        }}

        .fb-login-shell {{
            width: min(100%, 480px);
            margin: 0 auto;
        }}

        .fb-login-logo {{
            height: 78px; width: 78px;
            border-radius: 22px;
            background: linear-gradient(135deg, {_PRIMARY}, {_PRIMARY_DARK});
            display: flex; align-items: center; justify-content: center;
            font-size: 2.2rem;
            margin: 0 auto 1.3rem auto;
            box-shadow: 0 18px 30px rgba(79, 70, 229, 0.22);
            border: 2px solid rgba(255,255,255,0.22);
        }}
        .fb-login-title {{
            text-align: center;
            font-size: clamp(2.2rem, 4vw, 3.1rem);
            line-height: 1.08;
            font-weight: 800;
            letter-spacing: -0.06em;
            color: #121826;
            margin-bottom: 0.4rem;
        }}
        .fb-login-subtitle {{
            text-align: center;
            font-size: 1.02rem;
            color: #5F6A7F;
            margin-bottom: 2rem;
            font-weight: 500;
        }}

        .fb-login-card {{
            background: transparent;
            border: none;
            border-radius: 0;
            padding: 0;
            box-shadow: none;
        }}
        .fb-login-heading {{
            font-size: clamp(2rem, 3vw, 2.7rem);
            line-height: 1.08;
            font-weight: 700;
            letter-spacing: -0.05em;
            color: #111827;
            margin: 0 0 1.3rem 0;
            text-align: left;
        }}

        .fb-login-card [data-testid="stForm"] {{
            background: transparent;
            border: none;
            padding: 0;
            margin: 0;
        }}
        .fb-login-card .stTextInput > div > div > input,
        .fb-login-card .stTextInput > div > div > div > input,
        .fb-login-card .stNumberInput > div > div > input {{
            border-radius: 12px;
            border: 1px solid #D9DEE8;
            background: #F3F5F8;
            padding: 0.85rem 0.9rem;
            color: #111827;
            font-size: 1.05rem;
            min-height: 54px;
            box-shadow: inset 0 1px 2px rgba(15, 23, 42, 0.04);
        }}
        .fb-login-card .stTextInput > label,
        .fb-login-card .stTextInput > div > label,
        .fb-login-card .stTextInput label,
        .fb-login-card .stTextInput p,
        .fb-login-card .stTextInput > div > label p {{
            font-size: 0.98rem;
            color: #435066;
            font-weight: 600;
            margin-bottom: 0.45rem;
        }}
        .fb-login-card .stTextInput > div > div:focus-within,
        .fb-login-card .stTextInput > div > div > input:focus {{
            border-color: rgba(79, 70, 229, 0.55) !important;
            box-shadow: 0 0 0 3px rgba(79, 70, 229, 0.12) !important;
        }}

        .fb-login-card .stButton > button {{
            width: 100%;
            min-height: 52px;
            border-radius: 12px;
            border: 1px solid rgba(17, 24, 39, 0.06);
            margin-top: 0.8rem;
            padding: 0.75rem 1rem;
            font-size: 1.08rem;
            font-weight: 700;
            color: #111827;
            background: #F3F4F6;
            box-shadow: 0 1px 1px rgba(15, 23, 42, 0.02);
            transition: transform 0.15s ease, box-shadow 0.15s ease, background 0.15s ease;
        }}
        .fb-login-card .stButton > button:hover {{
            transform: translateY(-1px);
            background: #EFF2F7;
            box-shadow: 0 10px 18px rgba(15, 23, 42, 0.08);
        }}

        .fb-login-demo {{
            margin-top: 1.7rem;
            padding: 1rem 1.1rem;
            background: #F3F4F6;
            border: 1px solid #E5E7EB;
            border-radius: 12px;
            font-size: 0.82rem;
            color: #475569;
            line-height: 1.7;
        }}
        .fb-login-demo-label {{
            color: #1F2937;
            font-size: 0.82rem;
            font-weight: 700;
            margin-bottom: 0.35rem;
        }}
        .fb-login-footer {{
            text-align: center;
            font-size: 0.8rem;
            color: #7B8797;
            margin-top: 1.5rem;
            padding-top: 0.1rem;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar_brand() -> None:
    """Render the FindBack AI logo mark + title/subtitle in the sidebar."""
    st.sidebar.markdown(
        """
        <div class="fb-brand-row">
            <div class="fb-brand-icon">🔍</div>
            <div class="fb-brand-text">
                <div class="fb-brand-title">FindBack AI</div>
                <div class="fb-brand-subtitle">Lost &amp; Found, matched by AI</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def match_badge_class(label: str) -> str:
    """Map a human match label to a CSS pill class."""
    mapping = {
        "Very Strong Match": "fb-pill-strong",
        "Strong Match": "fb-pill-strong",
        "Possible Match": "fb-pill-possible",
        "Weak Match": "fb-pill-weak",
        "Unlikely Match": "fb-pill-weak",
    }
    return mapping.get(label, "fb-pill-muted")


def render_match_badge(final_score: float, label: str) -> None:
    """Render a colored pill like '91% Strong Match'."""
    css_class = match_badge_class(label)
    st.markdown(
        f'<span class="fb-pill {css_class}">{final_score:.0f}% {label}</span>',
        unsafe_allow_html=True,
    )


def render_score_bar(name: str, value: float) -> None:
    """Render one labeled progress bar for a match-score component.

    `value` is expected in the 0..1 range (as produced by ai.matcher).
    """
    pct = max(0.0, min(1.0, float(value))) * 100
    st.markdown(
        f"""
        <div class="fb-score-row">
            <div class="fb-score-label"><span>{name}</span><span>{pct:.0f}%</span></div>
            <div class="fb-score-track"><div class="fb-score-fill" style="width:{pct:.0f}%"></div></div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_provider_status(connected: bool, provider_name: str) -> None:
    """Small 'Connected / Disconnected' indicator for the sidebar."""
    dot = "fb-dot-on" if connected else "fb-dot-off"
    text = f"{provider_name} connected" if connected else "No AI key configured"
    st.markdown(
        f'<div class="fb-status"><span class="fb-dot {dot}"></span>{text}</div>',
        unsafe_allow_html=True,
    )


def card_open() -> None:
    """Open a `.fb-card` div. Must be paired with `card_close()`."""
    st.markdown('<div class="fb-card">', unsafe_allow_html=True)


def card_close() -> None:
    st.markdown("</div>", unsafe_allow_html=True)


def notification_card_open(unread: bool) -> None:
    """Open a `.fb-card` div styled for a notification (unread vs read)."""
    cls = "fb-notif-unread" if unread else "fb-notif-read"
    st.markdown(f'<div class="fb-card {cls}">', unsafe_allow_html=True)


def render_notification_title(title: str, unread: bool) -> None:
    """Render a notification's title, with a small 'NEW' tag when unread."""
    tag = '<span class="fb-notif-new-tag">NEW</span>' if unread else ""
    st.markdown(f'<div class="fb-notif-title">{title}{tag}</div>', unsafe_allow_html=True)
