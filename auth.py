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
    st.set_page_config(page_title="FindBack AI", page_icon="🔍", layout="centered")
    st.title("FindBack AI")
    st.subheader("Sign in")
    with st.form("login_form", clear_on_submit=False):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login")

    if submitted:
        ok, error = login(username, password)
        if ok:
            st.rerun()
        else:
            st.error(error)

    st.caption("Demo accounts: admin / Admin@123, staff / Staff@123, user1 / User@123, user2 / User@123, user3 / User@123")
