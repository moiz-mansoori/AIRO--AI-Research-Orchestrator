"""AIRO — frontend/pages/4_report_viewer.py"""
import streamlit as st
from pathlib import Path
import glob
from components.theme import inject_theme_css
from components.sidebar import render_sidebar

inject_theme_css()
render_sidebar()

st.markdown('<div class="page-title">📄 Report Viewer</div>', unsafe_allow_html=True)
st.markdown('<div class="page-desc">View and download generated experiment reports.</div>', unsafe_allow_html=True)

reports = sorted(glob.glob("reports/*/airo_report.md"), reverse=True)

if not reports:
    st.info("No reports generated yet. Run an experiment first.")
else:
    selected = st.selectbox("Select report", reports,
                            format_func=lambda x: Path(x).parent.name)
    content  = Path(selected).read_text(encoding="utf-8")
    st.markdown(content, unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        st.download_button("📥 Download Markdown", content, file_name="airo_report.md", mime="text/markdown")
    with col2:
        pdf_path = Path(selected).with_suffix(".pdf")
        if pdf_path.exists():
            with open(pdf_path, "rb") as f:
                st.download_button("📥 Download PDF", f, file_name="airo_report.pdf", mime="application/pdf")
