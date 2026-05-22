# ============================================================
# ILASO 6-File System — UI Components
# ============================================================
import streamlit as st
from config_styles import PREMIUM_CSS


def apply_page_config():
    st.set_page_config(
        page_title="ILASO",
        page_icon="📘",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    st.markdown(PREMIUM_CSS, unsafe_allow_html=True)


def hero():
    st.markdown(
        """
        <div class="ilaso-hero">
            <div class="ilaso-kicker">Intelligent Lecturer Allocation System</div>
            <div class="ilaso-title">ILASO</div>
            <div class="ilaso-subtitle">
                Fair KS Distribution • Emergency Reallocation • Manual Fine Tuning • Academic Workload Optimization
            </div>
            <div class="ilaso-tag-row">
                <span class="ilaso-tag">Fair KS Distribution</span>
                <span class="ilaso-tag">Individual Min/Max KS</span>
                <span class="ilaso-tag">Emergency Log</span>
                <span class="ilaso-tag">Manual Fine Tuning</span>
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
