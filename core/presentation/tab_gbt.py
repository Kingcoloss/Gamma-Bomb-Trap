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
from core.use_cases.data_helpers import extract_atm, extract_dte, extract_header_vol
from core.presentation.styles import get_styled_header
from core.presentation.legend import render_line_legend
from core.domain.constants import (
    BLOCK_TRADE_THRESHOLD,
    WALL_CONVERGENCE_TOLERANCE,
    DELTA_IV_CAP,
    SIGMA_ENTRY,
    SIGMA_TP,
    SIGMA_SL,
    TRADING_DAYS_PER_YEAR,
)
from core.use_cases.gtbr import calculate_gtbr_rule16
from core.use_cases.sd_range import calculate_sd_ranges
from core.domain.vol_surface import fit_vol_surface
from core.use_cases.dgc import calculate_polynomial_dgc


def render_gbt_tab(
    df_intraday: pd.DataFrame,
    df_oi: pd.DataFrame,
    chart_mode: str,
    pnl_view: str = "PropFirm Trader",
):
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

    # ── ATM / DTE / Header Vol ──
    _h1_v = _vol_snap['Header1'].iloc[0]
    _h1_o = _oi_snap['Header1'].iloc[0]
    _h2_v = _vol_snap['Header2'].iloc[0]
    _h2_o = _oi_snap['Header2'].iloc[0]
    _atm_v = extract_atm(_h1_v)
    _atm_o = extract_atm(_h1_o)
    _dte_v = extract_dte(_h1_v)
    _dte_o = extract_dte(_h1_o)
    _hvol_v = extract_header_vol(_h2_v)
    _hvol_o = extract_header_vol(_h2_o)

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
    # ATM IV: prefer official CME Header2 Vol, fallback to per-strike lookup
    _iv_v = get_atm_iv(_vol_snap, _atm, header_vol=_hvol_v)
    _iv_o = get_atm_iv(_oi_snap, _atm, header_vol=_hvol_o)
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
    _nva_o = _nvg_o = _nga_o = _nta_o = 0.0
    if _iv_o:
        result_o = calculate_gex_analysis(_oi_snap, _atm, _dte, "OI")
        _gf_o = result_o.flip
        _pw_o = result_o.pos_wall
        _nw_o = result_o.neg_wall
        _gdf_o = result_o.gex_df
        _pk_o = result_o.peak
        _nva_o = result_o.net_vanna_total
        _nvg_o = result_o.net_volga_total
        _nga_o = result_o.net_gamma_total
        _nta_o = result_o.net_theta_total

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

    # Mean of all crossings — informational display only (shown in metric delta).
    # SD table centers on the LOWEST composite flip crossing (nearest structural
    # gamma-neutral level below ATM). Falls back to ATM when no crossings exist.
    _mean_flip = (
        sum(_all_comp_crossings) / len(_all_comp_crossings)
        if len(_all_comp_crossings) > 1 else None
    )
    _sd_center = (
        min(_all_comp_crossings, key=lambda x: abs(x - _atm))
        if _all_comp_crossings else _atm
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

        # Vanna + Volga Adjusted GTBR — use aggregate Gamma/Theta for
        # internal consistency per Carr & Wu (2020) (issue #4 fix)
        vgtbr_result = calculate_vanna_adjusted_gtbr(
            _atm, _iv_comp, _dte,
            _net_vanna, _net_volga, _delta_iv,
            net_gamma=_nga_o or None,
            net_theta=_nta_o or None,
        )
        _va_ld = vgtbr_result.lo_daily
        _va_hd = vgtbr_result.hi_daily
        _va_le = vgtbr_result.lo_expiry
        _va_he = vgtbr_result.hi_expiry
        _v_shift_d = vgtbr_result.shift_daily
        _v_shift_e = vgtbr_result.shift_expiry

    # ── Pre-compute sigma + DGC variants (shared by chart and σ-Range tables) ──
    # Defined here so chart can use them before the σ-Range table section.
    _sigma_d = _atm * _iv_comp / math.sqrt(TRADING_DAYS_PER_YEAR) if _iv_comp and _dte > 0 else 0.0
    _sigma_e = _atm * _iv_comp * math.sqrt(_dte / TRADING_DAYS_PER_YEAR) if _iv_comp and _dte > 0 else 0.0

    # DGC Option 1: Wall Midpoint — structural center of gravity
    # Midpoint of +Wall (resistance) and −Wall (support) = where dealer
    # hedging forces are in structural equilibrium.
    _dgc_wall = (
        (_c_pw + _c_nw) / 2.0
        if _c_pw is not None and _c_nw is not None
        else None
    )

    # DGC Option 2: V-GTBR Midpoint — vertex of Carr & Wu P&L parabola
    # = F − (Net_Vanna × ΔIV) / Net_Gamma  (behavioral pin point)
    # Only meaningful when Δσ ≠ 0 (otherwise collapses to ATM).
    _dgc_vgtbr = (_va_ld + _va_hd) / 2.0 if _va_ld and _va_hd else None

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

    # ── Vol Surface polynomial fit (Phase 5/8) ──
    _poly_coeffs = None
    if 'Vol Settle' in _oi_snap.columns and _dte > 0:
        _T_fit = max(_dte / 365.0, 1e-6)
        _poly_coeffs = fit_vol_surface(
            _oi_snap['Strike'].tolist(),
            _oi_snap['Vol Settle'].tolist(),
            _atm, _T_fit,
        )

    # ── Polynomial DGC (Phase 6) ──
    _dgc_poly = None
    if _poly_coeffs is not None and _dte > 0:
        _T_fit2 = max(_dte / 365.0, 1e-6)
        _dgc_poly = calculate_polynomial_dgc(
            _oi_snap['Strike'].tolist(),
            _oi_snap['Call'].tolist(),
            _oi_snap['Put'].tolist(),
            _oi_snap['Vol Settle'].tolist(),
            _atm, _T_fit2, _poly_coeffs,
        )

    # ── SD Range controls (center + range type) ──
    _ctrl_col1, _ctrl_col2 = st.columns(2)

    with _ctrl_col1:
        _sd_opts = ["📊 Nearest Flip / ATM — Probability Center"]
        if _dgc_wall is not None:
            _sd_opts.append("📌 DGC Wall — ±Wall Midpoint (Structural)")
        if _dgc_vgtbr is not None:
            _sd_opts.append("📌 DGC V-GTBR — P&L Vertex (Behavioral)")
        if _dgc_poly is not None:
            _sd_opts.append("📌 DGC Polynomial — Vol Surface Vertex")
        # Preserve selection; on stale/missing, default to DGC Wall if available
        _DGC_WALL_OPT = "📌 DGC Wall — ±Wall Midpoint (Structural)"
        if st.session_state.get("gbt_sd_mode") not in _sd_opts:
            st.session_state["gbt_sd_mode"] = (
                _DGC_WALL_OPT if _DGC_WALL_OPT in _sd_opts
                else _sd_opts[0]
            )
        _sd_mode = st.selectbox(
            "📐 SD Center — จุดศูนย์กลาง",
            _sd_opts,
            key="gbt_sd_mode",
            help=(
                "จุดศูนย์กลางของ σ-Zone บนกราฟ · แต่ละตัวตอบคำถามต่างกัน:\n\n"
                "• **Nearest Flip / ATM** — จุดที่ Cumulative GEX เปลี่ยนเครื่องหมาย "
                "(ใกล้ ATM ที่สุด) ใช้ดู Regime boundary\n"
                "• **DGC Wall** — จุดกลาง (+Wall + −Wall) / 2 "
                "สะท้อนสมดุลโครงสร้าง Hedging ของ Dealer\n"
                "• **DGC V-GTBR** — Vertex ของ Carr & Wu P&L parabola "
                "จุดที่ Dealer มี Profit สูงสุด (ต้องการ Δσ ≠ 0)\n"
                "• **DGC Polynomial** — Numerical vertex จาก PnL(ΔF) + Vol Surface "
                "รวม Skew dynamics ทั้งหมด (Expert)\n\n"
                "💡 **PropFirm แนะนำ**: DGC Wall หรือ DGC V-GTBR เพราะสะท้อน "
                "แรงดึงดูดราคาที่แท้จริงจากโครงสร้าง Dealer"
            ),
        )

    with _ctrl_col2:
        # Build range options dynamically — V-GTBR options only when solved
        _range_opts = ["📏 R16 Daily  (F×σ/√252)"]
        if _va_ld and _va_hd:
            _range_opts.append("🔹 V-GTBR Daily  (Vanna-Volga adj.)")
        _range_opts.append("📏 R16 Expiry  (F×σ×√(DTE/252))")
        if _va_le and _va_he:
            _range_opts.append("🔹 V-GTBR Expiry  (Vanna-Volga adj.)")
        # Preserve selection; on stale/missing, default to R16 Expiry
        _R16_EXPIRY_OPT = "📏 R16 Expiry  (F×σ×√(DTE/252))"
        if st.session_state.get("gbt_range_mode") not in _range_opts:
            st.session_state["gbt_range_mode"] = (
                _R16_EXPIRY_OPT if _R16_EXPIRY_OPT in _range_opts
                else _range_opts[0]
            )
        _range_mode = st.selectbox(
            "📏 SD Range — ขนาด 1σ",
            _range_opts,
            key="gbt_range_mode",
            help=(
                "ขนาด 1σ สำหรับแถบสีบนกราฟ · เลือกตาม timeframe:\n\n"
                "• **R16 Daily** (F×σ/√252) — Breakeven รายวัน ใช้ Rule of 16\n"
                "• **R16 Expiry** (F×σ×√(DTE/252)) — Breakeven ตลอด DTE ที่เหลือ\n"
                "• **V-GTBR Daily/Expiry** — ครึ่งหนึ่งของ Vanna-Volga Kill Zone "
                "เป็น 1σ สะท้อนขีดจำกัดความอดทนจริงของ Dealer\n\n"
                "💡 **σ-Zone สี**: 1σ = 🟢 Safe Zone · 2σ = 🟡 Pressure · 3σ = 🔴 Kill Zone"
            ),
        )

    # Resolve center from selected SD mode
    _use_dgc = "DGC" in _sd_mode
    if "DGC Wall" in _sd_mode and _dgc_wall is not None:
        _chart_center = _dgc_wall
        _dgc_label = "DGC Wall"
    elif "DGC V-GTBR" in _sd_mode and _dgc_vgtbr is not None:
        _chart_center = _dgc_vgtbr
        _dgc_label = "DGC V-GTBR"
    elif "DGC Polynomial" in _sd_mode and _dgc_poly is not None:
        _chart_center = _dgc_poly
        _dgc_label = "DGC Poly"
    else:
        _chart_center = _sd_center
        _dgc_label = "SD Center"

    if "V-GTBR Daily" in _range_mode and _va_ld and _va_hd:
        _sigma_band = (_va_hd - _va_ld) / 2.0
        _range_label = "V-1D"
    elif "V-GTBR Expiry" in _range_mode and _va_le and _va_he:
        _sigma_band = (_va_he - _va_le) / 2.0
        _range_label = "V-Exp"
    elif "Expiry" in _range_mode:
        _sigma_band = _sigma_e
        _range_label = "Exp"
    else:
        _sigma_band = _sigma_d
        _range_label = "1D"

    # Band colors: PropFirm uses semantic colors, DGC uses gold, default uses purple
    if pnl_view == "PropFirm Trader":
        _band_color_1s = "rgba(34,197,94,0.12)"     # Green — Safe/SL zone
        _band_color_2s = "rgba(251,191,36,0.10)"     # Yellow — Entry zone
        _center_line_color = "#FBBF24" if _use_dgc else "#A855F7"
    elif _use_dgc:
        _band_color_1s = "rgba(251,191,36,0.14)"
        _band_color_2s = "rgba(251,191,36,0.06)"
        _center_line_color = "#FBBF24"
    else:
        _band_color_1s = "rgba(139,92,246,0.14)"
        _band_color_2s = "rgba(139,92,246,0.06)"
        _center_line_color = "#A855F7"

    # ── PropFirm σ-zone colors (3σ–5σ extend beyond existing 1σ/2σ) ──
    _ZONE_COLORS = {
        3: "rgba(239,68,68,0.10)",    # Red — TP / Kill Zone
        4: "rgba(139,92,246,0.06)",    # Purple — Extreme
        5: "rgba(139,92,246,0.03)",    # Purple faint — Black Swan
    }

    # ── Rule of 16 SD ranges (Phase 2) ──
    _r16_lo, _r16_hi, _r16_move = (0.0, 0.0, 0.0)
    _sd_result = None
    if _iv_comp and _dte > 0:
        _r16_lo, _r16_hi, _r16_move = calculate_gtbr_rule16(_atm, _iv_comp)
        _sd_result = calculate_sd_ranges(
            _atm, _iv_comp, max(_dte / 365.0, 1e-6),
            center=_chart_center,
            center_label=_dgc_label,
            poly_coeffs=_poly_coeffs,
        )

    def _card(title, value, sub="", border_color="rgba(255,255,255,0.15)"):
        return (
            f"<div style='padding:10px 14px;border-radius:8px;"
            f"background:rgba(255,255,255,0.03);"
            f"border:1px solid {border_color};"
            f"text-align:center;min-height:90px'>"
            f"<div style='font-size:11px;color:gray;font-weight:600;"
            f"text-transform:uppercase;letter-spacing:0.5px'>{title}</div>"
            f"<div style='font-size:18px;font-weight:700;color:white;"
            f"margin:4px 0 2px'>{value}</div>"
            f"<div style='font-size:11px;color:gray'>{sub}</div>"
            f"</div>"
        )

    # ═════════════════════════════════════
    #  CHART: 2-row subplot
    # ═════════════════════════════════════
    _fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        row_heights=[0.65, 0.35],
        vertical_spacing=0.10,
        subplot_titles=(
            "Composite GEX per Strike",
            "Cumulative Composite GEX",
        )
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

    # ── Compute y-ranges for toggleable reference line traces ──
    _y1_vals = (
        list(_cdf['GEX_OI']) + list(_cdf['γ_Flow'])
        + list(_cdf['Composite'])
    )
    _y1_min, _y1_max = min(_y1_vals), max(_y1_vals)
    _y1_pad = (_y1_max - _y1_min) * 0.15
    _y2_vals = list(_cdf['Cumulative'])
    _y2_min, _y2_max = min(_y2_vals), max(_y2_vals)
    _y2_pad = (_y2_max - _y2_min) * 0.15
    _yranges = {
        1: (_y1_min - _y1_pad, _y1_max + _y1_pad),
        2: (_y2_min - _y2_pad, _y2_max + _y2_pad),
    }

    # ── Reference lines + SD bands on both rows ──
    for _r in [1, 2]:
        # σ-Range rectangles (drawn first so they sit behind all lines)
        if _sigma_band > 0:
            _fig.add_vrect(
                x0=_chart_center - 2 * _sigma_band,
                x1=_chart_center + 2 * _sigma_band,
                fillcolor=_band_color_2s, line_width=0, layer="below",
                row=_r, col=1,
                annotation_text=f"2σ ({_range_label})" if _r == 1 else None,
                annotation_position="top left",
                annotation_font=dict(color=_center_line_color, size=8),
            )
            _fig.add_vrect(
                x0=_chart_center - _sigma_band,
                x1=_chart_center + _sigma_band,
                fillcolor=_band_color_1s, line_width=0, layer="below",
                row=_r, col=1,
                annotation_text=f"1σ ({_range_label})" if _r == 1 else None,
                annotation_position="top left",
                annotation_font=dict(color=_center_line_color, size=8),
            )
            # PropFirm 3σ–5σ extended zones
            if pnl_view == "PropFirm Trader":
                for _n_zone in range(3, 6):
                    _zc = _ZONE_COLORS.get(_n_zone, "rgba(128,128,128,0.03)")
                    _fig.add_vrect(
                        x0=_chart_center - _n_zone * _sigma_band,
                        x1=_chart_center + _n_zone * _sigma_band,
                        fillcolor=_zc, line_width=0, layer="below",
                        row=_r, col=1,
                        annotation_text=f"{_n_zone}σ" if _r == 1 and _n_zone == 3 else None,
                        annotation_position="top left",
                        annotation_font=dict(color="#EF4444", size=8),
                    )
            # Center line (toggleable via legend)
            _fig.add_trace(go.Scatter(
                x=[_chart_center, _chart_center],
                y=[_yranges[_r][0], _yranges[_r][1]],
                mode='lines',
                name=_dgc_label,
                line=dict(
                    color=_center_line_color,
                    dash="longdash", width=1.5,
                ),
                opacity=0.7,
                showlegend=(_r == 1),
                legendgroup="sd_center",
                hoverinfo='name+x',
            ), row=_r, col=1)
        # ── Toggleable reference lines (click legend to hide) ──
        _fig.add_trace(go.Scatter(
            x=[_atm, _atm],
            y=[_yranges[_r][0], _yranges[_r][1]],
            mode='lines',
            name='ATM',
            line=dict(color='#888888', dash='dash', width=1.5),
            opacity=0.8,
            showlegend=(_r == 1),
            legendgroup='atm',
            hoverinfo='name+x',
        ), row=_r, col=1)
        if _le and _he:
            for _xv, _lb in [
                (_le, "GTBR↓"), (_he, "GTBR↑"),
            ]:
                _fig.add_trace(go.Scatter(
                    x=[_xv, _xv],
                    y=[_yranges[_r][0], _yranges[_r][1]],
                    mode='lines',
                    name='GTBR Exp',
                    line=dict(
                        color='#FB923C', dash='dash', width=2,
                    ),
                    opacity=0.85,
                    showlegend=(_r == 1 and _lb == "GTBR↓"),
                    legendgroup='gtbr_exp',
                    hoverinfo='name+x',
                ), row=_r, col=1)
        if _ld and _hd:
            for _xv, _lb in [
                (_ld, "1D↓"), (_hd, "1D↑"),
            ]:
                _fig.add_trace(go.Scatter(
                    x=[_xv, _xv],
                    y=[_yranges[_r][0], _yranges[_r][1]],
                    mode='lines',
                    name='GTBR 1D',
                    line=dict(
                        color='#FCD34D', dash='dot', width=1.5,
                    ),
                    opacity=0.7,
                    showlegend=(_r == 1 and _lb == "1D↓"),
                    legendgroup='gtbr_1d',
                    hoverinfo='name+x',
                ), row=_r, col=1)
        # ── Vanna-Adjusted GTBR (cyan/teal) ──
        if _va_le and _va_he:
            for _xv, _lb in [
                (_va_le, "V-GTBR↓"),
                (_va_he, "V-GTBR↑"),
            ]:
                _fig.add_trace(go.Scatter(
                    x=[_xv, _xv],
                    y=[_yranges[_r][0], _yranges[_r][1]],
                    mode='lines',
                    name='V-GTBR Exp',
                    line=dict(
                        color='#06B6D4', dash='dashdot', width=2,
                    ),
                    opacity=0.8,
                    showlegend=(_r == 1 and _lb == "V-GTBR↓"),
                    legendgroup='vgtbr_exp',
                    hoverinfo='name+x',
                ), row=_r, col=1)
        if _va_ld and _va_hd:
            for _xv, _lb in [
                (_va_ld, "V-1D↓"),
                (_va_hd, "V-1D↑"),
            ]:
                _fig.add_trace(go.Scatter(
                    x=[_xv, _xv],
                    y=[_yranges[_r][0], _yranges[_r][1]],
                    mode='lines',
                    name='V-GTBR 1D',
                    line=dict(
                        color='#2DD4BF', dash='dot', width=1.5,
                    ),
                    opacity=0.65,
                    showlegend=(_r == 1 and _lb == "V-1D↓"),
                    legendgroup='vgtbr_1d',
                    hoverinfo='name+x',
                ), row=_r, col=1)
        if _c_flip:
            _fig.add_trace(go.Scatter(
                x=[_c_flip, _c_flip],
                y=[_yranges[_r][0], _yranges[_r][1]],
                mode='lines',
                name='Flip',
                line=dict(color='#A855F7', dash='dot', width=2),
                opacity=0.9,
                showlegend=(_r == 1),
                legendgroup='flip',
                hoverinfo='name+x',
            ), row=_r, col=1)
        if _c_pw:
            _fig.add_trace(go.Scatter(
                x=[_c_pw, _c_pw],
                y=[_yranges[_r][0], _yranges[_r][1]],
                mode='lines',
                name='+Wall',
                line=dict(
                    color='#22C55E', dash='dashdot', width=1.5,
                ),
                opacity=0.7,
                showlegend=(_r == 1),
                legendgroup='pos_wall',
                hoverinfo='name+x',
            ), row=_r, col=1)
        if _c_nw:
            _fig.add_trace(go.Scatter(
                x=[_c_nw, _c_nw],
                y=[_yranges[_r][0], _yranges[_r][1]],
                mode='lines',
                name='−Wall',
                line=dict(
                    color='#F43F5E', dash='dashdot', width=1.5,
                ),
                opacity=0.7,
                showlegend=(_r == 1),
                legendgroup='neg_wall',
                hoverinfo='name+x',
            ), row=_r, col=1)

    _fig.update_layout(
        barmode='group', bargap=0.15,
        height=750,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        hovermode="x unified",
        legend=dict(
            orientation="h",
            yanchor="bottom", y=1.04,
            xanchor="center", x=0.5,
            font=dict(size=11),
            itemclick="toggle",
            itemdoubleclick="toggleothers",
        ),
        margin=dict(l=10, r=10, t=80, b=10),
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

    # ── Dashboard metric badges (hoverable tooltips) ──
    _DASH_TIPS = {
        "Regime": {
            "color": "#22C55E",
            "title": "Gamma Regime — สภาวะตลาด",
            "desc": (
                "บอกว่าตลาดอยู่ในโหมด <b>สะกดความผันผวน</b> (Long γ = Mean-revert) "
                "หรือ <b>เร่งความผันผวน</b> (Short γ = Trend-follow)<br><br>"
                "• Long γ → Dealer ซื้อขาลง/ขายขาขึ้น → ราคามักดีดกลับเข้าหา ATM<br>"
                "• Short γ → Dealer ไล่ตามราคา → ราคาเคลื่อนไหวรุนแรงและเร่งตัว"
            ),
        },
        "ATM": {
            "color": "#888888",
            "title": "ATM / IV — จุดอ้างอิงกลาง",
            "desc": (
                "ราคา Futures ปัจจุบัน — จุดที่ <b>Gamma และ Theta สูงสุด</b><br>"
                "IV คือความคาดหวังของตลาดต่อความผันผวน ใช้คำนวณทุก Greek และกรอบ GTBR"
            ),
        },
        "Flip": {
            "color": "#A855F7",
            "title": "Composite Flip — จุดเปลี่ยนระบอบ",
            "desc": (
                "ระดับราคาที่ <b>Cumulative GEX เปลี่ยนจากบวกเป็นลบ</b><br>"
                "เป็น Inflection Point — พฤติกรรมราคาเปลี่ยนจากสงบเป็นรุนแรงทันที<br><br>"
                "• เหนือ Flip → Dealer Long γ → ตลาดสงบ<br>"
                "• ต่ำกว่า Flip → Dealer Short γ → ตลาดรุนแรง"
            ),
        },
        "±Wall": {
            "color": "#22C55E",
            "title": "±GEX Wall — แนวรับ/แนวต้านเชิงโครงสร้าง",
            "desc": (
                "Strike ที่ OI หนาแน่นที่สุด — Dealer จะ <b>Rebalance อย่างรุนแรง</b> "
                "เพื่อตรึงราคา (Pinning Effect)<br><br>"
                "• <b>+Wall</b> = แนวต้าน (Dealer ขาย Futures เข้าใกล้)<br>"
                "• <b>−Wall</b> = แนวรับ (หลุด → Cascading Sell-off)"
            ),
        },
        "GTBR": {
            "color": "#FB923C",
            "title": "GTBR — กรอบจุดคุ้มทุน γ/θ",
            "desc": (
                "กรอบที่ <b>Theta profit = Gamma Loss</b><br>"
                "หากราคาทะลุกรอบนี้ = Dealer ต้องไล่ Hedge ทันที (Inelastic Demand)<br><br>"
                "• Daily: ΔF = F×σ/√252 (Rule of 16) — จุดคุ้มทุนรายวัน<br>"
                "• Expiry: ΔF = F×σ×√(DTE/252) — จุดคุ้มทุนตลอดอายุสัญญา"
            ),
        },
        "V-GTBR": {
            "color": "#06B6D4",
            "title": "V-GTBR — กรอบปรับด้วย Vanna/Volga",
            "desc": (
                "กรอบจาก Carr & Wu (2020) ที่รวม <b>Shadow Greeks</b> เข้าไปด้วย<br>"
                "สะท้อน Kill Zone ที่แม่นยำกว่า GTBR ปกติ<br><br>"
                "• Vanna ทำให้กรอบ <b>เลื่อนไม่สมมาตร</b> ตามทิศทาง IV<br>"
                "• Volga ทำให้กรอบ <b>ขยาย/หดสมมาตร</b> ตาม Vol-of-Vol"
            ),
        },
        "Vanna": {
            "color": "#3B82F6",
            "title": "Net Vanna — Shadow Delta",
            "desc": (
                "วัดว่า <b>Delta เปลี่ยนแค่ไหนเมื่อ IV เปลี่ยน</b><br>"
                "ในตลาดทองคำ (Positive Spot-Vol Correlation):<br><br>"
                "• <b>บวก</b> → IV พุ่ง = แรงบีบซื้อ Futures (Gamma Squeeze ด้านบน)<br>"
                "• <b>ลบ</b> → IV พุ่ง = แรงบีบขาย Futures (Crash Acceleration)"
            ),
        },
        "Volga": {
            "color": "#A855F7",
            "title": "Net Volga — ความไว Vol-of-Vol",
            "desc": (
                "วัดว่า <b>Vega เปลี่ยนแค่ไหนเมื่อ IV เปลี่ยน</b><br><br>"
                "• <b>บวก</b> → กรอบ BE ขยาย — Dealer ทนได้มากขึ้น<br>"
                "• <b>ลบ</b> → กรอบ BE หด — Dealer เปราะบาง<br>"
                "• IV ระเบิด + Short Volga = ขาดทุนแบบ Exponential (Shadow Vega Trap)"
            ),
        },
        "ΔIV": {
            "color": "#3B82F6",
            "title": "ΔIV Proxy — การเปลี่ยนแปลง IV",
            "desc": (
                "ผลต่าง IV ระหว่าง <b>Intraday snapshot</b> กับ <b>OI settlement</b><br>"
                "ใช้คำนวณแรงผลักจาก Shadow Greeks ในสมการ Carr & Wu<br><br>"
                "• ΔIV สูง → Vanna/Volga term มีอิทธิพลมากขึ้น<br>"
                "• Cap ±5% เพื่อป้องกัน Distortion จาก Vol Regime Jump"
            ),
        },
        "DGC": {
            "color": "#FBBF24",
            "title": "DGC — Dealer Gravity Center",
            "desc": (
                "จุดศูนย์ถ่วงเชิงพฤติกรรม — <b>Operational Pin Point</b><br>"
                "จุดที่ Dealer มีแรงจูงใจทางการเงินสูงสุดในการตรึงราคา "
                "เพื่อให้ Theta profit ชนะ Gamma + Shadow Greeks loss<br><br>"
                "• <b>Wall Mid</b>: จุดกลาง +Wall/−Wall — สมดุลโครงสร้าง<br>"
                "• <b>V-GTBR</b>: Vertex ของ P&L parabola — สมดุลพฤติกรรม"
            ),
        },
    }
    _tip_badges = ""
    for _tk, _tv in _DASH_TIPS.items():
        _tc = _tv["color"]
        _tip_badges += (
            f'<div class="vl-item" style="border-color:{_tc}">'
            f'  <span class="vl-dot" style="background:{_tc}"></span>'
            f'  <span style="color:{_tc}">{_tk}</span>'
            f'  <div class="vl-tip">'
            f'    <div style="font-size:13px;font-weight:700;color:#fff;margin-bottom:6px">'
            f'      {_tv["title"]}'
            f'    </div>'
            f'    {_tv["desc"]}'
            f'  </div>'
            f'</div>'
        )
    st.markdown(
        f'<div class="vl-legend">{_tip_badges}</div>',
        unsafe_allow_html=True,
    )

    # ═════════════════════════════════════
    #  GBT REGIME DASHBOARD (unified cards)
    # ═════════════════════════════════════
    st.markdown("---")
    st.markdown(
        "### :material/dashboard: "
        "GBT Regime Dashboard"
    )

    # ── Row 1: Regime · ATM · Flip · ±Walls · GTBR ──
    _r1c1, _r1c2, _r1c3, _r1c4, _r1c5 = st.columns(5)
    with _r1c1:
        _rcol = "green" if _net >= 0 else "red"
        _rbg = (
            'rgba(34,197,94,0.15)' if _net >= 0
            else 'rgba(239,68,68,0.15)'
        )
        st.markdown(
            f"<div style='padding:10px 14px;border-radius:8px;"
            f"background:{_rbg};border:1px solid {_rcol};"
            f"text-align:center;min-height:90px'>"
            f"<div style='font-size:11px;color:gray;font-weight:600;"
            f"text-transform:uppercase;letter-spacing:0.5px'>Gamma Regime</div>"
            f"<div style='font-size:16px;font-weight:700;color:{_rcol};"
            f"margin:4px 0 2px'>{_regime}</div>"
            f"<div style='font-size:11px;color:gray'>Net: {_net:,.1f}</div>"
            f"</div>",
            unsafe_allow_html=True,
        )
    with _r1c2:
        st.markdown(_card(
            "ATM",
            f"{_atm:,.1f}",
            (f"IV {_iv_comp*100:.1f}% · DTE {_dte:.1f}"
             if _iv_comp else f"DTE {_dte:.1f}"),
            "rgba(136,136,136,0.4)",
        ), unsafe_allow_html=True)
    with _r1c3:
        _flip_str = f"{_c_flip:,.1f}" if _c_flip else "N/A"
        _cross_n = len(_all_comp_crossings)
        _flip_sub = f"{_cross_n} crossing{'s' if _cross_n != 1 else ''}"
        if _mean_flip is not None:
            _flip_sub += f" · mean {_mean_flip:,.1f}"
        st.markdown(_card(
            "Composite Flip",
            _flip_str,
            _flip_sub,
            "rgba(168,85,247,0.4)",
        ), unsafe_allow_html=True)
    with _r1c4:
        _wall_str = "—"
        if _c_pw and _c_nw:
            _wall_str = f"{_c_nw:,.0f} — {_c_pw:,.0f}"
        elif _c_pw:
            _wall_str = f"— / {_c_pw:,.0f}"
        elif _c_nw:
            _wall_str = f"{_c_nw:,.0f} / —"
        st.markdown(_card(
            "−Wall / +Wall",
            _wall_str,
            "Support — Resistance",
            "rgba(34,197,94,0.3)",
        ), unsafe_allow_html=True)
    with _r1c5:
        if _ld and _hd:
            _gtbr_sub = f"Exp: {_le:,.0f}—{_he:,.0f}" if _le and _he else ""
            st.markdown(_card(
                "GTBR Daily",
                f"{_ld:,.0f} — {_hd:,.0f}",
                _gtbr_sub,
                "rgba(251,146,60,0.3)",
            ), unsafe_allow_html=True)
        else:
            st.markdown(_card(
                "GTBR", "N/A", "",
                "rgba(251,146,60,0.2)",
            ), unsafe_allow_html=True)

    st.markdown("<div style='margin-top:12px'></div>", unsafe_allow_html=True)

    # ── Row 2: V-GTBR · Net Vanna · Net Volga · ΔIV · DGC ──
    _r2c1, _r2c2, _r2c3, _r2c4, _r2c5 = st.columns(5)
    with _r2c1:
        if _va_ld and _va_hd:
            _vgtbr_sub = f"Exp: {_va_le:,.0f}—{_va_he:,.0f}" if _va_le and _va_he else ""
            if _v_shift_d != 0:
                _vgtbr_sub += f" · shift {_v_shift_d:+.1f}"
            st.markdown(_card(
                "V-GTBR Daily",
                f"{_va_ld:,.0f} — {_va_hd:,.0f}",
                _vgtbr_sub,
                "rgba(6,182,212,0.3)",
            ), unsafe_allow_html=True)
        else:
            st.markdown(_card(
                "V-GTBR", "N/A", "",
                "rgba(6,182,212,0.2)",
            ), unsafe_allow_html=True)
    with _r2c2:
        _vanna_dir_label = (
            "Bullish Shift" if _net_vanna > 0
            else "Bearish Shift" if _net_vanna < 0
            else "Neutral"
        )
        st.markdown(_card(
            "Net Vanna",
            f"{_net_vanna:,.2f}",
            _vanna_dir_label,
            "rgba(59,130,246,0.3)",
        ), unsafe_allow_html=True)
    with _r2c3:
        _volga_label = (
            "Widen Range" if _net_volga > 0
            else "Narrow Range" if _net_volga < 0
            else "Neutral"
        )
        st.markdown(_card(
            "Net Volga",
            f"{_net_volga:,.2f}",
            _volga_label,
            "rgba(168,85,247,0.3)",
        ), unsafe_allow_html=True)
    with _r2c4:
        _was_capped = (
            bool(_iv_v and _iv_o)
            and abs(_iv_v - _iv_o) > DELTA_IV_CAP
        )
        _div_str = (
            f"{_delta_iv*100:+.2f}%"
            + (" (capped)" if _was_capped else "")
            if _delta_iv != 0
            else "0"
        )
        st.markdown(_card(
            "ΔIV Proxy",
            _div_str,
            "IV_intraday − IV_OI",
            "rgba(59,130,246,0.2)",
        ), unsafe_allow_html=True)
    with _r2c5:
        _dgc_display = _dgc_wall if _dgc_wall is not None else _dgc_vgtbr
        if _dgc_display is not None:
            _dgc_offset = _dgc_display - _atm
            _dgc_type = "Wall Mid" if _dgc_wall is not None else "V-GTBR"
            st.markdown(_card(
                f"DGC ({_dgc_type})",
                f"{_dgc_display:,.1f}",
                f"ATM {_dgc_offset:+.1f}",
                "rgba(251,191,36,0.3)",
            ), unsafe_allow_html=True)
        else:
            st.markdown(_card(
                "DGC", "N/A", "",
                "rgba(251,191,36,0.2)",
            ), unsafe_allow_html=True)

    # ── Vanna/Volga interpretation caption ──
    if _net_vanna != 0 and _delta_iv != 0:
        _vanna_dir = (
            "upside" if _net_vanna * _delta_iv > 0
            else "downside"
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

    st.markdown("<div style='margin-top:12px'></div>", unsafe_allow_html=True)

    # ── Convergence info ──
    if _conv:
        st.info(
            "**Convergence:**  "
            + "  |  ".join(_conv)
        )

    # ── Block info with TP/SL per strike ──
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

        # ── Compute TP/SL per block strike based on regime ──
        _is_long_gamma = _net >= 0
        _tp_long_list = []
        _tp_short_list = []
        _sl_list = []

        if _is_long_gamma:
            # Mean-Reversion: TP = ±Wall, SL = Composite Flip
            _tp_l = _c_pw if _c_pw else _chart_center + 2 * _sigma_band
            _tp_s = _c_nw if _c_nw else _chart_center - 2 * _sigma_band
            _sl_val = _c_flip if _c_flip else _chart_center
            for _ in range(len(_blk_detail)):
                _tp_long_list.append(round(_tp_l, 1))
                _tp_short_list.append(round(_tp_s, 1))
                _sl_list.append(round(_sl_val, 1))
        else:
            # Trend-Following: TP = 3σ, SL = 1σ (or Flip)
            _tp_up = _chart_center + SIGMA_TP * _sigma_band
            _tp_dn = _chart_center - SIGMA_TP * _sigma_band
            _sl_flip = _c_flip if _c_flip else _chart_center
            for _ in range(len(_blk_detail)):
                _tp_long_list.append(round(_tp_up, 1))
                _tp_short_list.append(round(_tp_dn, 1))
                _sl_list.append(round(_sl_flip, 1))

        _blk_detail['TP Long'] = _tp_long_list
        _blk_detail['TP Short'] = _tp_short_list
        _blk_detail['SL'] = _sl_list

        _regime_tag = "LONG γ → Mean-Reversion" if _is_long_gamma else "SHORT γ → Trend-Following"
        st.warning(
            f"🟣 **{_n_blocks} Block Trade(s) detected** "
            f"(Ratio ≥ {_block_thr}x) — **{_regime_tag}**"
        )
        st.caption(
            "**Ratio** = |γ-Flow / GEX_OI| — ค่า ≥ 1.0 = สถาบันเปิดสถานะใหม่เท่ากับ OI เดิม  ·  "
            + (
                "**TP** = ±Wall (จุดสมดุล Hedging) · **SL** = Flip (จุดเปลี่ยน Regime)"
                if _is_long_gamma else
                f"**TP** = ±{SIGMA_TP}σ (Dealer forced hedge climax) · **SL** = Flip/Center"
            )
        )
        st.dataframe(
            _blk_detail,
            column_config={
                "Strike": st.column_config.NumberColumn("Strike", format="%d"),
                "Call_Vol": st.column_config.NumberColumn("Call Vol", format="%d"),
                "Put_Vol": st.column_config.NumberColumn("Put Vol", format="%d"),
                "γ_Flow": st.column_config.NumberColumn("γ-Flow", format="%.2f"),
                "GEX_OI": st.column_config.NumberColumn("GEX (OI)", format="%.2f"),
                "Ratio": st.column_config.NumberColumn("Ratio", format="%.2f"),
                "TP Long": st.column_config.NumberColumn("TP Long", format="%.1f"),
                "TP Short": st.column_config.NumberColumn("TP Short", format="%.1f"),
                "SL": st.column_config.NumberColumn("SL", format="%.1f"),
            },
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

    # ═════════════════════════════════════
    #  σ-RANGE TABLE: 1–6 Standard Deviations
    # ═════════════════════════════════════
    if _iv_comp and _dte > 0:
        st.markdown("---")
        st.markdown(
            "### :material/sigma: "
            "σ-Range Table — 1 ถึง 6 Standard Deviations"
        )

        _center_label = (
            f"Nearest Composite Flip {_sd_center:,.1f}"
            if _all_comp_crossings else f"ATM {_atm:,.1f} (no crossings)"
        )

        st.caption(
            f"**ศูนย์กลาง (Center):** {_center_label}  ·  "
            f"σ_daily = F×σ/√252 = ±{_sigma_d:.1f}  ·  "
            f"σ_expiry = F×σ×√(DTE/252) = ±{_sigma_e:.1f}  ·  "
            f"IV = {_iv_comp * 100:.2f}%  ·  DTE = {_dte:.2f}  ·  "
            f"⚠ ตลาดจริงมี Fat Tail — 3σ+ เกิดบ่อยกว่า Normal Distribution"
        )

        _sd_probs   = [68.27, 95.45, 99.73, 99.994, 99.99994, 99.9999998]
        _sd_notes   = [
            "Gamma Scalping Zone — เคลื่อนไหวปกติ",
            "Stop-loss Reference — ระดับ Outlier",
            "Rare Event — Black Swan เริ่มต้น",
            "Extreme Tail Risk — หายากมาก",
            "Near-Impossible (Normal) — ⚠ Fat Tail ทำให้เกิดได้",
            "Fat-Tail Warning ⚠ ตลาดจริงเกินบ่อยกว่านี้มาก",
        ]
        _sd_rows = []
        for _n, _prob, _note in zip(range(1, 7), _sd_probs, _sd_notes):
            _sd_rows.append({
                "σ": f"{_n}σ",
                "Normal %": f"{_prob:.5f}",
                "Daily Lo": round(_sd_center - _n * _sigma_d, 1),
                "Daily Hi": round(_sd_center + _n * _sigma_d, 1),
                "Daily Width": round(2 * _n * _sigma_d, 1),
                "Expiry Lo": round(_sd_center - _n * _sigma_e, 1),
                "Expiry Hi": round(_sd_center + _n * _sigma_e, 1),
                "Expiry Width": round(2 * _n * _sigma_e, 1),
                "หมายเหตุ": _note,
            })
        _sd_df = pd.DataFrame(_sd_rows)

        st.dataframe(
            _sd_df,
            column_config={
                "σ": st.column_config.TextColumn("σ", width="small"),
                "Normal %": st.column_config.NumberColumn(
                    "Normal %", format="%.5f%%", width="medium"),
                "Daily Lo": st.column_config.NumberColumn(
                    "Daily Lo", format="%,.1f"),
                "Daily Hi": st.column_config.NumberColumn(
                    "Daily Hi", format="%,.1f"),
                "Daily Width": st.column_config.NumberColumn(
                    "Daily ±Width", format="%,.1f"),
                "Expiry Lo": st.column_config.NumberColumn(
                    "Expiry Lo", format="%,.1f"),
                "Expiry Hi": st.column_config.NumberColumn(
                    "Expiry Hi", format="%,.1f"),
                "Expiry Width": st.column_config.NumberColumn(
                    "Expiry ±Width", format="%,.1f"),
                "หมายเหตุ": st.column_config.TextColumn(
                    "หมายเหตุ", width="large"),
            },
            hide_index=True,
            use_container_width=True,
        )

        # ═════════════════════════════════════
        #  σ-RANGE TABLE: DEALER GRAVITY CENTER
        #  Center = Vanna-Volga GTBR midpoint (F + shift_daily)
        #  = midpoint of dealer's Theta-optimal safe zone after Vanna/Volga adjustment.
        #  Answers: "where is price PULLED to?" (behavioral) vs the Flip-centered
        #  table above which answers "where can price go?" (statistical probability).
        #  Supported by Carr & Wu (2020) and institutional GEX pinning theory:
        #  in Positive GEX regime price is magnetised toward the dealer-optimal pin;
        #  V-GTBR midpoint is more precise than raw Max Pain because it incorporates
        #  dynamic IV (Vanna) and vol-of-vol (Volga) into the dealer's cost centre.
        # ═════════════════════════════════════
        # ── Resolve which DGC to use for the σ-Range table ──
        _dgc_table = None
        _dgc_table_label = ""
        _dgc_table_sub = ""
        if _dgc_wall is not None:
            _dgc_table = _dgc_wall
            _wall_offset = _dgc_wall - _atm
            _dgc_table_label = "DGC Wall — ±Wall Midpoint"
            _dgc_table_sub = (
                f"**ศูนย์กลาง (DGC Wall):** "
                f"(+Wall {_c_pw:,.0f} + −Wall {_c_nw:,.0f}) / 2 = {_dgc_wall:,.1f}  "
                f"(ATM {_atm:,.1f} {_wall_offset:+.1f})  ·  "
            )
        if _dgc_vgtbr is not None and abs(_v_shift_d) > 0.5:
            _dgc_table = _dgc_vgtbr
            _dgc_table_label = "DGC V-GTBR — P&L Vertex"
            _dgc_table_sub = (
                f"**ศูนย์กลาง (DGC V-GTBR):** "
                f"V-GTBR Midpoint = {_dgc_vgtbr:,.1f}  "
                f"(ATM {_atm:,.1f} {_v_shift_d:+.1f} จาก Vanna-Volga shift)  ·  "
            )

        if _dgc_table is not None:
            st.markdown("---")
            st.markdown(
                f"### :material/hub: "
                f"σ-Range Table — {_dgc_table_label}"
            )
            st.caption(
                _dgc_table_sub
                + f"σ_daily (R16) = ±{_sigma_d:.1f}  ·  σ_expiry (R16) = ±{_sigma_e:.1f}  ·  "
                f"IV = {_iv_comp * 100:.2f}%  ·  DTE = {_dte:.2f}  ·  "
                f"📌 DGC = จุดที่ Dealer มีแรงจูงใจ Pin ราคา (Behavioral Center)  ·  "
                f"⚠ ตลาดจริงมี Fat Tail — 3σ+ เกิดบ่อยกว่า Normal Distribution"
            )

            _dgc_notes = [
                "Dealer Safe Zone — Theta > Gamma Loss (ปกป้องพรีเมียม)",
                "Hedging Pressure Zone — Dealer เริ่ม Rebalance เชิงรุก",
                "Inelastic Demand — Panic Hedge / Gamma Squeeze เริ่มต้น",
                "Extreme Tail — Dealer ขาดทุนเกินระดับ Gamma Scalping",
                "Near-Impossible (Normal) — ⚠ Fat Tail ทำให้เกิดได้",
                "Fat-Tail Warning ⚠ Shadow Vega / Volga Trap — ขาดทุนแบบ Exponential",
            ]
            _dgc_rows = []
            for _n, _prob, _note in zip(range(1, 7), _sd_probs, _dgc_notes):
                _dgc_rows.append({
                    "σ": f"{_n}σ",
                    "Normal %": f"{_prob:.5f}",
                    "Daily Lo": round(_dgc_table - _n * _sigma_d, 1),
                    "Daily Hi": round(_dgc_table + _n * _sigma_d, 1),
                    "Daily Width": round(2 * _n * _sigma_d, 1),
                    "Expiry Lo": round(_dgc_table - _n * _sigma_e, 1),
                    "Expiry Hi": round(_dgc_table + _n * _sigma_e, 1),
                    "Expiry Width": round(2 * _n * _sigma_e, 1),
                    "หมายเหตุ": _note,
                })
            _dgc_df = pd.DataFrame(_dgc_rows)

            st.dataframe(
                _dgc_df,
                column_config={
                    "σ": st.column_config.TextColumn("σ", width="small"),
                    "Normal %": st.column_config.NumberColumn(
                        "Normal %", format="%.5f%%", width="medium"),
                    "Daily Lo": st.column_config.NumberColumn(
                        "Daily Lo", format="%,.1f"),
                    "Daily Hi": st.column_config.NumberColumn(
                        "Daily Hi", format="%,.1f"),
                    "Daily Width": st.column_config.NumberColumn(
                        "Daily ±Width", format="%,.1f"),
                    "Expiry Lo": st.column_config.NumberColumn(
                        "Expiry Lo", format="%,.1f"),
                    "Expiry Hi": st.column_config.NumberColumn(
                        "Expiry Hi", format="%,.1f"),
                    "Expiry Width": st.column_config.NumberColumn(
                        "Expiry ±Width", format="%,.1f"),
                    "หมายเหตุ": st.column_config.TextColumn(
                        "หมายเหตุ", width="large"),
                },
                hide_index=True,
                use_container_width=True,
            )

            # Comparison callout: show the offset between DGC and probability center
            _dgc_vs_sd = _dgc_table - _sd_center
            if abs(_dgc_vs_sd) > 0.5:
                _pull_dir = "สูงกว่า" if _dgc_vs_sd > 0 else "ต่ำกว่า"
                st.info(
                    f"📌 **DGC vs Probability Center:** "
                    f"Dealer Gravity Center อยู่ {_pull_dir} Lowest Flip "
                    f"**{abs(_dgc_vs_sd):,.1f} จุด** "
                    f"({_sd_center:,.1f} → {_dgc_table:,.1f})  ·  "
                    f"ยิ่ง DGC ห่างจาก ATM มาก = แรงดึง Dealer ต่อตลาดยิ่งชัดเจน"
                )
