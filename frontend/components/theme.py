"""
AIRO — frontend/components/theme.py
Shared CSS theme injection for all pages.
"""
import streamlit as st


def inject_theme_css():
    """Inject the AIRO dark theme CSS into the current page."""
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

        html, body, [class*="css"] { font-family: 'Space Grotesk', sans-serif; }

        .main .block-container { padding: 2rem 2.5rem 3rem; max-width: 1100px; }

        #MainMenu, footer, header { visibility: hidden; }
        [data-testid="stDecoration"] { display: none; }

        [data-testid="stSidebar"] {
            background: #0d0f14 !important;
            border-right: 1px solid #1e2330;
            padding-bottom: 20px;
        }
        [data-testid="stSidebar"] * { color: #c9cdd8 !important; }

        [data-testid="stSidebarNavLink"] {
            border-radius: 8px;
            margin: 2px 8px;
            padding: 10px 14px !important;
            transition: background 0.2s;
        }
        [data-testid="stSidebarNavLink"]:hover { background: #1a1f2e !important; }
        [data-testid="stSidebarNavLink"][aria-current="page"] {
            background: #1a2740 !important;
            border-left: 3px solid #4f8ef7;
        }

        .sidebar-brand { padding: 20px 16px 16px; border-bottom: 1px solid #1e2330; }
        .sidebar-brand-name { font-size: 18px; font-weight: 700; color: #e8eaf0 !important; }
        .sidebar-brand-sub {
            font-size: 11px; color: #3a4460 !important;
            font-family: 'JetBrains Mono', monospace;
        }
        .sidebar-version {
            font-size: 10px; color: #2e3650 !important;
            font-family: 'JetBrains Mono', monospace; margin-top: 12px;
        }

        .sidebar-stats { margin-top: 12px; }
        .sidebar-stat-row {
            display: flex; justify-content: space-between; align-items: center;
            padding: 6px 0; font-size: 12px;
        }
        .sidebar-stat-label { color: #4a5270 !important; }
        .sidebar-stat-value { font-family: 'JetBrains Mono', monospace; font-weight: 500; }

        /* Page title styling */
        .page-title {
            font-size: 24px; font-weight: 700; color: #e8eaf0;
            margin-bottom: 4px;
        }
        .page-desc {
            font-size: 14px; color: #5a6480; margin-bottom: 24px;
        }
    </style>
    """, unsafe_allow_html=True)
