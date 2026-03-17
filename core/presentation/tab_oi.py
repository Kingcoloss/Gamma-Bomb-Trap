"""
Tab 3 — Open Interest (OI)
===========================
Renders the Open Interest / GEX analysis tab.
"""
import math

import pandas as pd
import numpy as np
import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from core.use_cases.gex_analysis import calculate_gex_analysis, get_atm_iv
from core.use_cases.gtbr import (
    calculate_gamma_theta_breakeven,
    calculate_vanna_adjusted_gtbr,
)
from core.use_cases.data_helpers import extract_atm, extract_dte
from core.domain.constants import DELTA_IV_CAP
from core.presentation.styles import get_styled_header
from core.presentation.chart_helpers import (
    add_atm_vline,
    add_theta_breakeven_vlines,
    add_gex_vlines,
)
from core.presentation.legend import render_line_legend


def render_oi_tab(df_oi: pd.DataFrame, chart_mode: str, df_intraday: pd.DataFrame | None = None):
    """Render the Open Interest tab content."""
    if df_oi.empty:
        return

    latest_oi = (
        df_oi[df_oi['Datetime'] == df_oi['Datetime'].max()]
        .copy()
        .sort_values('Strike')
    )
    if latest_oi['Vol Settle'].max() < 1:
        latest_oi['Vol Settle'] = (latest_oi['Vol Settle'] * 100).round(2)

    h1_oi  = latest_oi['Header1'].iloc[0]
    h2_oi  = latest_oi['Header2'].iloc[0]
    atm_oi = extract_atm(h1_oi)
    dte_oi = extract_dte(h1_oi)

    st.markdown(get_styled_header(h1_oi, h2_oi), unsafe_allow_html=True)

    # ── Compute GEX & breakeven for OI data ──
    oi_raw = (
        df_oi[df_oi['Datetime'] == df_oi['Datetime'].max()]
        .copy()
        .sort_values('Strike')
    )
    gex_flip_o = pos_wall_o = neg_wall_o = gex_peak_o = None
    gex_df_o = None
    lo_exp_o = hi_exp_o = lo_day_o = hi_day_o = None
    iv_atm_o = None
    net_vanna_o = net_volga_o = 0.0
    net_gamma_o = net_theta_o = 0.0
    va_ld_o = va_hd_o = va_le_o = va_he_o = None
    v_shift_d_o = 0.0
    dgc_o = None

    if atm_oi and dte_oi:
        iv_atm_o = get_atm_iv(oi_raw, atm_oi)
        if iv_atm_o and dte_oi > 0:
            result = calculate_gex_analysis(
                oi_raw, atm_oi, dte_oi, data_mode="OI"
            )
            gex_flip_o = result.flip
            pos_wall_o = result.pos_wall
            neg_wall_o = result.neg_wall
            gex_df_o = result.gex_df
            gex_peak_o = result.peak
            net_vanna_o = result.net_vanna_total
            net_volga_o = result.net_volga_total
            net_gamma_o = result.net_gamma_total
            net_theta_o = result.net_theta_total

            gtbr = calculate_gamma_theta_breakeven(atm_oi, iv_atm_o, dte_oi)
            lo_exp_o = gtbr.lo_expiry
            hi_exp_o = gtbr.hi_expiry
            lo_day_o = gtbr.lo_daily
            hi_day_o = gtbr.hi_daily

            # ── Vanna-Volga Adjusted GTBR + DGC ──
            _delta_iv_o = 0.0
            if df_intraday is not None and not df_intraday.empty:
                _intra_snap = df_intraday[
                    df_intraday['Time'] == st.session_state.selected_time_state
                ].copy()
                if not _intra_snap.empty:
                    _iv_intra = get_atm_iv(_intra_snap, atm_oi)
                    if _iv_intra and iv_atm_o:
                        _raw_d = _iv_intra - iv_atm_o
                        _delta_iv_o = max(
                            -DELTA_IV_CAP, min(DELTA_IV_CAP, _raw_d)
                        )

            vgtbr_o = calculate_vanna_adjusted_gtbr(
                atm_oi, iv_atm_o, dte_oi,
                net_vanna_o, net_volga_o, _delta_iv_o,
                net_gamma=net_gamma_o or None,
                net_theta=net_theta_o or None,
            )
            va_ld_o = vgtbr_o.lo_daily
            va_hd_o = vgtbr_o.hi_daily
            va_le_o = vgtbr_o.lo_expiry
            va_he_o = vgtbr_o.hi_expiry
            v_shift_d_o = vgtbr_o.shift_daily
            dgc_o = (va_ld_o + va_hd_o) / 2.0

    # ── Build chart ──
    fig_oi = make_subplots(specs=[[{"secondary_y": True}]])

    if chart_mode == "Call / Put Vol":
        fig_oi.add_trace(
            go.Bar(
                x=latest_oi['Strike'], y=latest_oi['Put'],
                name='Put OI',
                marker=dict(color='rgba(245, 158, 11, 0.85)', line=dict(color='#F59E0B', width=1)),
            ),
            secondary_y=False,
        )
        fig_oi.add_trace(
            go.Bar(
                x=latest_oi['Strike'], y=latest_oi['Call'],
                name='Call OI',
                marker=dict(color='rgba(59, 130, 246, 0.85)', line=dict(color='#3B82F6', width=1)),
            ),
            secondary_y=False,
        )
    else:
        total_oi = latest_oi['Call'] + latest_oi['Put']
        fig_oi.add_trace(
            go.Bar(
                x=latest_oi['Strike'], y=total_oi,
                name='Total OI',
                marker=dict(color='rgba(16, 185, 129, 0.85)', line=dict(color='#10B981', width=1)),
            ),
            secondary_y=False,
        )

    fig_oi.add_trace(
        go.Scatter(
            x=latest_oi['Strike'], y=latest_oi['Vol Settle'],
            name='Vol Settle', mode='lines+markers',
            line=dict(color='#EF4444', width=3, shape='spline'),
            marker=dict(size=6, color='#EF4444'),
        ),
        secondary_y=True,
    )

    # ── Vertical lines ──
    if atm_oi:
        add_atm_vline(fig_oi, atm_oi)
    if lo_exp_o and hi_exp_o:
        add_theta_breakeven_vlines(fig_oi, lo_exp_o, hi_exp_o, lo_day_o, hi_day_o)
    add_gex_vlines(fig_oi, gex_flip_o, pos_wall_o, neg_wall_o)
    if gex_peak_o is not None:
        fig_oi.add_vline(
            x=gex_peak_o, line_dash="dot", line_color="#C084FC",
            line_width=1.5, opacity=0.7,
            annotation_text="GEX Peak",
            annotation_position="top right",
            annotation_font=dict(color="#C084FC", size=10),
        )

    fig_oi.update_layout(
        barmode='group', bargap=0.15, height=500,
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.05, xanchor="center", x=0.5),
        margin=dict(l=10, r=10, t=10, b=10),
    )
    fig_oi.update_xaxes(title_text="Strike Price", showgrid=True, gridcolor='rgba(128,128,128,0.2)')
    fig_oi.update_yaxes(title_text="Open Interest", secondary_y=False, showgrid=True,  gridcolor='rgba(128,128,128,0.2)')
    fig_oi.update_yaxes(title_text="Volatility",    secondary_y=True,  showgrid=False)
    st.plotly_chart(fig_oi, use_container_width=True)

    # ── Hoverable Thai legend ──
    render_line_legend()

    # ── GEX / Breakeven info row ──
    if gex_flip_o or gex_peak_o or lo_exp_o:
        mc1, mc2, mc3, mc4, mc5 = st.columns(5)
        with mc1:
            if gex_flip_o:
                st.metric("🟣 GEX Flip (B76)", f"{gex_flip_o:,.1f}")
            elif gex_peak_o:
                st.metric("🟣 GEX Peak (B76)", f"{gex_peak_o:,.1f}")
        with mc2:
            if pos_wall_o:
                st.metric("🟢 +GEX Wall", f"{pos_wall_o:,.0f}")
        with mc3:
            if neg_wall_o:
                st.metric("🔴 −GEX Wall", f"{neg_wall_o:,.0f}")
        with mc4:
            if lo_exp_o and hi_exp_o:
                st.metric("🟠 γ/θ Expiry Range",
                          f"{lo_exp_o:,.1f} – {hi_exp_o:,.1f}")
        with mc5:
            if lo_day_o and hi_day_o:
                st.metric("🟡 γ/θ Daily Range",
                          f"{lo_day_o:,.1f} – {hi_day_o:,.1f}")

    # ── Vanna & Volga metrics ──
    if net_vanna_o != 0 or net_volga_o != 0:
        vc1, vc2 = st.columns(2)
        with vc1:
            _vanna_dir_o = "Bullish Shift" if net_vanna_o > 0 else "Bearish Shift" if net_vanna_o < 0 else "Neutral"
            st.metric("🔵 Net Vanna (OI)", f"{net_vanna_o:,.2f}",
                      delta=_vanna_dir_o, delta_color="normal")
        with vc2:
            _volga_eff_o = "Widen BE" if net_volga_o > 0 else "Narrow BE" if net_volga_o < 0 else "Neutral"
            st.metric("🟣 Net Volga (OI)", f"{net_volga_o:,.2f}",
                      delta=_volga_eff_o, delta_color="off")

    st.markdown("---")
    st.markdown("### :material/analytics: OI Volume Data")
    table_df_oi = latest_oi[['Strike', 'Call', 'Put', 'Vol Settle']].copy()
    table_df_oi['Total OI'] = table_df_oi['Call'] + table_df_oi['Put']
    table_df_oi = table_df_oi[['Strike', 'Call', 'Put', 'Total OI', 'Vol Settle']]

    st.dataframe(
        table_df_oi,
        column_config={
            "Strike":    st.column_config.NumberColumn("Strike Price", format="%d"),
            "Call":      st.column_config.ProgressColumn("Call OI",  format="%d", min_value=0, max_value=int(table_df_oi['Call'].max())      if not table_df_oi.empty else 100),
            "Put":       st.column_config.ProgressColumn("Put OI",   format="%d", min_value=0, max_value=int(table_df_oi['Put'].max())       if not table_df_oi.empty else 100),
            "Total OI":  st.column_config.ProgressColumn("Total OI",    format="%d", min_value=0, max_value=int(table_df_oi['Total OI'].max()) if not table_df_oi.empty else 100),
            "Vol Settle":st.column_config.NumberColumn("Vol Settle", format="%.2f"),
        },
        hide_index=True, use_container_width=True, height=800,
    )

    # ── GEX Table ──
    if gex_df_o is not None and not gex_df_o.empty:
        st.markdown("---")
        st.markdown(
            "### :material/ssid_chart: GEX — Gamma Exposure per Strike (Black-76)"
        )
        st.caption(
            "ใช้ Open Interest (ตำแหน่ง Dealer) — แสดง **Net Gamma Exposure** "
            "ตามสูตร: Net GEX_K = Γ_B76(F,K,T,σ) × (Call_OI − Put_OI) × F² × 0.01"
        )
        gex_tbl_o = gex_df_o[['Strike', 'Call', 'Put', 'IV %', 'Gamma', 'Net_GEX', 'Cumulative_GEX']].copy()
        gex_tbl_o = gex_tbl_o.rename(columns={
            'Net_GEX': 'Net GEX',
            'Cumulative_GEX': 'Σ GEX',
        })
        st.dataframe(
            gex_tbl_o,
            column_config={
                "Strike":   st.column_config.NumberColumn("Strike", format="%d"),
                "Call":     st.column_config.NumberColumn("Call OI", format="%d"),
                "Put":      st.column_config.NumberColumn("Put OI", format="%d"),
                "IV %":     st.column_config.NumberColumn("IV %", format="%.2f"),
                "Gamma":    st.column_config.NumberColumn("Γ (B76)", format="%.6e"),
                "Net GEX":  st.column_config.NumberColumn("Net GEX", format="%.2f"),
                "Σ GEX":    st.column_config.NumberColumn("Σ GEX", format="%.2f"),
            },
            hide_index=True, use_container_width=True, height=500,
        )

    # ── GTBR Table ──
    if atm_oi and dte_oi and iv_atm_o:
        st.markdown("---")
        st.markdown(
            "### :material/balance: γ/θ Breakeven Range (Black-76)"
        )
        be_data_o = {
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
                f"{atm_oi:,.1f}",
                f"{iv_atm_o * 100:.2f} %",
                f"{dte_oi:.2f}",
                f"{dte_oi / 365:.6f}",
                f"± {atm_oi * iv_atm_o / math.sqrt(365):.1f}",
                f"{lo_day_o:,.1f} – {hi_day_o:,.1f}" if lo_day_o else "N/A",
                f"± {atm_oi * iv_atm_o * math.sqrt(dte_oi / 365):.1f}",
                f"{lo_exp_o:,.1f} – {hi_exp_o:,.1f}" if lo_exp_o else "N/A",
            ],
        }
        st.dataframe(
            pd.DataFrame(be_data_o),
            hide_index=True, use_container_width=True,
        )
