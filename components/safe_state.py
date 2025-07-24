
import streamlit as st

def safe_get(key, default=None):
    """Safely get session state value"""
    try:
        return st.session_state.get(key, default)
    except AttributeError:
        return default

def safe_set(key, value):
    """Safely set session state value"""
    try:
        st.session_state[key] = value
    except Exception:
        pass
