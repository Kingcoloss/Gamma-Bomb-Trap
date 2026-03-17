"""
GEX Analysis Use Case
=====================
Compute per-strike Net Gamma Exposure, Vanna, Volga and
identify structural levels (flip, walls, peak).
"""
import pandas as pd

from core.domain.black76 import (
    b76_gamma,
    b76_vanna,
    b76_volga,
    normalize_iv,
)
from core.domain.models import GexResult
from core.domain.constants import GEX_SCALE


def calculate_gex_analysis(
    df: pd.DataFrame,
    futures_price: float,
    dte: float,
    data_mode: str = "OI",
) -> GexResult:
    """
    Compute per-strike Net Gamma Exposure using the Black-76 model
    and identify key structural levels.

    Two semantically distinct modes (same math, different interpretation):

      data_mode = "OI"   →  GEX (Gamma Exposure)
        Uses Open Interest.  Measures *dealer positions*.
        Net GEX_K = Γ_B76(F,K,T,σ_K) × (Call_OI − Put_OI) × F² × 0.01

      data_mode = "Intraday"  →  γ-Flow (Gamma-weighted Volume Flow)
        Uses Intraday Volume.  Measures *activity / order-flow*.
        Net γ-Flow_K = Γ_B76(F,K,T,σ_K) × (Call_Vol − Put_Vol) × F² × 0.01

    Sign convention (dealer perspective):
      +value → stabilising (long gamma / mean-revert tendency)
      −value → destabilising (short gamma / trending tendency)
    """
    T = max(dte / 365.0, 1e-6)

    gex_rows = []
    net_vanna_total = 0.0
    net_volga_total = 0.0

    for _, row in df.iterrows():
        K     = float(row['Strike'])
        sigma = normalize_iv(row['Vol Settle'])
        call  = float(row['Call'])
        put   = float(row['Put'])

        gamma   = b76_gamma(futures_price, K, T, sigma)
        net_gex = gamma * (call - put) * (futures_price ** 2) * GEX_SCALE

        # Per-strike Vanna & Volga
        vanna_k = b76_vanna(futures_price, K, T, sigma) if sigma > 0.001 else 0.0
        volga_k = b76_volga(futures_price, K, T, sigma) if sigma > 0.001 else 0.0
        # Net Vanna: directional (Call − Put)
        net_vanna_k = vanna_k * (call - put)
        # Net Volga: symmetric (Call + Put)
        net_volga_k = volga_k * (call + put)

        net_vanna_total += net_vanna_k
        net_volga_total += net_volga_k

        gex_rows.append({
            'Strike': K,
            'Call': call,
            'Put': put,
            'IV %': round(sigma * 100, 2),
            'Gamma': gamma,
            'Net_GEX': net_gex,
            'Vanna': vanna_k,
            'Volga': volga_k,
            'Net_Vanna': net_vanna_k,
            'Net_Volga': net_volga_k,
        })

    gex_df = (
        pd.DataFrame(gex_rows)
        .sort_values('Strike')
        .reset_index(drop=True)
    )

    # Restrict to strikes with actual activity (OI or Volume > 0)
    active_df = gex_df[(gex_df['Call'] > 0) | (gex_df['Put'] > 0)].copy()
    active_df = active_df.reset_index(drop=True)

    gex_df['Cumulative_GEX'] = gex_df['Net_GEX'].cumsum()
    active_df['Cumulative_GEX'] = active_df['Net_GEX'].cumsum()

    # Flip point: zero-crossing of cumulative GEX nearest to ATM
    all_crossings = []
    for i in range(1, len(active_df)):
        prev_cum = active_df.loc[i - 1, 'Cumulative_GEX']
        curr_cum = active_df.loc[i,     'Cumulative_GEX']
        if prev_cum * curr_cum <= 0 and not (prev_cum == 0 and curr_cum == 0):
            denom = abs(prev_cum) + abs(curr_cum)
            w = abs(prev_cum) / denom if denom > 0 else 0.5
            cross = (active_df.loc[i - 1, 'Strike']
                     + w * (active_df.loc[i, 'Strike'] - active_df.loc[i - 1, 'Strike']))
            all_crossings.append(cross)

    # Pick the crossing nearest to ATM (futures_price)
    flip = None
    if all_crossings:
        flip = min(all_crossings, key=lambda x: abs(x - futures_price))

    # When no zero-crossing exists, return peak (max |value| strike)
    peak = gex_df.loc[gex_df['Net_GEX'].abs().idxmax(), 'Strike'] if flip is None else None

    # Walls
    pos_wall = (
        gex_df.loc[gex_df['Net_GEX'].idxmax(), 'Strike']
        if gex_df['Net_GEX'].max() > 0 else None
    )
    neg_wall = (
        gex_df.loc[gex_df['Net_GEX'].idxmin(), 'Strike']
        if gex_df['Net_GEX'].min() < 0 else None
    )

    return GexResult(
        flip=flip,
        pos_wall=pos_wall,
        neg_wall=neg_wall,
        gex_df=gex_df,
        peak=peak,
        net_vanna_total=net_vanna_total,
        net_volga_total=net_volga_total,
    )


def get_atm_iv(df: pd.DataFrame, futures_price: float) -> float | None:
    """Return implied volatility (Vol Settle, decimal) at the strike nearest to the futures price."""
    df_copy = df.copy()
    df_copy['_dist'] = (df_copy['Strike'] - futures_price).abs()
    closest = df_copy.nsmallest(1, '_dist')
    if closest.empty:
        return None
    return normalize_iv(closest['Vol Settle'].iloc[0])
