import os
import sys
import glob
import streamlit as st
from pathlib import Path
from dotenv import load_dotenv

project_root = str(Path(__file__).parent.parent)
sys.path.insert(0, project_root)
os.chdir(project_root)
load_dotenv()

st.set_page_config(
    page_title="AIRO — AI Research Orchestrator",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
    /* ── A. Google Fonts ── */
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

    /* ── B. Base font ── */
    html, body, [class*="css"] {
        font-family: 'Space Grotesk', sans-serif;
    }

    /* ── C. Main container ── */
    .main .block-container {
        padding: 2rem 2.5rem 3rem;
        max-width: 1100px;
    }

    /* ── D. Hide Streamlit branding ── */
    #MainMenu, footer, header { visibility: hidden; }
    [data-testid="stDecoration"] { display: none; }

    /* ── E. Sidebar base ── */
    [data-testid="stSidebar"] {
        background: #0d0f14 !important;
        border-right: 1px solid #1e2330;
        padding-bottom: 20px;
    }
    [data-testid="stSidebar"] * { color: #c9cdd8 !important; }

    /* ── F. Sidebar nav links ── */
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

    /* ── G. Metric card grid ── */
    .metric-grid {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 16px;
        margin: 24px 0;
    }
    .metric-card {
        background: #10131a;
        border: 1px solid #1e2330;
        border-radius: 12px;
        padding: 20px 24px;
        position: relative;
        overflow: hidden;
        transition: border-color 0.2s, transform 0.2s;
    }
    .metric-card:hover { border-color: #2e3650; transform: translateY(-2px); }
    .metric-card::before {
        content: '';
        position: absolute;
        top: 0; left: 0; right: 0;
        height: 3px;
    }
    .metric-card.blue::before  { background: linear-gradient(90deg, #4f8ef7, #6c63ff); }
    .metric-card.teal::before  { background: linear-gradient(90deg, #10b981, #06b6d4); }
    .metric-card.amber::before { background: linear-gradient(90deg, #f59e0b, #ef4444); }
    .metric-label {
        font-size: 11px; font-weight: 600;
        letter-spacing: 0.1em; text-transform: uppercase;
        color: #5a6480; margin-bottom: 8px;
    }
    .metric-value { font-size: 28px; font-weight: 700; color: #e8eaf0; }
    .metric-sub { font-size: 12px; color: #4a5270; font-family: 'JetBrains Mono', monospace; }

    /* ── H. Hero section ── */
    .hero-section {
        background: linear-gradient(135deg, #0d1117 0%, #10131a 50%, #0d1520 100%);
        border: 1px solid #1e2330;
        border-radius: 16px;
        padding: 32px 36px;
        margin-bottom: 8px;
        position: relative;
        overflow: hidden;
    }
    .hero-section::after {
        content: '';
        position: absolute; top: -60px; right: -60px;
        width: 200px; height: 200px;
        background: radial-gradient(circle, rgba(79,142,247,0.08) 0%, transparent 70%);
        pointer-events: none;
    }
    .hero-title { font-size: 28px; font-weight: 700; color: #e8eaf0; margin: 0 0 8px 0; }
    .hero-badge {
        font-size: 10px; font-weight: 600;
        letter-spacing: 0.08em; text-transform: uppercase;
        background: #1a2740; color: #4f8ef7;
        border: 1px solid #2a3f6a; border-radius: 20px;
        padding: 3px 10px;
    }
    .hero-desc { font-size: 14px; color: #5a6480; line-height: 1.7; max-width: 620px; }

    /* ── I. CTA banner ── */
    .cta-banner {
        background: linear-gradient(90deg, #0f1e35, #0d1520);
        border: 1px solid #1e3a5f;
        border-left: 4px solid #4f8ef7;
        border-radius: 10px;
        padding: 16px 20px; margin: 20px 0;
    }
    .cta-banner-text { font-size: 13px; color: #8aa8d4; }
    .cta-banner-text strong { color: #4f8ef7; }

    /* ── J. Section headers ── */
    .section-header {
        display: flex; align-items: center; gap: 10px;
        margin: 28px 0 16px;
    }
    .section-header-icon {
        width: 32px; height: 32px;
        background: #1a1f2e; border-radius: 8px;
        display: flex; align-items: center; justify-content: center;
        font-size: 14px;
    }
    .section-header-title { font-size: 16px; font-weight: 600; color: #c9cdd8; }
    .section-header-line { flex: 1; height: 1px; background: #1e2330; }

    /* ── K. Experiment cards ── */
    .exp-card {
        background: #10131a; border: 1px solid #1e2330;
        border-radius: 10px; padding: 16px 20px; margin-bottom: 10px;
        display: flex; align-items: center; justify-content: space-between;
        transition: border-color 0.2s, background 0.2s;
    }
    .exp-card:hover { border-color: #2e3650; background: #12151d; }
    .exp-id {
        font-family: 'JetBrains Mono', monospace;
        font-size: 13px; color: #4f8ef7; font-weight: 500;
    }
    .exp-meta { font-size: 11px; color: #4a5270; margin-top: 3px; }
    .exp-tag {
        font-size: 10px; font-weight: 600;
        letter-spacing: 0.06em; text-transform: uppercase;
        background: #1a2740; color: #4f8ef7;
        border: 1px solid #2a3f6a; border-radius: 6px;
        padding: 4px 10px;
    }

    /* ── L. Pipeline strip ── */
    .pipeline { display: flex; align-items: center; gap: 0; margin: 16px 0; overflow-x: auto; }
    .pipeline-step {
        background: #10131a; border: 1px solid #1e2330;
        border-radius: 8px; padding: 10px 16px;
        text-align: center; min-width: 90px;
    }
    .pipeline-step-num { font-size: 10px; color: #4a5270; font-family: 'JetBrains Mono', monospace; }
    .pipeline-step-name { font-size: 12px; font-weight: 600; color: #c9cdd8; }
    .pipeline-step-role { font-size: 10px; color: #4a5270; margin-top: 2px; }
    .pipeline-arrow { color: #2e3650; font-size: 18px; padding: 0 4px; }

    /* ── M. Status dot animation ── */
    .status-dot {
        display: inline-block; width: 7px; height: 7px;
        border-radius: 50%; background: #10b981;
        margin-right: 6px; box-shadow: 0 0 6px #10b981;
        animation: pulse 2s infinite;
    }
    @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.5; } }

    /* ── Sidebar brand ── */
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

    /* ── Sidebar stats ── */
    .sidebar-stats { margin-top: 12px; }
    .sidebar-stat-row {
        display: flex; justify-content: space-between; align-items: center;
        padding: 6px 0; font-size: 12px;
    }
    .sidebar-stat-label { color: #4a5270 !important; }
    .sidebar-stat-value { font-family: 'JetBrains Mono', monospace; font-weight: 500; }
</style>
""", unsafe_allow_html=True)


# Sidebar (shared component)
from components.sidebar import render_sidebar
render_sidebar()


# Hero section
st.markdown("""
<div class="hero-section">
    <div class="hero-title">
        AIRO — AI Research Orchestrator
        <span class="hero-badge">Multi-Agent</span>
    </div>
    <p class="hero-desc">
        Upload a dataset, configure your experiment, and AIRO's six
        specialized agents handle everything — from data cleaning and
        parallel model training to a full PDF report with SHAP explainability.
    </p>
</div>
""", unsafe_allow_html=True)


# Metric cards
st.markdown("""
<div class="metric-grid">
    <div class="metric-card blue">
        <div class="metric-label">Specialized Agents</div>
        <div class="metric-value">6</div>
        <div class="metric-sub">Data · Config · Train · Critic · Eval · Report</div>
    </div>
    <div class="metric-card teal">
        <div class="metric-label">Parallel Training</div>
        <div class="metric-value">✓</div>
        <div class="metric-sub">concurrent.futures ThreadPool</div>
    </div>
    <div class="metric-card amber">
        <div class="metric-label">Experiment Tracking</div>
        <div class="metric-value">MLflow</div>
        <div class="metric-sub">SQLite · Full run provenance</div>
    </div>
</div>
""", unsafe_allow_html=True)


# CTA Banner
st.markdown("""
<div class="cta-banner">
    <div class="cta-banner-text">
        👈 Use the sidebar to navigate. Start with <strong>Run Experiment</strong> to launch your first pipeline.
    </div>
</div>
""", unsafe_allow_html=True)


# Agent pipeline strip
st.markdown("""
<div class="section-header">
    <div class="section-header-icon">⚙️</div>
    <div class="section-header-title">Agent Pipeline</div>
    <div class="section-header-line"></div>
</div>
<div class="pipeline">
    <div class="pipeline-step">
        <div class="pipeline-step-num">01</div>
        <div class="pipeline-step-name">Data</div>
        <div class="pipeline-step-role">Clean & Split</div>
    </div>
    <div class="pipeline-arrow">›</div>
    <div class="pipeline-step">
        <div class="pipeline-step-num">02</div>
        <div class="pipeline-step-name">Config</div>
        <div class="pipeline-step-role">LLM Configs</div>
    </div>
    <div class="pipeline-arrow">›</div>
    <div class="pipeline-step">
        <div class="pipeline-step-num">03</div>
        <div class="pipeline-step-name">Train</div>
        <div class="pipeline-step-role">Parallel Fit</div>
    </div>
    <div class="pipeline-arrow">›</div>
    <div class="pipeline-step">
        <div class="pipeline-step-num">04</div>
        <div class="pipeline-step-name">Critic</div>
        <div class="pipeline-step-role">Audit Models</div>
    </div>
    <div class="pipeline-arrow">›</div>
    <div class="pipeline-step">
        <div class="pipeline-step-num">05</div>
        <div class="pipeline-step-name">Evaluator</div>
        <div class="pipeline-step-role">Rank & Select</div>
    </div>
    <div class="pipeline-arrow">›</div>
    <div class="pipeline-step">
        <div class="pipeline-step-num">06</div>
        <div class="pipeline-step-name">Reporter</div>
        <div class="pipeline-step-role">PDF Report</div>
    </div>
</div>
""", unsafe_allow_html=True)


# Recent Experiments section
st.markdown("""
<div class="section-header">
    <div class="section-header-icon">📊</div>
    <div class="section-header-title">Recent Experiments</div>
    <div class="section-header-line"></div>
</div>
""", unsafe_allow_html=True)

import pandas as pd
report_dirs = sorted(glob.glob("reports/*/leaderboard.csv"), reverse=True)

if not report_dirs:
    st.markdown("""
    <div style="background:#10131a; border:1px dashed #1e2330;
                border-radius:10px; padding:32px; text-align:center;">
        <div style="font-size:32px; margin-bottom:8px;">🔬</div>
        <div style="font-size:14px; color:#5a6480; font-weight:500;">
            No experiments yet
        </div>
        <div style="font-size:12px; color:#3a4460; margin-top:4px;">
            Go to <span style="color:#4f8ef7;">Run Experiment</span> to get started
        </div>
    </div>
    """, unsafe_allow_html=True)
else:
    for csv_path in report_dirs[:5]:
        exp_id = Path(csv_path).parent.name
        md_path = Path(csv_path).parent / "airo_report.md"

        # Read best model and metric from leaderboard CSV
        best_model = "—"
        best_metric = "—"
        try:
            df = pd.read_csv(csv_path)
            if not df.empty:
                top = df.iloc[0]
                best_model = str(top.get("model_type", "—"))
                best_metric = f"{float(top.get('primary_metric', 0)):.4f}"
        except Exception:
            pass

        has_report = md_path.exists()
        report_tag = '<span class="exp-tag">View Report</span>' \
                     if has_report else \
                     '<span style="font-size:11px; color:#2e3650;">No report</span>'

        st.markdown(f"""
        <div class="exp-card">
            <div>
                <div class="exp-id">{exp_id}</div>
                <div class="exp-meta">Best: {best_model} · F1 {best_metric}</div>
            </div>
            {report_tag}
        </div>
        """, unsafe_allow_html=True)


# Status bar footer
st.markdown("""
<div style="margin-top:40px; padding:14px 20px;
            background:#0a0c11; border:1px solid #1a1f2e;
            border-radius:10px; display:flex;
            align-items:center; justify-content:space-between;">
    <div style="font-size:12px; color:#3a4460;
                font-family:'JetBrains Mono',monospace;">
        <span class="status-dot"></span>
        AIRO v0.1.0 · LangGraph · Groq LLaMA 3.3 · MLflow SQLite
    </div>
    <div style="font-size:11px; color:#2e3650;">
        BSAI · Dawood University · 2026
    </div>
</div>
""", unsafe_allow_html=True)
