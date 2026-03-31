"""AIRO — frontend/pages/1_run_experiment.py

Main dashboard for uploading datasets, configuring budgets, 
and launching the LangGraph AIRO pipeline asynchronously.
"""
import os
import sys
import tempfile
import threading
import time
from pathlib import Path

import streamlit as st
from streamlit.runtime.scriptrunner import add_script_run_ctx

from components.sidebar import render_sidebar
from components.theme import inject_theme_css

# Pre-load heavy modules on the main thread to prevent import lock deadlocks
from dotenv import load_dotenv
from loguru import logger
from orchestrator.graph import compile_graph
from orchestrator.state import AIROState, ComputeBudget, TaskType

load_dotenv()

inject_theme_css()
render_sidebar()

st.markdown('<div class="page-title">🚀 Run Experiment</div>', unsafe_allow_html=True)
st.markdown('<div class="page-desc">Upload a dataset, configure your experiment, and launch the AIRO pipeline.</div>', unsafe_allow_html=True)

# Session state keys 
KEYS = {
    "running":      False,   # pipeline is currently executing
    "done":         False,   # pipeline finished
    "final_state":  None,    # AIROState result object
    "experiment_id": None,   # current experiment ID
    "errors":       [],      # pipeline errors
    "thread":       None,    # background thread reference
    "start_time":   None,    # when pipeline started
}
for k, v in KEYS.items():
    if k not in st.session_state:
        st.session_state[k] = v


# Background pipeline runner 
def _run_pipeline_background(
    dataset_path: str,
    task_type: str,
    target_col: str,
    budget: str,
    skip_curves: bool,
    skip_shap: bool,
    project_root: str,
) -> None:
    """
    Runs in a background thread. Writes results back to st.session_state
    so the main Streamlit thread can read them on each rerun.
    """
    try:
        sys.path.insert(0, project_root)
        os.chdir(project_root)

        Path("logs").mkdir(exist_ok=True, parents=True)
        log_file = str(Path(__file__).parents[2] / "logs" / "airo.log")
        # Remove old handlers to avoid duplicate logs
        logger.remove()
        logger.add(log_file, mode="w", enqueue=True, catch=True,
                   format="{time:HH:mm:ss} | {level:<8} | {message}")
        logger.add(lambda msg: None)  # suppress stderr in thread

        if skip_curves:
            os.environ["AIRO_SKIP_CURVES"] = "true"
        if skip_shap:
            os.environ["AIRO_SKIP_SHAP"] = "true"

        initial_state = AIROState(
            dataset_path   = dataset_path,
            task_type      = TaskType(task_type),
            target_column  = target_col,
            compute_budget = ComputeBudget(budget),
        )

        # Write experiment ID immediately so Live Trace page can show it
        st.session_state["experiment_id"] = initial_state.experiment_id
        logger.info(f"[AIRO] Experiment started: {initial_state.experiment_id}")

        graph = compile_graph()
        final_state = graph.invoke(
            initial_state,
            config={"recursion_limit": 50},
        )

        st.session_state["final_state"] = final_state
        st.session_state["errors"] = getattr(final_state, "errors", [])
        logger.info(f"[AIRO] Experiment complete: {initial_state.experiment_id}")

    except Exception as exc:
        import traceback
        st.session_state["errors"] = [f"Pipeline crashed: {exc}\n{traceback.format_exc()}"]

    finally:
        st.session_state["running"] = False
        st.session_state["done"]    = True


# Upload & config form 
# Only show the form when the pipeline is NOT running
if not st.session_state["running"]:
    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("Dataset")
        uploaded    = st.file_uploader("Upload CSV, Parquet, or JSON",
                                       type=["csv", "parquet", "json"])
        target_col  = st.text_input("Target column name", value="target")

    with col2:
        st.subheader("Configuration")
        task_type   = st.selectbox("Task type", ["classification", "regression"])
        budget_label = st.selectbox(
            "Compute budget",
            ["fast (3 configs)", "standard (6 configs)", "exhaustive (10 configs)"]
        )
        budget_map  = {
            "fast (3 configs)":        "fast",
            "standard (6 configs)":    "standard",
            "exhaustive (10 configs)": "exhaustive",
        }
        skip_curves = st.checkbox("Skip learning curves (faster)", value=True)
        skip_shap   = st.checkbox("Skip SHAP explainability (faster)", value=False)

    st.divider()

    launch_clicked = st.button(
        "▶  Launch AIRO Pipeline",
        type="primary",
        use_container_width=True,
        disabled=uploaded is None,
    )

    if launch_clicked and uploaded:
        # Save file to temp location (NOT data/raw — avoids pollution)
        suffix = Path(uploaded.name).suffix
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(uploaded.getbuffer())
            dataset_path = tmp.name

        # Reset state for new run
        st.session_state["running"]      = True
        st.session_state["done"]         = False
        st.session_state["final_state"]  = None
        st.session_state["errors"]       = []
        st.session_state["experiment_id"] = None
        st.session_state["start_time"]   = time.time()

        project_root = str(Path(__file__).parents[2])

        # Launch pipeline in background thread — UI stays responsive
        thread = threading.Thread(
            target=_run_pipeline_background,
            args=(
                dataset_path,
                task_type,
                target_col,
                budget_map[budget_label],
                skip_curves,
                skip_shap,
                project_root,
            ),
            daemon=True,
        )
        # Attach Streamlit context so the background thread can write to session_state
        add_script_run_ctx(thread)
        thread.start()
        st.session_state["thread"] = thread
        st.rerun()


