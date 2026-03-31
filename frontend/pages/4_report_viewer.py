"""AIRO — frontend/pages/4_report_viewer.py"""
import base64
import glob
import mimetypes
import re
from pathlib import Path

import streamlit as st
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
    selected = st.selectbox(
        "Select report", reports, format_func=lambda x: Path(x).parent.name
    )
    report_file = Path(selected)
    content = report_file.read_text(encoding="utf-8")

    # Embed local relative images as base64 data URIs so Streamlit renders them natively
    def _embed_local_images(match):
        alt, path_str = match.group(1), match.group(2)
        if path_str.startswith(("http", "data:")):
            return match.group(0)
            
        img_path = report_file.parent / path_str
        if img_path.exists() and img_path.is_file():
            mime, _ = mimetypes.guess_type(str(img_path))
            mime = mime or "image/png"
            with open(img_path, "rb") as f:
                b64_data = base64.b64encode(f.read()).decode("utf-8")
            return f"![{alt}](data:{mime};base64,{b64_data})"
        return match.group(0)

    content_with_images = re.sub(r"!\[(.*?)\]\((.*?)\)", _embed_local_images, content)
    st.markdown(content_with_images, unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        st.download_button(
            "📥 Download Markdown", content, file_name="airo_report.md", mime="text/markdown"
        )
    with col2:
        pdf_path = report_file.with_suffix(".pdf")
        if pdf_path.exists():
            with open(pdf_path, "rb") as f:
                st.download_button("📥 Download PDF", f, file_name="airo_report.pdf", mime="application/pdf")
