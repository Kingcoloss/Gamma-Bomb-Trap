"""
SD Range Calculator — 1σ to 5σ Price Ranges
============================================
Supports symmetric (Rule of 16) and asymmetric (Vol Surface) ranges.
Multiple center options: ATM, Flip, DGC Wall, DGC V-GTBR, Polynomial DGC.

Dependency rules:
  - Imports from domain/ only
  - No Streamlit or framework dependencies
"""
import math

import numpy as np

from core.domain.constants import TRADING_DAYS_PER_YEAR, MAX_SIGMA_DISPLAY
from core.domain.models import SdRangeRow, SdRangeResult

# Normal distribution probabilities for 1σ–5σ
_SIGMA_PROBS = [68.27, 95.45, 99.73, 99.994, 99.99994]


def calculate_sd_ranges(
    F: float,
    atm_iv: float,
    T: float,
    center: float,
    center_label: str = "ATM",
    poly_coeffs: np.ndarray | None = None,
    max_sigma: int = MAX_SIGMA_DISPLAY,
) -> SdRangeResult:
    """Calculate 1σ–5σ price ranges (symmetric + asymmetric).

    Args:
        F: Futures price
        atm_iv: ATM implied volatility (decimal)
        T: Time to expiry (years)
        center: Mean value (ATM, DGC, Flip, etc.)
        center_label: Display label for center
        poly_coeffs: D₀…D₄ from vol surface fit (None = symmetric only)
        max_sigma: Maximum sigma level (default 5)

    Returns:
        SdRangeResult with symmetric and asymmetric ranges per σ level.
    """
    sd_base = F * atm_iv / math.sqrt(TRADING_DAYS_PER_YEAR)
    rows = []

    for n in range(1, max_sigma + 1):
        prob = _SIGMA_PROBS[n - 1] if n <= len(_SIGMA_PROBS) else 99.999999
        lo_sym = center - n * sd_base
        hi_sym = center + n * sd_base
        hi_asym = hi_sym
        lo_asym = lo_sym

        # Asymmetric bounds when Vol Surface polynomial is available
        if poly_coeffs is not None:
            from core.domain.vol_surface import eval_vol_at_delta, strike_to_delta

            delta_up = strike_to_delta(F, center + n * sd_base, T, atm_iv)
            delta_down = strike_to_delta(F, center - n * sd_base, T, atm_iv)
            iv_up = eval_vol_at_delta(poly_coeffs, delta_up)
            iv_down = eval_vol_at_delta(poly_coeffs, delta_down)
            sd_up = F * iv_up / math.sqrt(TRADING_DAYS_PER_YEAR)
            sd_down = F * iv_down / math.sqrt(TRADING_DAYS_PER_YEAR)
            hi_asym = center + n * sd_up
            lo_asym = center - n * sd_down

        rows.append(SdRangeRow(
            sigma=n,
            lo_sym=lo_sym,
            hi_sym=hi_sym,
            lo_asym=lo_asym,
            hi_asym=hi_asym,
            probability=prob,
        ))

    return SdRangeResult(
        center=center,
        center_label=center_label,
        sd_base=sd_base,
        ranges=rows,
    )
