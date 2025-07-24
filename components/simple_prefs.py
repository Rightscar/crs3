
import streamlit as st

def save_pref(key, value):
    """Save preference (session only for now)"""
    st.session_state[f'pref_{key}'] = value

def get_pref(key, default=None):
    """Get preference"""
    return st.session_state.get(f'pref_{key}', default)
