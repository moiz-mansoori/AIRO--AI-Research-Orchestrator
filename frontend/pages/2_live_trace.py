"""AIRO — frontend/pages/2_live_trace.py

Real-time log viewer for the AIRO agents.
"""
import time
from pathlib import Path

import streamlit as st
from components.sidebar import render_sidebar
from components.theme import inject_theme_css

inject_theme_css()
render_sidebar()

st.markdown('<div class="page-title">📡 Live Agent Trace</div>', unsafe_allow_html=True)
st.markdown('<div class="page-desc">Real-time log viewer. Auto-refreshes while a pipeline is running.</div>', unsafe_allow_html=True)

# Status banner 
is_running  = st.session_state.get("running", False)
exp_id      = st.session_state.get("experiment_id")
start_time  = st.session_state.get("start_time")

if is_running:
    elapsed   = int(time.time() - (start_time or time.time()))
    mins, sec = divmod(elapsed, 60)
    st.markdown(f"""
    <div style="background:#0a1f0f; border:1px solid #0d3320;
                border-left:4px solid #10b981; border-radius:10px;
                padding:14px 20px; margin-bottom:16px;
                display:flex; align-items:center; gap:12px;">
        <span style="font-size:18px;">⚡</span>
        <div>
            <div style="font-size:13px; font-weight:600; color:#10b981;">
                Pipeline running — auto-refreshing every 3s
            </div>
            <div style="font-family:'JetBrains Mono',monospace; font-size:11px;
                        color:#4a7a5e; margin-top:2px;">
                {f"Experiment: {exp_id}" if exp_id else "Waiting for experiment ID..."}
                &nbsp;·&nbsp; Elapsed: {mins:02d}:{sec:02d}
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

elif st.session_state.get("done") and exp_id:
    st.markdown(f"""
    <div style="background:#0f1e35; border:1px solid #1e3a5f;
                border-left:4px solid #4f8ef7; border-radius:10px;
                padding:14px 20px; margin-bottom:16px;">
        <div style="font-size:13px; font-weight:600; color:#4f8ef7;">
            ✅ Last experiment complete
        </div>
        <div style="font-family:'JetBrains Mono',monospace; font-size:11px;
                    color:#5a6480; margin-top:2px;">
            {exp_id}
        </div>
    </div>
    """, unsafe_allow_html=True)

# Log viewer     
log_path = Path(__file__).parents[2] / "logs" / "airo.log"
if not log_path.exists():
    log_path = Path(__file__).parents[2] / "logs" / "experiment.log"

if log_path.exists():
    try:
        content = log_path.read_text(encoding="utf-8", errors="replace").strip()
        lines   = content.split("\n") if content else []
    except Exception:
        lines = []

    # Controls row
    ctrl1, ctrl2, ctrl3 = st.columns([2, 1, 1])
    with ctrl1:
        n_lines = st.slider("Lines to show", 50, 500, 150, step=50)
    with ctrl2:
        follow  = st.checkbox("Follow tail", value=True,
                              help="Always show most recent lines")
    with ctrl3:
        if st.button("🔄 Refresh now", use_container_width=True):
            st.rerun()

    display_lines = lines[-n_lines:] if follow else lines[:n_lines]
    log_text      = "\n".join(display_lines) if display_lines else "Log file is empty."

    # Color-code log levels with HTML
    colored_lines = []
    for line in display_lines:
        if "ERROR" in line or "✗" in line or "FAILED" in line:
            colored_lines.append(
                f'<span style="color:#f87171;">{line}</span>'
            )
        elif "WARNING" in line or "WARN" in line:
            colored_lines.append(
                f'<span style="color:#fbbf24;">{line}</span>'
            )
        elif "✓" in line or "complete" in line.lower() or "PASS" in line:
            colored_lines.append(
                f'<span style="color:#34d399;">{line}</span>'
            )
        elif line.startswith("2") and "|" in line:  # timestamp lines
            colored_lines.append(
                f'<span style="color:#94a3b8;">{line}</span>'
            )
        else:
            colored_lines.append(
                f'<span style="color:#c9cdd8;">{line}</span>'
            )

    log_html = "<br>".join(colored_lines) if colored_lines else \
               '<span style="color:#3a4460;">Log file is empty.</span>'

    st.markdown(f"""
    <div style="background:#0a0c11; border:1px solid #1a1f2e;
                border-radius:10px; padding:20px 24px;
                font-family:'JetBrains Mono',monospace; font-size:12px;
                line-height:1.8; max-height:520px; overflow-y:auto;">
        {log_html}
    </div>
    """, unsafe_allow_html=True)

    st.caption(
        f"Log file: `{log_path}` · {len(lines)} total lines · "
        f"showing last {len(display_lines)}"
    )

else:
    st.markdown("""
    <div style="background:#10131a; border:1px dashed #1e2330;
                border-radius:10px; padding:32px; text-align:center;">
        <div style="font-size:32px; margin-bottom:8px;">📭</div>
        <div style="font-size:14px; color:#5a6480; font-weight:500;">
            No log file found yet
        </div>
        <div style="font-size:12px; color:#3a4460; margin-top:4px;">
            Launch a pipeline from
            <span style="color:#4f8ef7;">Run Experiment</span>
            first
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.caption(f"Looking for: `{log_path}`")

# Auto-refresh while pipeline is running 
if is_running:
    time.sleep(3)
    st.rerun()
