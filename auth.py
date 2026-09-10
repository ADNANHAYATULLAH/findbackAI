from __future__ import annotations

import streamlit as st

from database.queries import get_user_by_username
from utils.security import verify_password

DEFAULT_USERS = {
    "admin": {"username": "admin", "password": "Admin@123", "role": "Administrator", "full_name": "System Administrator"},
    "staff": {"username": "staff", "password": "Staff@123", "role": "Staff", "full_name": "Operations Staff"},
    "user1": {"username": "user1", "password": "User@123", "role": "Regular User", "full_name": "Regular User 1"},
    "user2": {"username": "user2", "password": "User@123", "role": "Regular User", "full_name": "Regular User 2"},
    "user3": {"username": "user3", "password": "User@123", "role": "Regular User", "full_name": "Regular User 3"},
}


def is_authenticated() -> bool:
    return bool(st.session_state.get("authenticated_user"))


def get_current_user() -> dict | None:
    return st.session_state.get("authenticated_user")


def get_current_role() -> str:
    return get_current_user().get("role", "Regular User") if get_current_user() else "" 


def has_permission(permission: str) -> bool:
    role = get_current_role()
    if permission == "admin":
        return role == "Administrator"
    if permission == "staff":
        return role in {"Administrator", "Staff"}
    if permission == "user":
        return role in {"Administrator", "Staff", "Regular User"}
    return False


def login(username: str, password: str) -> tuple[bool, str | None]:
    user = get_user_by_username(username.strip())
    if not user:
        return False, "Invalid username or password."
    if not verify_password(password, user["password_hash"]):
        return False, "Invalid username or password."

    st.session_state["authenticated_user"] = {
        "id": user["id"],
        "username": user["username"],
        "full_name": user["full_name"],
        "role": user["role"],
    }
    st.session_state["auth_error"] = ""
    st.session_state["nav"] = "Home"
    return True, None


def logout() -> None:
    for key in [
        "authenticated_user",
        "auth_error",
        "nav",
        "selected_match",
        "match_results",
        "match_lost_item",
    ]:
        st.session_state.pop(key, None)
    st.session_state["nav"] = "Home"


def require_auth() -> None:
    if not is_authenticated():
        st.session_state["auth_required"] = True
        st.switch_page("app.py")


def render_login_screen() -> None:
    # NOTE: st.set_page_config() is already called once in app.py before this
    # runs (Streamlit allows only a single call per script run), so this
    # screen relies on components.theme.inject_login_css() to restyle the
    # page into a centered auth card instead of calling it again here.
    from components.theme import inject_login_css

    inject_login_css()

    st.markdown('<div class="fb-login-shell">', unsafe_allow_html=True)
    st.markdown('<div class="fb-login-logo">🔍</div>', unsafe_allow_html=True)
    st.markdown('<div class="fb-login-title">FindBack AI</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="fb-login-subtitle">AI-powered lost &amp; found for your campus</div>',
        unsafe_allow_html=True,
    )

    st.markdown('<div class="fb-login-card">', unsafe_allow_html=True)
    st.markdown('<div class="fb-login-heading">Sign in to your account</div>', unsafe_allow_html=True)
    with st.form("login_form", clear_on_submit=False):
        username = st.text_input("Username", placeholder="e.g. user1")
        password = st.text_input("Password", type="password", placeholder="••••••••")
        submitted = st.form_submit_button("Sign In")

    if submitted:
        ok, error = login(username, password)
        if ok:
            st.rerun()
        else:
            st.error(error)

    st.markdown(
        """
        <div class="fb-login-demo">
        <div class="fb-login-demo-label">Demo accounts</div>
        admin / Admin@123 &nbsp;·&nbsp; staff / Staff@123<br>
        user1 / User@123 &nbsp;·&nbsp; user2 / User@123 &nbsp;·&nbsp; user3 / User@123
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown(
        '<div class="fb-login-footer">Semantic + visual + context matching, verified by staff.</div>',
        unsafe_allow_html=True,
    )
    st.markdown("</div>", unsafe_allow_html=True)
