"""
Tab 1 — GBT Composite Analysis
===============================
Renders the GBT (Gamma Bomb Trap) composite GEX analysis tab combining
Open Interest (structural dealer positions) and Intraday Volume (market activity).
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
from core.presentation.styles import get_styled_header
from core.presentation.legend import render_line_legend
from core.domain.constants import (
    BLOCK_TRADE_THRESHOLD,
    WALL_CONVERGENCE_TOLERANCE,
    DELTA_IV_CAP,
)


def render_gbt_tab(df_intraday: pd.DataFrame, df_oi: pd.DataFrame, chart_mode: str):
    """
    Render the GBT Composite Analysis tab.

    Combines Open Interest (structural dealer positions) and Intraday Volume
    (market activity) into a composite GEX signal, with block detection,
    convergence analysis, and Vanna-Volga adjusted GTBR.

    Parameters
    ----------
    df_intraday : pd.DataFrame
        Intraday Volume data from CME feed
    df_oi : pd.DataFrame
        Open Interest data from CME feed
    chart_mode : str
        Chart mode selection (passed but not currently used in this tab)
    """
    if df_intraday.empty or df_oi.empty:
        st.warning(
            "⚠ ต้องมีข้อมูลทั้ง **Intraday Volume** และ **Open Interest** "
            "เพื่อวิเคราะห์ GBT — กรุณา Refresh"
        )
        return

    # ── Latest snapshots ──
    _vol_snap = (
        df_intraday[
            df_intraday['Time'] == st.session_state.selected_time_state
        ].copy().sort_values('Strike')
    )
    _oi_snap = (
        df_oi[df_oi['Datetime'] == df_oi['Datetime'].max()]
        .copy().sort_values('Strike')
    )

    if _vol_snap.empty or _oi_snap.empty:
        st.warning("⚠ ไม่พบข้อมูลที่ตรงกัน กรุณา Refresh")
        return

    # ── ATM / DTE ──
    _h1_v = _vol_snap['Header1'].iloc[0]
    _h1_o = _oi_snap['Header1'].iloc[0]
    _atm_v = extract_atm(_h1_v)
    _atm_o = extract_atm(_h1_o)
    _dte_v = extract_dte(_h1_v)
    _dte_o = extract_dte(_h1_o)

    # v5 FIX: prefer Intraday DTE (fresher) for all Greeks
    _dte = _dte_v if _dte_v and _dte_v > 0 else _dte_o
    _atm = _atm_v if _atm_v else _atm_o

    if not _atm or not _dte:
        st.error("❌ ไม่สามารถดึง ATM/DTE จาก header ได้")
        return

    # ── Styled header ──
    st.markdown(get_styled_header(
        f"GBT Composite — ATM {_atm:,.1f}  |  "
        f"DTE {_dte:.2f} (Intraday)",
        f"OI: {_h1_o}  •  Vol: {_h1_v}",
    ), unsafe_allow_html=True)

    # ── Alpha slider ──
    _alpha = st.slider(
        "α — Intraday Volume Weight  "
        "(0 = OI only · 0.4 = recommended · 1 = Vol only)",
        0.0, 1.0, 0.4, 0.05,
        key="gbt_alpha",
    )
    _block_thr = BLOCK_TRADE_THRESHOLD

    # ── Compute both GEX layers with SAME DTE ──
    _iv_v = get_atm_iv(_vol_snap, _atm)
    _iv_o = get_atm_iv(_oi_snap, _atm)
    _iv_comp = _iv_v if _iv_v else _iv_o

    _gf_v = _pw_v = _nw_v = _pk_v = None
    _gdf_v = None
    _nva_v = _nvg_v = 0.0
    if _iv_v:
        result_v = calculate_gex_analysis(_vol_snap, _atm, _dte, "Intraday")
        _gf_v = result_v.flip
        _pw_v = result_v.pos_wall
        _nw_v = result_v.neg_wall
        _gdf_v = result_v.gex_df
        _pk_v = result_v.peak
        _nva_v = result_v.net_vanna_total
        _nvg_v = result_v.net_volga_total

    _gf_o = _pw_o = _nw_o = _pk_o = None
    _gdf_o = None
    _nva_o = _nvg_o = 0.0
    if _iv_o:
        result_o = calculate_gex_analysis(_oi_snap, _atm, _dte, "OI")
        _gf_o = result_o.flip
        _pw_o = result_o.pos_wall
        _nw_o = result_o.neg_wall
        _gdf_o = result_o.gex_df
        _pk_o = result_o.peak
        _nva_o = result_o.net_vanna_total
        _nvg_o = result_o.net_volga_total

    # ── Build composite per-strike table ──
    _rows = []
    if _gdf_o is not None and _gdf_v is not None:
        _m_oi = _gdf_o.set_index('Strike')
        _m_vol = _gdf_v.set_index('Strike')
        _all_K = sorted(
            set(_m_oi.index.tolist()
                + _m_vol.index.tolist())
        )
        for K in _all_K:
            g_oi = float(_m_oi.loc[K, 'Net_GEX']) if K in _m_oi.index else 0.0
            g_vol = float(_m_vol.loc[K, 'Net_GEX']) if K in _m_vol.index else 0.0
            comp = (1 - _alpha) * g_oi + _alpha * g_vol

            c_oi = float(_m_oi.loc[K, 'Call']) if K in _m_oi.index else 0
            p_oi = float(_m_oi.loc[K, 'Put']) if K in _m_oi.index else 0
            c_vol = float(_m_vol.loc[K, 'Call']) if K in _m_vol.index else 0
            p_vol = float(_m_vol.loc[K, 'Put']) if K in _m_vol.index else 0

            is_block = (
                abs(g_oi) > 0
                and abs(g_vol / g_oi) >= _block_thr
            )

            _rows.append({
                'Strike': K,
                'Call_OI': c_oi, 'Put_OI': p_oi,
                'Call_Vol': c_vol, 'Put_Vol': p_vol,
                'GEX_OI': g_oi,
                'γ_Flow': g_vol,
                'Composite': comp,
                'Block': is_block,
            })

    _cdf = pd.DataFrame(_rows)

    if _cdf.empty:
        st.warning(
            "⚠ ไม่สามารถสร้าง Composite GEX ได้ "
            "— ตรวจสอบข้อมูล OI/Vol"
        )
        return

    _cdf = _cdf.sort_values('Strike').reset_index(drop=True)
    _cdf['Cumulative'] = _cdf['Composite'].cumsum()

    # ── Composite Flip ──
    # Collect ALL zero-crossings then pick nearest to ATM
    # (mirrors gex_analysis.py:96-110 pattern exactly)
    _all_comp_crossings = []
    for i in range(1, len(_cdf)):
        _p = _cdf.loc[i-1, 'Cumulative']
        _c = _cdf.loc[i,   'Cumulative']
        if _p * _c <= 0 and not (_p == 0 and _c == 0):
            _d = abs(_p) + abs(_c)
            _w = abs(_p) / _d if _d > 0 else 0.5
            _all_comp_crossings.append(
                _cdf.loc[i-1, 'Strike']
                + _w * (_cdf.loc[i, 'Strike']
                        - _cdf.loc[i-1, 'Strike'])
            )

    _c_flip = (
        min(_all_comp_crossings, key=lambda x: abs(x - _atm))
        if _all_comp_crossings else None
    )

    # ── Composite Walls ──
    _c_pw = (
        _cdf.loc[_cdf['Composite'].idxmax(), 'Strike']
        if _cdf['Composite'].max() > 0 else None
    )
    _c_nw = (
        _cdf.loc[_cdf['Composite'].idxmin(), 'Strike']
        if _cdf['Composite'].min() < 0 else None
    )

    # ── Net regime ──
    _net = _cdf['Composite'].sum()
    _regime = (
        "LONG γ — Mean-Revert"
        if _net >= 0
        else "SHORT γ — Trend-Follow"
    )

    # ── GTBR + Vanna/Volga-Adjusted GTBR ──
    _le = _he = _ld = _hd = None
    _va_ld = _va_hd = _va_le = _va_he = None
    _v_shift_d = _v_shift_e = 0.0
    # Reuse Net Vanna/Volga already computed by
    # calculate_gex_analysis (OI-based for dealer hedging)
    _net_vanna = _nva_o
    _net_volga = _nvg_o

    if _iv_comp and _dte > 0:
        # Standard GTBR (baseline)
        gtbr_result = calculate_gamma_theta_breakeven(_atm, _iv_comp, _dte)
        _le = gtbr_result.lo_expiry
        _he = gtbr_result.hi_expiry
        _ld = gtbr_result.lo_daily
        _hd = gtbr_result.hi_daily

        # Estimate daily IV change from
        # IV skew slope (OI vs Vol IV difference)
        _delta_iv = 0.0
        if _iv_v and _iv_o:
            _raw_delta_iv = _iv_v - _iv_o
            _delta_iv = max(-DELTA_IV_CAP, min(DELTA_IV_CAP, _raw_delta_iv))

        # Vanna + Volga Adjusted GTBR
        vgtbr_result = calculate_vanna_adjusted_gtbr(
            _atm, _iv_comp, _dte,
            _net_vanna, _net_volga, _delta_iv,
        )
        _va_ld = vgtbr_result.lo_daily
        _va_hd = vgtbr_result.hi_daily
        _va_le = vgtbr_result.lo_expiry
        _va_he = vgtbr_result.hi_expiry
        _v_shift_d = vgtbr_result.shift_daily
        _v_shift_e = vgtbr_result.shift_expiry

    # ── Block count ──
    _n_blocks = int(_cdf['Block'].sum())

    # ── Convergence ──
    _conv = []
    if _pw_o and _pw_v:
        if abs(_pw_o - _pw_v) <= WALL_CONVERGENCE_TOLERANCE:
            _conv.append(
                "✅ +Wall converged → "
                "high-conviction resistance"
            )
        else:
            _conv.append(
                f"⚠ +Wall diverge: "
                f"OI {_pw_o:.0f} vs Vol {_pw_v:.0f}"
            )
    if _nw_o and _nw_v:
        if abs(_nw_o - _nw_v) <= WALL_CONVERGENCE_TOLERANCE:
            _conv.append(
                "✅ −Wall converged → "
                "high-conviction support"
            )
        else:
            _conv.append(
                f"⚠ −Wall diverge: "
                f"OI {_nw_o:.0f} vs Vol {_nw_v:.0f}"
            )

    # ═════════════════════════════════════
    #  CHART: 2-row subplot
    # ═════════════════════════════════════
    _fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        row_heights=[0.65, 0.35],
        vertical_spacing=0.06,
        subplot_titles=(
            "Composite GEX per Strike",
            "Cumulative Composite GEX",
        ),
    )

    # Row 1 — bars + composite line
    _fig.add_trace(go.Bar(
        x=_cdf['Strike'], y=_cdf['GEX_OI'],
        name='GEX (OI)',
        marker=dict(color=[
            'rgba(34,197,94,0.45)' if v >= 0
            else 'rgba(239,68,68,0.45)'
            for v in _cdf['GEX_OI']
        ]),
        opacity=0.75,
    ), row=1, col=1)

    _fig.add_trace(go.Bar(
        x=_cdf['Strike'], y=_cdf['γ_Flow'],
        name='γ-Flow (Vol)',
        marker=dict(color=[
            'rgba(59,130,246,0.55)' if v >= 0
            else 'rgba(251,146,60,0.55)'
            for v in _cdf['γ_Flow']
        ]),
        opacity=0.75,
    ), row=1, col=1)

    _fig.add_trace(go.Scatter(
        x=_cdf['Strike'],
        y=_cdf['Composite'],
        name=f'Composite (α={_alpha:.2f})',
        mode='lines+markers',
        line=dict(color='#FBBF24', width=2.5),
        marker=dict(size=4),
    ), row=1, col=1)

    # Block markers
    _blk = _cdf[_cdf['Block']]
    if not _blk.empty:
        _fig.add_trace(go.Scatter(
            x=_blk['Strike'],
            y=_blk['Composite'],
            name='Block Trade',
            mode='markers',
            marker=dict(
                symbol='diamond',
                size=10,
                color='#E879F9',
                line=dict(width=1, color='white'),
            ),
        ), row=1, col=1)

    # Row 2 — cumulative fill
    _fig.add_trace(go.Scatter(
        x=_cdf['Strike'],
        y=_cdf['Cumulative'],
        name='Σ Composite',
        fill='tozeroy',
        line=dict(color='#A855F7', width=2),
        fillcolor='rgba(168,85,247,0.15)',
    ), row=2, col=1)

    # ── Reference lines on both rows ──
    for _r in [1, 2]:
        _fig.add_vline(
            x=_atm, line_dash="dash",
            line_color="#888", opacity=0.8,
            row=_r, col=1,
            annotation_text="ATM" if _r == 1 else None,
            annotation_position="top",
        )
        if _le and _he:
            for _xv, _lb in [
                (_le, "GTBR↓"), (_he, "GTBR↑"),
            ]:
                _fig.add_vline(
                    x=_xv, line_dash="dash",
                    line_color="#FB923C",
                    line_width=2, opacity=0.85,
                    row=_r, col=1,
                    annotation_text=(
                        _lb if _r == 1 else None
                    ),
                    annotation_font=dict(
                        color="#FB923C", size=9),
                )
        if _ld and _hd:
            for _xv, _lb in [
                (_ld, "1D↓"), (_hd, "1D↑"),
            ]:
                _fig.add_vline(
                    x=_xv, line_dash="dot",
                    line_color="#FCD34D",
                    line_width=1.5, opacity=0.7,
                    row=_r, col=1,
                    annotation_text=(
                        _lb if _r == 1 else None
                    ),
                    annotation_font=dict(
                        color="#FCD34D", size=8),
                )
        # ── Vanna-Adjusted GTBR (cyan/teal) ──
        if _va_le and _va_he:
            for _xv, _lb in [
                (_va_le, "V-GTBR↓"),
                (_va_he, "V-GTBR↑"),
            ]:
                _fig.add_vline(
                    x=_xv, line_dash="dashdot",
                    line_color="#06B6D4",
                    line_width=2, opacity=0.8,
                    row=_r, col=1,
                    annotation_text=(
                        _lb if _r == 1 else None
                    ),
                    annotation_font=dict(
                        color="#06B6D4", size=9),
                )
        if _va_ld and _va_hd:
            for _xv, _lb in [
                (_va_ld, "V-1D↓"),
                (_va_hd, "V-1D↑"),
            ]:
                _fig.add_vline(
                    x=_xv, line_dash="dot",
                    line_color="#2DD4BF",
                    line_width=1.5, opacity=0.65,
                    row=_r, col=1,
                    annotation_text=(
                        _lb if _r == 1 else None
                    ),
                    annotation_font=dict(
                        color="#2DD4BF", size=8),
                )
        if _c_flip:
            _fig.add_vline(
                x=_c_flip, line_dash="dot",
                line_color="#A855F7",
                line_width=2, opacity=0.9,
                row=_r, col=1,
                annotation_text=(
                    "Flip" if _r == 2 else None
                ),
                annotation_font=dict(
                    color="#A855F7", size=10),
            )
        if _c_pw:
            _fig.add_vline(
                x=_c_pw, line_dash="dashdot",
                line_color="#22C55E",
                line_width=1.5, opacity=0.7,
                row=_r, col=1,
                annotation_text=(
                    "+Wall" if _r == 1 else None
                ),
                annotation_font=dict(
                    color="#22C55E", size=9),
            )
        if _c_nw:
            _fig.add_vline(
                x=_c_nw, line_dash="dashdot",
                line_color="#F43F5E",
                line_width=1.5, opacity=0.7,
                row=_r, col=1,
                annotation_text=(
                    "−Wall" if _r == 1 else None
                ),
                annotation_font=dict(
                    color="#F43F5E", size=9),
            )

    _fig.update_layout(
        barmode='group', bargap=0.15,
        height=700,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        hovermode="x unified",
        legend=dict(
            orientation="h",
            yanchor="bottom", y=1.03,
            xanchor="center", x=0.5,
        ),
        margin=dict(l=10, r=10, t=40, b=10),
    )
    _fig.update_xaxes(
        title_text="Strike Price",
        row=2, col=1,
        showgrid=True,
        gridcolor='rgba(128,128,128,0.2)',
    )
    _fig.update_yaxes(
        title_text="Net GEX / γ-Flow",
        row=1, col=1,
        showgrid=True,
        gridcolor='rgba(128,128,128,0.2)',
    )
    _fig.update_yaxes(
        title_text="Σ Composite",
        row=2, col=1,
        showgrid=True,
        gridcolor='rgba(128,128,128,0.2)',
    )
    st.plotly_chart(
        _fig, use_container_width=True
    )

    # ── Legend ──
    render_line_legend()

    # ═════════════════════════════════════
    #  METRICS DASHBOARD
    # ═════════════════════════════════════
    st.markdown("---")
    st.markdown(
        "### :material/dashboard: "
        "GBT Regime Dashboard"
    )

    m1, m2, m3, m4, m5 = st.columns(5)
    with m1:
        _rcol = (
            "green" if _net >= 0 else "red"
        )
        _rbg = (
            'rgba(34,197,94,0.15)'
            if _net >= 0
            else 'rgba(239,68,68,0.15)'
        )
        st.markdown(
            f"<div style='text-align:center;"
            f"padding:8px;border-radius:8px;"
            f"background:{_rbg};"
            f"border:1px solid {_rcol}'>"
            f"<b style='color:{_rcol};"
            f"font-size:14px'>{_regime}</b>"
            f"<br><span style='font-size:12px;"
            f"color:gray'>"
            f"Net: {_net:,.1f}</span></div>",
            unsafe_allow_html=True,
        )
    with m2:
        st.metric(
            "🟣 Composite Flip",
            f"{_c_flip:,.1f}"
            if _c_flip else "N/A",
        )
    with m3:
        st.metric(
            "🟢 +Wall",
            f"{_c_pw:,.0f}"
            if _c_pw else "—",
        )
    with m4:
        st.metric(
            "🔴 −Wall",
            f"{_c_nw:,.0f}"
            if _c_nw else "—",
        )
    with m5:
        if _le and _he:
            st.metric(
                "🟠 GTBR Expiry",
                f"{_le:,.0f}–{_he:,.0f}",
            )
        elif _ld and _hd:
            st.metric(
                "🟡 GTBR Daily",
                f"{_ld:,.0f}–{_hd:,.0f}",
            )

    # ── Vanna/Volga metrics row ──
    v1, v2, v3, v4, v5 = st.columns(5)
    with v1:
        st.metric(
            "🔷 Net Vanna",
            f"{_net_vanna:,.2f}",
            help="Σ Vanna × (Call−Put) OI — asymmetric shift",
        )
    with v2:
        st.metric(
            "🔶 Net Volga",
            f"{_net_volga:,.2f}",
            help="Σ Volga × (Call+Put) OI — symmetric widening",
        )
    with v3:
        _was_capped = (
            bool(_iv_v and _iv_o)
            and abs(_iv_v - _iv_o) > DELTA_IV_CAP
        )
        _div_str = (
            f"{_delta_iv*100:+.2f}%"
            + (" (capped)" if _was_capped else "")
            if _delta_iv != 0
            else "0 (no IV diff)"
        )
        st.metric(
            "🔷 ΔIV proxy",
            _div_str,
            help="IV_intraday − IV_OI as proxy for expected IV move (capped at ±5%)",
        )
    with v4:
        if _va_ld and _va_hd:
            st.metric(
                "🔹 V-GTBR Daily",
                f"{_va_ld:,.0f}–{_va_hd:,.0f}",
                delta=f"shift {_v_shift_d:+.1f}" if _v_shift_d != 0 else None,
                delta_color="inverse",
            )
    with v5:
        if _va_le and _va_he:
            st.metric(
                "🔹 V-GTBR Expiry",
                f"{_va_le:,.0f}–{_va_he:,.0f}",
                delta=f"shift {_v_shift_e:+.1f}" if _v_shift_e != 0 else None,
                delta_color="inverse",
            )

    # ── Vanna/Volga interpretation ──
    if _net_vanna != 0 and _delta_iv != 0:
        _vanna_dir = (
            "downside" if _net_vanna * _delta_iv > 0
            else "upside"
        )
        _vanna_msg = (
            f"**Vanna** shifts GTBR toward **{_vanna_dir}** "
            f"(Vanna={'+'if _net_vanna>0 else ''}{_net_vanna:.2f} × "
            f"ΔIV={_delta_iv*100:+.2f}%)"
        )
        if _net_volga != 0:
            _volga_effect = "widens" if _net_volga * _delta_iv * _delta_iv > 0 else "narrows"
            _vanna_msg += (
                f"  |  **Volga** {_volga_effect} range symmetrically "
                f"(Volga={_net_volga:+.2f} × (Δσ)²)"
            )
        st.caption(f"🔷 **Vol Dimension:** {_vanna_msg}")

    # ── Convergence info ──
    if _conv:
        st.info(
            "**Convergence:**  "
            + "  |  ".join(_conv)
        )

    # ── Block info ──
    if _n_blocks > 0:
        _blk_detail = _cdf[_cdf['Block']][[
            'Strike', 'Call_Vol', 'Put_Vol',
            'γ_Flow', 'GEX_OI',
        ]].copy()
        _blk_detail['Ratio'] = (
            _blk_detail['γ_Flow'].abs()
            / _blk_detail['GEX_OI'].abs()
            .replace(0, np.nan)
        ).round(2)
        st.warning(
            f"🟣 **{_n_blocks} Block Trade(s) "
            f"detected** "
            f"(Vol/OI ratio ≥ {_block_thr}x)"
        )
        st.dataframe(
            _blk_detail,
            hide_index=True,
            use_container_width=True,
        )

    # ═════════════════════════════════════
    #  WALL COMPARISON TABLE
    # ═════════════════════════════════════
    st.markdown("---")
    st.markdown(
        "### :material/compare_arrows: "
        "OI vs Vol — Wall Comparison"
    )
    _wt = {
        "Level": [
            "+GEX Wall (Resistance)",
            "−GEX Wall (Support)",
            "Flip Point",
            "GTBR Daily",
            "GTBR Expiry",
        ],
        "OI": [
            f"{_pw_o:,.0f}" if _pw_o else "—",
            f"{_nw_o:,.0f}" if _nw_o else "—",
            f"{_gf_o:,.1f}" if _gf_o else "—",
            (f"{_ld:,.0f}–{_hd:,.0f}"
             if _ld else "—"),
            (f"{_le:,.0f}–{_he:,.0f}"
             if _le else "—"),
        ],
        "Vol": [
            f"{_pw_v:,.0f}" if _pw_v else "—",
            f"{_nw_v:,.0f}" if _nw_v else "—",
            f"{_gf_v:,.1f}" if _gf_v else "—",
            "=", "=",
        ],
        f"Comp (α={_alpha})": [
            (f"{_c_pw:,.0f}"
             if _c_pw else "—"),
            (f"{_c_nw:,.0f}"
             if _c_nw else "—"),
            (f"{_c_flip:,.1f}"
             if _c_flip else "—"),
            (f"{_ld:,.0f}–{_hd:,.0f}"
             if _ld else "—"),
            (f"{_le:,.0f}–{_he:,.0f}"
             if _le else "—"),
        ],
    }
    st.dataframe(
        pd.DataFrame(_wt),
        hide_index=True,
        use_container_width=True,
    )

    # ═════════════════════════════════════
    #  COMPOSITE DATA TABLE
    # ═════════════════════════════════════
    st.markdown("---")
    st.markdown(
        "### :material/table_chart: "
        "Composite Strike Data"
    )
    st.caption(
        f"Composite = GEX_OI×(1−{_alpha:.2f})"
        f" + γ-Flow×{_alpha:.2f}  |  "
        f"DTE {_dte:.2f} (Intraday)  |  "
        f"Black-76"
    )
    _disp = _cdf[[
        'Strike', 'Call_OI', 'Put_OI',
        'Call_Vol', 'Put_Vol',
        'GEX_OI', 'γ_Flow',
        'Composite', 'Cumulative', 'Block',
    ]].copy()
    _disp.columns = [
        'Strike', 'Call OI', 'Put OI',
        'Call Vol', 'Put Vol',
        'GEX (OI)', 'γ-Flow',
        'Comp GEX', 'Σ Comp', 'Block',
    ]
    st.dataframe(
        _disp,
        column_config={
            "Strike":
                st.column_config.NumberColumn(
                    "Strike", format="%d"),
            "Call OI":
                st.column_config.NumberColumn(
                    "Call OI", format="%d"),
            "Put OI":
                st.column_config.NumberColumn(
                    "Put OI", format="%d"),
            "Call Vol":
                st.column_config.NumberColumn(
                    "Call Vol", format="%d"),
            "Put Vol":
                st.column_config.NumberColumn(
                    "Put Vol", format="%d"),
            "GEX (OI)":
                st.column_config.NumberColumn(
                    "GEX (OI)", format="%.2f"),
            "γ-Flow":
                st.column_config.NumberColumn(
                    "γ-Flow", format="%.2f"),
            "Comp GEX":
                st.column_config.NumberColumn(
                    "Comp GEX", format="%.2f"),
            "Σ Comp":
                st.column_config.NumberColumn(
                    "Σ Comp", format="%.2f"),
            "Block":
                st.column_config.CheckboxColumn(
                    "Block"),
        },
        hide_index=True,
        use_container_width=True,
        height=600,
    )

    # ═════════════════════════════════════
    #  GTBR DETAIL TABLE
    # ═════════════════════════════════════
    if _iv_comp and _dte > 0:
        st.markdown("---")
        st.markdown(
            "### :material/balance: "
            "γ/θ Breakeven Range — Composite"
        )
        _gd = {
            "Metric": [
                "Futures (ATM)",
                "ATM IV (σ) — Intraday",
                "DTE (Intraday)",
                "T (years)",
                "γ/θ Daily ΔF = F·σ/√365",
                "γ/θ Daily Range",
                "γ/θ Expiry ΔF = F·σ·√T",
                "γ/θ Expiry Range",
                "Net Composite GEX",
                "Regime",
                "Blocks Detected",
            ],
            "Value": [
                f"{_atm:,.1f}",
                f"{_iv_comp*100:.2f} %",
                f"{_dte:.2f}",
                f"{_dte/365:.6f}",
                f"± {_atm * _iv_comp / math.sqrt(365):.1f}",
                (f"{_ld:,.1f}–{_hd:,.1f}"
                 if _ld else "N/A"),
                f"± {_atm * _iv_comp * math.sqrt(_dte / 365):.1f}",
                (f"{_le:,.1f}–{_he:,.1f}"
                 if _le else "N/A"),
                f"{_net:,.2f}",
                _regime,
                str(_n_blocks),
            ],
        }
        st.dataframe(
            pd.DataFrame(_gd),
            hide_index=True,
            use_container_width=True,
        )
