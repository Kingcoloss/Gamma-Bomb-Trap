"""
Tab 2 — Intraday Volume
========================
Renders the Intraday Volume (γ-Flow) analysis tab.
"""
import math
import time

import pandas as pd
import numpy as np
import streamlit as st
import streamlit.components.v1 as components
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from core.use_cases.gex_analysis import calculate_gex_analysis, get_atm_iv
from core.use_cases.gtbr import calculate_gamma_theta_breakeven
from core.use_cases.data_helpers import extract_atm, extract_dte
from core.presentation.styles import get_styled_header
from core.presentation.chart_helpers import (
    add_atm_vline,
    add_theta_breakeven_vlines,
    add_gex_vlines,
)
from core.presentation.legend import render_line_legend


def render_intraday_tab(df_intraday: pd.DataFrame, chart_mode: str, available_times):
    """Render the Intraday Volume tab content."""
    time_val   = st.session_state.selected_time_state
    frame_data = (
        df_intraday[df_intraday['Time'] == time_val]
        .copy()
        .sort_values('Strike')
    )
    if frame_data['Vol Settle'].max() < 1:
        frame_data['Vol Settle'] = (frame_data['Vol Settle'] * 100).round(2)

    h1_intra = frame_data['Header1'].iloc[0]
    h2_intra = frame_data['Header2'].iloc[0]
    st.markdown(get_styled_header(h1_intra, h2_intra), unsafe_allow_html=True)

    # ── Compute GEX & breakeven ──
    atm_intra = extract_atm(h1_intra)
    dte_intra = extract_dte(h1_intra)

    frame_raw = (
        df_intraday[df_intraday['Time'] == time_val]
        .copy()
        .sort_values('Strike')
    )
    gex_flip_i = pos_wall_i = neg_wall_i = gex_peak_i = None
    gex_df_i = None
    lo_exp_i = hi_exp_i = lo_day_i = hi_day_i = None
    iv_atm_i = None
    net_vanna_i = net_volga_i = 0.0

    if atm_intra and dte_intra:
        iv_atm_i = get_atm_iv(frame_raw, atm_intra)
        if iv_atm_i and dte_intra > 0:
            result = calculate_gex_analysis(
                frame_raw, atm_intra, dte_intra, data_mode="Intraday"
            )
            gex_flip_i = result.flip
            pos_wall_i = result.pos_wall
            neg_wall_i = result.neg_wall
            gex_df_i = result.gex_df
            gex_peak_i = result.peak
            net_vanna_i = result.net_vanna_total
            net_volga_i = result.net_volga_total

            gtbr = calculate_gamma_theta_breakeven(atm_intra, iv_atm_i, dte_intra)
            lo_exp_i = gtbr.lo_expiry
            hi_exp_i = gtbr.hi_expiry
            lo_day_i = gtbr.lo_daily
            hi_day_i = gtbr.hi_daily

    # ── Build chart ──
    fig_intra = make_subplots(specs=[[{"secondary_y": True}]])

    if chart_mode == "Call / Put Vol":
        fig_intra.add_trace(
            go.Bar(
                x=frame_data['Strike'], y=frame_data['Put'],
                name='Put Vol',
                marker=dict(color='rgba(245, 158, 11, 0.85)', line=dict(color='#F59E0B', width=1)),
            ),
            secondary_y=False,
        )
        fig_intra.add_trace(
            go.Bar(
                x=frame_data['Strike'], y=frame_data['Call'],
                name='Call Vol',
                marker=dict(color='rgba(59, 130, 246, 0.85)', line=dict(color='#3B82F6', width=1)),
            ),
            secondary_y=False,
        )
    else:
        total_vol = frame_data['Call'] + frame_data['Put']
        fig_intra.add_trace(
            go.Bar(
                x=frame_data['Strike'], y=total_vol,
                name='Total Vol',
                marker=dict(color='rgba(16, 185, 129, 0.85)', line=dict(color='#10B981', width=1)),
            ),
            secondary_y=False,
        )

    fig_intra.add_trace(
        go.Scatter(
            x=frame_data['Strike'], y=frame_data['Vol Settle'],
            name='Vol Settle', mode='lines+markers',
            line=dict(color='#EF4444', width=3, shape='spline'),
            marker=dict(size=6, color='#EF4444'),
        ),
        secondary_y=True,
    )

    # ── Vertical lines ──
    if atm_intra:
        add_atm_vline(fig_intra, atm_intra)
    if lo_exp_i and hi_exp_i:
        add_theta_breakeven_vlines(fig_intra, lo_exp_i, hi_exp_i, lo_day_i, hi_day_i)
    add_gex_vlines(fig_intra, gex_flip_i, pos_wall_i, neg_wall_i, label="γ-Flow")
    if gex_peak_i is not None:
        fig_intra.add_vline(
            x=gex_peak_i, line_dash="dot", line_color="#C084FC",
            line_width=1.5, opacity=0.7,
            annotation_text="γ-Flow Peak",
            annotation_position="top right",
            annotation_font=dict(color="#C084FC", size=10),
        )

    fig_intra.update_layout(
        barmode='group', bargap=0.15, height=500,
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.05, xanchor="center", x=0.5),
        margin=dict(l=10, r=10, t=10, b=10),
    )
    fig_intra.update_xaxes(title_text="Strike Price", showgrid=True, gridcolor='rgba(128,128,128,0.2)')
    fig_intra.update_yaxes(title_text="Volume",     secondary_y=False, showgrid=True,  gridcolor='rgba(128,128,128,0.2)')
    fig_intra.update_yaxes(title_text="Volatility", secondary_y=True,  showgrid=False)
    st.plotly_chart(fig_intra, use_container_width=True)

    # ── Hoverable Thai legend ──
    render_line_legend()

    # ── γ-Flow / Breakeven info row ──
    if gex_flip_i or gex_peak_i or lo_exp_i:
        mc1, mc2, mc3, mc4, mc5 = st.columns(5)
        with mc1:
            if gex_flip_i:
                st.metric("🟣 γ-Flow Flip (B76)", f"{gex_flip_i:,.1f}")
            elif gex_peak_i:
                st.metric("🟣 γ-Flow Peak (B76)", f"{gex_peak_i:,.1f}")
        with mc2:
            if pos_wall_i:
                st.metric("🟢 +γ-Flow Wall", f"{pos_wall_i:,.0f}")
        with mc3:
            if neg_wall_i:
                st.metric("🔴 −γ-Flow Wall", f"{neg_wall_i:,.0f}")
        with mc4:
            if lo_exp_i and hi_exp_i:
                st.metric("🟠 γ/θ Expiry Range",
                          f"{lo_exp_i:,.1f} – {hi_exp_i:,.1f}")
        with mc5:
            if lo_day_i and hi_day_i:
                st.metric("🟡 γ/θ Daily Range",
                          f"{lo_day_i:,.1f} – {hi_day_i:,.1f}")

    # ── Vanna & Volga metrics ──
    if net_vanna_i != 0 or net_volga_i != 0:
        vc1, vc2 = st.columns(2)
        with vc1:
            _vanna_dir = "Bullish Shift" if net_vanna_i > 0 else "Bearish Shift" if net_vanna_i < 0 else "Neutral"
            st.metric("🔵 Net Vanna (γ-Flow)", f"{net_vanna_i:,.2f}",
                      delta=_vanna_dir, delta_color="normal")
        with vc2:
            _volga_eff = "Widen BE" if net_volga_i > 0 else "Narrow BE" if net_volga_i < 0 else "Neutral"
            st.metric("🟣 Net Volga (γ-Flow)", f"{net_volga_i:,.2f}",
                      delta=_volga_eff, delta_color="off")

    # ── Timeline controls ──
    col_play, col_slider = st.columns([1, 10])

    with col_play:
        if st.session_state.is_playing:
            if st.button(":material/pause: Pause", use_container_width=True):
                st.session_state.is_playing = False
                st.session_state.focus_slider = True
                st.rerun()
        else:
            if st.button(":material/play_arrow: Play", use_container_width=True):
                st.session_state.is_playing = True
                current_idx = list(available_times).index(st.session_state.selected_time_state)
                if current_idx == len(available_times) - 1:
                    st.session_state.anim_idx = 0
                else:
                    st.session_state.anim_idx = current_idx
                st.session_state.selected_time_state = available_times[st.session_state.anim_idx]
                st.rerun()

    with col_slider:
        st.select_slider(
            "Timeline",
            options=available_times,
            key="selected_time_state",
            label_visibility="collapsed",
        )

    if st.session_state.focus_slider:
        components.html(
            """
            <script>
                const sliders = window.parent.document.querySelectorAll('div[role="slider"]');
                if (sliders.length > 0) { sliders[0].focus(); }
            </script>
            """,
            height=0, width=0,
        )
        st.session_state.focus_slider = False

    st.markdown("---")
    st.markdown("### :material/analytics: Intraday Volume Data")

    table_df_intra = frame_data[['Strike', 'Call', 'Put', 'Vol Settle']].copy()
    table_df_intra['Total Vol'] = table_df_intra['Call'] + table_df_intra['Put']
    table_df_intra = table_df_intra[['Strike', 'Call', 'Put', 'Total Vol', 'Vol Settle']]

    st.dataframe(
        table_df_intra,
        column_config={
            "Strike":    st.column_config.NumberColumn("Strike Price", format="%d"),
            "Call":      st.column_config.ProgressColumn("Call Volume",  format="%d", min_value=0, max_value=int(table_df_intra['Call'].max())      if not table_df_intra.empty else 100),
            "Put":       st.column_config.ProgressColumn("Put Volume",   format="%d", min_value=0, max_value=int(table_df_intra['Put'].max())       if not table_df_intra.empty else 100),
            "Total Vol": st.column_config.ProgressColumn("Total Vol",    format="%d", min_value=0, max_value=int(table_df_intra['Total Vol'].max()) if not table_df_intra.empty else 100),
            "Vol Settle":st.column_config.NumberColumn("Vol Settle", format="%.2f"),
        },
        hide_index=True, use_container_width=True, height=800,
    )

    # ── γ-Flow Table ──
    if gex_df_i is not None and not gex_df_i.empty:
        st.markdown("---")
        st.markdown(
            "### :material/ssid_chart: γ-Flow — Gamma-Weighted Volume Flow (Black-76)"
        )
        st.caption(
            "⚠ ใช้ Intraday Volume (ไม่ใช่ Open Interest) — แสดง **Gamma × Volume Flow** "
            "ไม่ใช่ Gamma Exposure (GEX) ที่ใช้ OI ของ Dealer"
        )
        gex_tbl_i = gex_df_i[['Strike', 'Call', 'Put', 'IV %', 'Gamma', 'Net_GEX', 'Cumulative_GEX']].copy()
        gex_tbl_i = gex_tbl_i.rename(columns={
            'Net_GEX': 'Net γ-Flow',
            'Cumulative_GEX': 'Σ γ-Flow',
        })
        st.dataframe(
            gex_tbl_i,
            column_config={
                "Strike":      st.column_config.NumberColumn("Strike", format="%d"),
                "Call":        st.column_config.NumberColumn("Call Vol", format="%d"),
                "Put":         st.column_config.NumberColumn("Put Vol", format="%d"),
                "IV %":        st.column_config.NumberColumn("IV %", format="%.2f"),
                "Gamma":       st.column_config.NumberColumn("Γ (B76)", format="%.6e"),
                "Net γ-Flow":  st.column_config.NumberColumn("Net γ-Flow", format="%.2f"),
                "Σ γ-Flow":    st.column_config.NumberColumn("Σ γ-Flow", format="%.2f"),
            },
            hide_index=True, use_container_width=True, height=500,
        )

    # ── Gamma-Theta Breakeven Range Table ──
    if atm_intra and dte_intra and iv_atm_i:
        st.markdown("---")
        st.markdown(
            "### :material/balance: γ/θ Breakeven Range (Black-76)"
        )
        be_data_i = {
            "Metric": [
                "Futures (ATM)",
                "ATM IV (σ)",
                "DTE",
                "T (years)",
                "γ/θ Daily ΔF = F·σ/√365",
                "γ/θ Daily Range",
                "γ/θ Expiry ΔF = F·σ·√T",
                "γ/θ Expiry Range",
            ],
            "Value": [
                f"{atm_intra:,.1f}",
                f"{iv_atm_i * 100:.2f} %",
                f"{dte_intra:.2f}",
                f"{dte_intra / 365:.6f}",
                f"± {atm_intra * iv_atm_i / math.sqrt(365):.1f}",
                f"{lo_day_i:,.1f} – {hi_day_i:,.1f}" if lo_day_i else "N/A",
                f"± {atm_intra * iv_atm_i * math.sqrt(dte_intra / 365):.1f}",
                f"{lo_exp_i:,.1f} – {hi_exp_i:,.1f}" if lo_exp_i else "N/A",
            ],
        }
        st.dataframe(
            pd.DataFrame(be_data_i),
            hide_index=True, use_container_width=True,
        )

    # ── Animation auto-advance ──
    if st.session_state.is_playing:
        time.sleep(0.6)
        st.session_state.anim_idx += 1
        if st.session_state.anim_idx < len(available_times):
            st.rerun()
        else:
            st.session_state.is_playing = False
            st.rerun()
