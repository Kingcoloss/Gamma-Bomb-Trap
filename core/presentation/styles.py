"""
CSS Styles and Styled Components
=================================
Custom CSS and HTML builder functions for the Streamlit dashboard.
"""
import streamlit as st


# ── Page-level custom CSS ──
PAGE_CSS = """
<style>
    .block-container {
        padding-top: 3rem !important;
        padding-bottom: 1rem !important;
    }
    .header-box {
        background-color: var(--secondary-background-color);
        color: var(--text-color) !important;
        padding: 15px;
        border-radius: 8px;
        margin-bottom: 20px;
        text-align: center;
        border: 1px solid var(--border-color);
    }
    .header-title { font-size: 20px; font-weight: bold; color: var(--text-color); margin-bottom: 10px; }
    .header-metrics span { font-size: 16px; margin: 0 15px; font-weight: bold; }
    .t-put { color: #F59E0B; }
    .t-call { color: #3B82F6; }
    .t-vol { color: #EF4444; }
    .t-neutral { color: #718096; }
    div[data-baseweb="select"] {
        user-select: none;
        -webkit-user-select: none;
        -ms-user-select: none;
        cursor: pointer !important;
    }
    div[data-baseweb="select"] * { cursor: pointer !important; }
    div[data-baseweb="select"] input { caret-color: transparent !important; }
</style>
"""


def inject_page_css():
    """Inject the page-level custom CSS."""
    st.markdown(PAGE_CSS, unsafe_allow_html=True)


def get_styled_header(h1_text: str, h2_text: str) -> str:
    """Build a styled header box with color-coded metrics."""
    h2_styled = (h2_text
        .replace("Put:", "<span class='t-put'>Put:</span>")
        .replace("Call:", "<span class='t-call'>Call:</span>")
        .replace("Vol:", "<span class='t-vol'>Vol:</span>")
        .replace("Vol Chg:", "<span class='t-neutral'>Vol Chg:</span>")
        .replace("Future Chg:", "<span class='t-neutral'>Future Chg:</span>"))
    return f"""
    <div class="header-box" style="margin-bottom: 5px;">
        <div class="header-title">{h1_text}</div>
        <div class="header-metrics">{h2_styled}</div>
    </div>
    """
