"""
Gamma Bomb Trap — Streamlit Entry Point
========================================
Thin orchestration layer. All business logic lives in core/.

Architecture:
  core/
    domain/         → Black-76 engine, models, constants
    use_cases/      → GEX analysis, GTBR, data helpers
    infrastructure/ → GitHub client, session state manager
    presentation/   → Tabs, charts, legend, CSS styles
"""
import json
import ssl
ssl._create_default_https_context = ssl._create_unverified_context

import streamlit as st
import time

# ── Page Config (must be first Streamlit call) ──
st.set_page_config(layout="wide", page_title="GBT-Analysis", page_icon=":abacus:")

# ── Core Imports ──
from core.presentation.styles import inject_page_css
from core.infrastructure.session_manager import SessionManager
from core.infrastructure.github_client import (
    fetch_github_history,
    get_latest_commit_sha,
)
from core.use_cases.data_helpers import filter_session_data
from core.domain.constants import AUTO_REFRESH_INTERVAL

# ── Tab Renderers ──
from core.presentation.tab_intraday import render_intraday_tab
from core.presentation.tab_oi import render_oi_tab
from core.presentation.tab_gbt import render_gbt_tab
from core.presentation.tab_guide import render_guide_tab

# ── Inject CSS ──
inject_page_css()

# ── Secrets ──
try:
    GITHUB_TOKEN = st.secrets["github"]["access_token"]
except Exception:
    GITHUB_TOKEN = ""

REPO = st.secrets["github"]["data_source_repo"]

# ══════════════════════════════════════
# Session State — Initialize & Load Data
# ══════════════════════════════════════
sm = SessionManager(repo=REPO, token=GITHUB_TOKEN)
sm.handle_stale_data()
sm.handle_initial_load()

df_intraday = sm.df_intraday
df_oi       = sm.df_oi

# ══════════════════════════════════════
# Top Controls
# ══════════════════════════════════════
col_spin, col_mode, col_dropdown, col_refresh = st.columns([5.5, 2, 2, 1.5])

with col_dropdown:
    chart_mode = st.selectbox(
        "โหมดแสดงกราฟ",
        ["Call / Put Vol", "Total Vol"],
        label_visibility="collapsed",
    )

with col_mode:
    _prev_fetch_mode = st.session_state.fetch_mode
    fetch_mode = st.selectbox(
        "Fetch Mode",
        ["📋 Manual", "🔄 Auto (1 min)"],
        index=["📋 Manual", "🔄 Auto (1 min)"].index(st.session_state.fetch_mode),
        label_visibility="collapsed",
        key="fetch_mode_select",
    )
    st.session_state.fetch_mode = fetch_mode
    if fetch_mode == "🔄 Auto (1 min)" and _prev_fetch_mode != fetch_mode:
        st.session_state.last_auto_check = time.time()

with col_spin:
    status_placeholder = st.empty()

    print(f"Intraday data loaded: {not df_intraday.empty}, OI data loaded: {not df_oi.empty}")
    print(f"Intraday data length: {len(df_intraday)}, OI data length: {len(df_oi)}")
    if not df_intraday.empty:
        last_fetch = df_intraday['Datetime'].max().strftime("%H:%M:%S")
        status_placeholder.caption(f"⏱  ข้อมูลล่าสุดเวลา **{last_fetch}** น.")

with col_refresh:
    refresh_disabled = (fetch_mode == "🔄 Auto (1 min)")
    if st.button(
        ":material/refresh: Refresh",
        use_container_width=True,
        disabled=refresh_disabled,
        help="ปิดใช้งานเมื่อเปิด Auto Refresh" if refresh_disabled else "โหลดข้อมูลใหม่จาก GitHub",
    ):
        start_time = time.time()
        with status_placeholder:
            with st.spinner("กำลังเชื่อมต่อข้อมูล..."):
                sm.manual_refresh()
                elapsed_time = time.time() - start_time
                if elapsed_time < 3.0:
                    time.sleep(3.0 - elapsed_time)

        # Reload references after refresh
        df_intraday = sm.df_intraday
        df_oi       = sm.df_oi
        st.rerun()


