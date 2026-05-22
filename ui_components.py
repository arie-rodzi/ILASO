# ============================================================
# ILASO 6-File System — UI Components
# ============================================================
import base64
from pathlib import Path
import streamlit as st
from config_styles import APP_CSS


def _image_to_base64(path: str) -> str:
    file_path = Path(__file__).parent / path
    if not file_path.exists():
        return ""
    return base64.b64encode(file_path.read_bytes()).decode("utf-8")


def apply_page_config():
    st.set_page_config(
        page_title="ILASO",
        page_icon="📘",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    st.markdown(APP_CSS, unsafe_allow_html=True)


def hero():
    logo_b64 = _image_to_base64("assets/bentara_sigma_logo.png")
    logo_html = (
        f'<img src="data:image/png;base64,{logo_b64}" alt="Bentara Sigma Logo" />'
        if logo_b64
        else '<div style="font-size:52px;font-weight:1000;color:#F5D27A;">Σ</div>'
    )

    st.markdown(
        f"""
        <div class="ilaso-hero">
            <div class="hero-grid">
                <div class="hero-logo-wrap">
                    {logo_html}
                </div>
                <div>
                    <div class="ilaso-kicker">Bentara Sigma Initiative</div>
                    <div class="ilaso-title">ILASO</div>
                    <div class="ilaso-subtitle">Intelligent Lecturer Allocation System</div>
                    <div class="ilaso-subnote">
                        Fair KS Distribution • Emergency Reallocation • Manual Fine Tuning • Academic Workload Optimization
                    </div>
                    <div class="ilaso-tag-row">
                        <span class="ilaso-tag">Fair KS Distribution</span>
                        <span class="ilaso-tag">Individual Min/Max KS</span>
                        <span class="ilaso-tag">Emergency Log</span>
                        <span class="ilaso-tag">Manual Fine Tuning</span>
                    </div>
                </div>
            </div>
            <div class="workflow-strip">
                <div class="workflow-chip"><b>01 Upload</b><span>Class and lecturer data</span></div>
                <div class="workflow-chip"><b>02 Optimize</b><span>Fair KS allocation</span></div>
                <div class="workflow-chip"><b>03 Adjust</b><span>Emergency and manual tuning</span></div>
                <div class="workflow-chip"><b>04 Export</b><span>Decision-ready reports</span></div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def section(title, note=""):
    st.markdown(f'<div class="section-title">{title}</div>', unsafe_allow_html=True)
    if note:
        st.markdown(f'<div class="section-note">{note}</div>', unsafe_allow_html=True)


def metric_card(label, value, note=""):
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">{label}</div>
            <div class="metric-value">{value}</div>
            <div class="metric-note">{note}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def soft_card_html(html):
    st.markdown(f'<div class="soft-card">{html}</div>', unsafe_allow_html=True)
