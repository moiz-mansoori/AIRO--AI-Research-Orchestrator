"""AIRO — frontend/pages/2_live_trace.py"""
import streamlit as st
from pathlib import Path
from components.theme import inject_theme_css
from components.sidebar import render_sidebar

inject_theme_css()
render_sidebar()

st.markdown('<div class="page-title">📡 Live Agent Trace</div>', unsafe_allow_html=True)
st.markdown('<div class="page-desc">Real-time log viewer for the AIRO pipeline execution.</div>', unsafe_allow_html=True)

log_path = Path("logs/experiment.log")

if not log_path.exists():
    alt_log = Path("logs/airo.log")
    if alt_log.exists():
        log_path = alt_log

if log_path.exists():
    logs = log_path.read_text(encoding="utf-8").strip().split("\n")
    n_lines = st.slider("Lines to display", 50, 500, 200)
    st.code("\n".join(logs[-n_lines:]), language="text")
    if st.button("🔄 Refresh"):
        st.rerun()
else:
    st.info("No experiment logs found yet. Run an experiment first.")
    st.caption(f"Looking for: `{log_path}`")