# ══════════════════════════════════════
# Main Content — Tabs
# ══════════════════════════════════════
print(f"intraday data rows: {len(df_intraday)}, OI data rows: {len(df_oi)}")
if not df_intraday.empty:
    available_times = df_intraday['Time'].unique()

    if (
        'selected_time_state' not in st.session_state
        or st.session_state.selected_time_state not in available_times
    ):
        st.session_state.selected_time_state = available_times[-1]

    if st.session_state.is_playing:
        if 'anim_idx' in st.session_state and st.session_state.anim_idx < len(available_times):
            st.session_state.selected_time_state = available_times[st.session_state.anim_idx]

    tab1, tab2, tab3, tab4 = st.tabs([
        ":material/query_stats: GBT Analysis",
        ":material/show_chart: Intraday Volume",
        ":material/account_balance: Open Interest (OI)",
        ":material/menu_book: คู่มืออ่านค่า",
    ])

    # ── Tab 1 — GBT Composite Analysis ──
    with tab1:
        render_gbt_tab(df_intraday, df_oi, chart_mode)

    # ── Tab 2 — Intraday Volume ──
    with tab2:
        render_intraday_tab(df_intraday, chart_mode, available_times)

    # ── Tab 3 — Open Interest ──
    with tab3:
        render_oi_tab(df_oi, chart_mode)

    # ── Tab 4 — Guide ──
    with tab4:
        render_guide_tab()


# ══════════════════════════════════════
# Auto-Refresh Engine
# ══════════════════════════════════════
if st.session_state.fetch_mode == "🔄 Auto (1 min)":
    now      = time.time()
    elapsed  = now - st.session_state.last_auto_check
    wait_sec = max(0.0, AUTO_REFRESH_INTERVAL - elapsed)

    # ── Update status bar countdown ──
    if not df_intraday.empty:
        last_fetch_t = df_intraday['Datetime'].max().strftime("%H:%M:%S")
        if wait_sec > 0:
            status_placeholder.caption(
                f"⏱ ข้อมูลล่าสุด **{last_fetch_t}** น.  |  "
                f"🔄 ตรวจสอบอัปเดตใน **{int(wait_sec)} วินาที**"
            )
        else:
            status_placeholder.caption(
                f"⏱ ข้อมูลล่าสุด **{last_fetch_t}** น.  |  🔄 กำลังตรวจสอบ..."
            )

    if wait_sec <= 0:
        # ── Check GitHub for new commits ──
        new_sha_intra = get_latest_commit_sha("IntradayData.txt", REPO, GITHUB_TOKEN)
        new_sha_oi    = get_latest_commit_sha("OIData.txt", REPO, GITHUB_TOKEN)

        data_changed = (
            new_sha_intra != st.session_state.sha_intra
            or new_sha_oi  != st.session_state.sha_oi
        )

        if data_changed:
            raw_i = fetch_github_history("IntradayData.txt", REPO, GITHUB_TOKEN, max_commits=200)
            raw_o = fetch_github_history("OIData.txt", REPO, GITHUB_TOKEN, max_commits=1)
            st.session_state.my_intraday_data = filter_session_data(raw_i, "Intraday")
            st.session_state.my_oi_data       = filter_session_data(raw_o, "OI")
            st.session_state.last_fetch_datetime = sm._get_data_last_fetch_dt()
            if 'selected_time_state' in st.session_state:
                del st.session_state['selected_time_state']

        # Update tracking state
        st.session_state.sha_intra       = new_sha_intra
        st.session_state.sha_oi          = new_sha_oi
        st.session_state.last_auto_check = time.time()
        st.rerun()

    else:
        # ── Sleep in 5-second ticks so the countdown stays responsive ──
        time.sleep(min(5.0, wait_sec))
        st.rerun()
