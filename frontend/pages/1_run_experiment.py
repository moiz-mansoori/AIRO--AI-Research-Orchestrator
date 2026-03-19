"""AIRO — frontend/pages/1_run_experiment.py"""
import json
import tempfile
from pathlib import Path

import streamlit as st
from components.theme import inject_theme_css
from components.sidebar import render_sidebar

inject_theme_css()
render_sidebar()

st.markdown('<div class="page-title">🚀 Run Experiment</div>', unsafe_allow_html=True)
st.markdown('<div class="page-desc">Upload a dataset, configure your experiment, and launch the AIRO pipeline.</div>', unsafe_allow_html=True)

col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("Dataset")
    uploaded = st.file_uploader("Upload CSV, Parquet, or JSON", type=["csv", "parquet", "json"])
    target_col = st.text_input("Target column name", value="target")

with col2:
    st.subheader("Configuration")
    task_type = st.selectbox("Task type", ["classification", "regression"])
    budget    = st.selectbox("Compute budget",
                             ["fast (3 configs)", "standard (6 configs)", "exhaustive (10 configs)"])
    budget_map = {"fast (3 configs)": "fast", "standard (6 configs)": "standard", "exhaustive (10 configs)": "exhaustive"}

    skip_curves = st.checkbox("Skip learning curves (faster)", value=True)
    skip_shap = st.checkbox("Skip SHAP explainability (faster)", value=False)

st.divider()

if uploaded and st.button("▶  Launch AIRO Pipeline", type="primary", use_container_width=True):
    import sys, os
    project_root = str(Path(__file__).parents[2])
    sys.path.insert(0, project_root)
    os.chdir(project_root)

    from dotenv import load_dotenv
    load_dotenv()

    # Set skip toggles
    if skip_curves:
        os.environ["AIRO_SKIP_CURVES"] = "true"
    if skip_shap:
        os.environ["AIRO_SKIP_SHAP"] = "true"

    from orchestrator.graph import compile_graph
    from orchestrator.state import AIROState, TaskType, ComputeBudget

    # Save upload to data/raw
    suffix = Path(uploaded.name).suffix
    raw_dir = Path("data/raw")
    raw_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix, dir=str(raw_dir)) as tmp:
        tmp.write(uploaded.getbuffer())
        dataset_path = tmp.name

    initial_state = AIROState(
        dataset_path   = dataset_path,
        task_type      = TaskType(task_type),
        target_column  = target_col,
        compute_budget = ComputeBudget(budget_map[budget]),
    )

    st.info(f"Experiment ID: `{initial_state.experiment_id}`")
    graph = compile_graph()

    progress_bar = st.progress(0, text="Starting AIRO agents...")

    with st.spinner("Running AIRO agents..."):
        final_state = graph.invoke(initial_state, config={"recursion_limit": 50})

    progress_bar.progress(100, text="Pipeline complete!")

    errors = final_state.get("errors", [])
    if errors:
        st.error("Pipeline completed with errors:")
        for e in errors:
            st.code(e)
    else:
        st.success("✅ Experiment complete!")

    leaderboard = final_state.get("leaderboard", [])
    if leaderboard:
        st.subheader("Results")
        m1, m2, m3 = st.columns(3)

        best_model = final_state.get("best_model_type", "N/A")
        task = final_state.get("task_type", "classification")
        metric_name = "f1_macro" if task == "classification" else "rmse"
        improvement = final_state.get("improvement_over_baseline_pct", 0)

        m1.metric("Best model", best_model)
        m2.metric(metric_name.upper(), f"{leaderboard[0].primary_metric:.4f}")
        m3.metric("vs baseline", f"{improvement:+.1f}%")

    if leaderboard:
        import pandas as pd
        df = pd.DataFrame([{
            "Rank": e.rank, "Model": e.model_type,
            metric_name.upper(): e.primary_metric,
            "Verdict": e.verdict,
        } for e in leaderboard])
        st.dataframe(df, use_container_width=True, hide_index=True)

    report_md = final_state.get("report_md_path", "")
    report_pdf = final_state.get("report_pdf_path", "")

    if report_pdf and Path(report_pdf).exists():
        with open(report_pdf, "rb") as f:
            st.download_button("📄 Download PDF Report", f, file_name="airo_report.pdf", mime="application/pdf")
    elif report_md and Path(report_md).exists():
        with open(report_md, "r", encoding="utf-8") as f:
            st.download_button("📄 Download Markdown Report", f.read(), file_name="airo_report.md", mime="text/markdown")
