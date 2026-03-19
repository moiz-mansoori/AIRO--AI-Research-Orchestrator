"""AIRO — frontend/pages/3_leaderboard.py"""
import streamlit as st
import pandas as pd
from pathlib import Path
import glob
from components.theme import inject_theme_css
from components.sidebar import render_sidebar

inject_theme_css()
render_sidebar()

st.markdown('<div class="page-title">🏆 Experiment Leaderboard</div>', unsafe_allow_html=True)
st.markdown('<div class="page-desc">Compare models across all your experiments.</div>', unsafe_allow_html=True)

csvs = sorted(glob.glob("reports/*/leaderboard.csv"), reverse=True)

if not csvs:
    st.info("No experiments run yet. Run an experiment first.")
else:
    selected = st.selectbox("Select experiment", csvs,
                            format_func=lambda x: Path(x).parent.name)
    df = pd.read_csv(selected)
    st.dataframe(df, use_container_width=True, hide_index=True)

    if "model_type" in df.columns:
        metric_cols = [c for c in df.columns if c not in ("rank", "model_type", "config_id", "run_id", "verdict", "Rank", "Model")]
        if metric_cols:
            chart_metric = st.selectbox("Chart metric", metric_cols)
            st.bar_chart(df.set_index("model_type" if "model_type" in df.columns else "Model")[chart_metric])

    exp_dir = Path(selected).parent
    shap_img = exp_dir / "shap_summary.png"
    if shap_img.exists():
        st.subheader("SHAP Feature Importance")
        st.image(str(shap_img))

    curve_dir = exp_dir / "learning_curves"
    curve_files = list(curve_dir.glob("*.png")) if curve_dir.exists() else []
    if curve_files:
        st.subheader("Learning Curves")
        cols = st.columns(min(len(curve_files), 3))
        for i, cf in enumerate(curve_files):
            cols[i % 3].image(str(cf), caption=cf.stem)
