import streamlit as st

from SDS.auth_api import login_to_qa


DEFAULT_PLATFORM = "3D热转印"
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"


def get_selected_platform():
    return st.session_state.get("selected_platform", DEFAULT_PLATFORM)


def get_qa_token():
    current_platform = get_selected_platform()
    token_cache = st.session_state.setdefault("qa_token_by_platform", {})
    qa_token = token_cache.get(current_platform)

    if not qa_token:
        qa_token = login_to_qa()
        if qa_token:
            token_cache[current_platform] = qa_token

    return qa_token


def get_qa_headers():
    return {
        "User-Agent": USER_AGENT,
        "Accept": "application/json, text/plain, */*",
        "access-token": get_qa_token(),
    }


def build_token_headers(token):
    return {
        "User-Agent": USER_AGENT,
        "Accept": "application/json, text/plain, */*",
        "access-token": token,
    }
