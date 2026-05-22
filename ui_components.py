# ============================================================
# ILASO — UI Components (Bentara Sigma Hero)
# Replace your existing ui_components.py with this file.
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
        else '<div class="sigma-fallback">Σ</div>'
    )

    st.markdown(
        f"""
        <div class="hero-shell">
            <div class="hero-glow hero-glow-one"></div>
            <div class="hero-glow hero-glow-two"></div>
            <div class="hero-content-grid">
                <div class="hero-logo-card">
                    {logo_html}
                </div>
                <div class="hero-copy">
                    <div class="hero-eyebrow">Bentara Sigma Initiative</div>
                    <div class="hero-title-main">ILASO</div>
                    <div class="hero-title-sub">Intelligent Lecturer Allocation System</div>
                    <div class="hero-description">
                        Fair KS Distribution • Emergency Reallocation • Manual Fine Tuning • Academic Workload Optimization
                    </div>
                    <div class="hero-chip-row">
                        <span>Fair KS Distribution</span>
                        <span>Individual Min/Max KS</span>
                        <span>Emergency Log</span>
                        <span>Manual Fine Tuning</span>
                    </div>
                </div>
            </div>

            <div class="hero-workflow">
                <div class="hero-step"><b>01</b><span>Upload Data</span></div>
                <div class="hero-step"><b>02</b><span>Validate KS</span></div>
                <div class="hero-step"><b>03</b><span>Optimize</span></div>
                <div class="hero-step"><b>04</b><span>Adjust</span></div>
                <div class="hero-step"><b>05</b><span>Export</span></div>
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
