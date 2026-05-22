# ============================================================
# ILASO Premium 6-File System — UI Components
# ============================================================
import streamlit as st
from config_styles import PREMIUM_CSS


def apply_page_config():
    st.set_page_config(
        page_title="ILASO Premium",
        page_icon="📘",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    st.markdown(PREMIUM_CSS, unsafe_allow_html=True)


def hero():
    st.markdown(
        """
        <div class="ilaso-hero">
            <div class="ilaso-kicker">Premium Allocation Intelligence</div>
            <div class="ilaso-title">ILASO</div>
            <div class="ilaso-subtitle">
                Intelligent Lecturer Allocation System with Fair KS Optimization, Emergency Reallocation Log,
                and Minimal-Disturbance Academic Workload Governance.
            </div>
            <div class="ilaso-tag-row">
                <span class="ilaso-tag">Fair KS Engine</span>
                <span class="ilaso-tag">Min/Max Individu</span>
                <span class="ilaso-tag">Emergency Log</span>
                <span class="ilaso-tag">Premium Dashboard</span>
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
