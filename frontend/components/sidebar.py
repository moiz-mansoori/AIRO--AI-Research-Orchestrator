"""
AIRO — frontend/components/sidebar.py
Shared sidebar navigation rendered on every page.
"""
import glob
import streamlit as st


def render_sidebar():
    """Render the AIRO sidebar with branding, nav links, and session stats."""
    exp_count = len(glob.glob("reports/*/leaderboard.csv"))

    with st.sidebar:
        st.markdown("""
        <div class="sidebar-brand">
            <div class="sidebar-brand-name">🔬 AIRO</div>
            <div class="sidebar-brand-sub">AI Research Orchestrator</div>
            <div class="sidebar-version">v0.1.0 · 2026</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("**Navigate**")
        st.page_link("app.py",                     label="🏠  Home")
        st.page_link("pages/1_run_experiment.py",   label="🚀  Run Experiment")
        st.page_link("pages/2_live_trace.py",       label="📡  Live Trace")
        st.page_link("pages/3_leaderboard.py",      label="🏆  Leaderboard")
        st.page_link("pages/4_report_viewer.py",    label="📄  Report Viewer")

        st.divider()

        st.markdown(f"""
        <div class="sidebar-stats">
            <div class="sidebar-stat-row">
                <span class="sidebar-stat-label">Experiments</span>
                <span class="sidebar-stat-value" style="color:#4f8ef7 !important;">{exp_count}</span>
            </div>
            <div class="sidebar-stat-row">
                <span class="sidebar-stat-label">Agents</span>
                <span class="sidebar-stat-value" style="color:#10b981 !important;">6</span>
            </div>
            <div class="sidebar-stat-row">
                <span class="sidebar-stat-label">LLM Provider</span>
                <span class="sidebar-stat-value" style="color:#f59e0b !important;">Groq</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