# Running state UI 
if st.session_state["running"]:
    exp_id    = st.session_state.get("experiment_id") or "starting..."
    elapsed   = int(time.time() - (st.session_state["start_time"] or time.time()))
    mins, sec = divmod(elapsed, 60)

    st.markdown(f"""
    <div style="background:#0f1e35; border:1px solid #1e3a5f;
                border-left:4px solid #4f8ef7; border-radius:10px;
                padding:20px 24px; margin:16px 0;">
        <div style="font-size:13px; color:#4f8ef7; font-weight:600;
                    margin-bottom:6px;">
            ⚡ Pipeline running...
        </div>
        <div style="font-family:'JetBrains Mono',monospace; font-size:12px;
                    color:#8aa8d4; margin-bottom:4px;">
            Experiment: {exp_id}
        </div>
        <div style="font-family:'JetBrains Mono',monospace; font-size:12px;
                    color:#5a6480;">
            Elapsed: {mins:02d}:{sec:02d}
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.info("📡 Switch to **Live Trace** in the sidebar to watch agents execute in real time. Come back here when done.", icon="ℹ️")

    col_a, col_b = st.columns([1, 1])
    with col_a:
        if st.button("🔄 Check status", use_container_width=True):
            st.rerun()
    with col_b:
        st.caption("Page auto-refreshes every 5 seconds")

    # Auto-refresh every 5 seconds while running
    time.sleep(5)
    st.rerun()


# Results UI 
if st.session_state["done"]:
    final_state = st.session_state["final_state"]
    errors      = st.session_state["errors"]

    if errors:
        st.error("Pipeline completed with errors:")
        for e in errors:
            st.code(e)
    else:
        st.success(f"✅ Experiment complete!  `{st.session_state['experiment_id']}`")

    if final_state:
        leaderboard = getattr(final_state, "leaderboard", [])

        if leaderboard:
            st.subheader("Results")
            m1, m2, m3 = st.columns(3)
            best_model  = getattr(final_state, "best_model_type", "N/A")
            task        = str(getattr(final_state, "task_type", "classification"))
            metric_name = "f1_macro" if "classification" in task else "rmse"
            improvement = getattr(final_state, "improvement_over_baseline_pct", 0.0)

            m1.metric("Best model",       best_model)
            m2.metric(metric_name.upper(), f"{leaderboard[0].primary_metric:.4f}")
            m3.metric("vs baseline",      f"{improvement:+.1f}%")

            import pandas as pd
            df = pd.DataFrame([{
                "Rank":           e.rank,
                "Model":          e.model_type,
                metric_name.upper(): e.primary_metric,
                "Verdict":        e.verdict,
            } for e in leaderboard])
            st.dataframe(df, use_container_width=True, hide_index=True)

        report_pdf = getattr(final_state, "report_pdf_path", "")
        report_md  = getattr(final_state, "report_md_path", "")

        if report_pdf and Path(report_pdf).exists():
            with open(report_pdf, "rb") as f:
                st.download_button("📄 Download PDF Report", f,
                                   file_name="airo_report.pdf",
                                   mime="application/pdf")
        elif report_md and Path(report_md).exists():
            with open(report_md, "r", encoding="utf-8") as f:
                st.download_button("📄 Download Markdown Report", f.read(),
                                   file_name="airo_report.md",
                                   mime="text/markdown")

    # Allow starting a new experiment
    st.divider()
    if st.button("🔁 Run another experiment", use_container_width=True):
        st.session_state["done"]        = False
        st.session_state["final_state"] = None
        st.session_state["errors"]      = []
        st.session_state["experiment_id"] = None
        st.rerun()