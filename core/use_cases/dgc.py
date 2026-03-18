"""
Polynomial DGC — Dealer Gravity Center via Vol Surface
=======================================================
Finds the ΔF that maximises the dealer's portfolio PnL using
the vol-surface polynomial for dynamic Δσ(ΔF).

    DGC = F + ΔF*  where  dPnL/dΔF = 0

When Skew = 0, DGC collapses back to F (symmetric).

Dependency rules:
  - Imports from domain/ and use_cases/ only
  - No Streamlit or framework dependencies
"""
import math

import numpy as np
from scipy.optimize import minimize_scalar

from core.domain.black76 import (
    b76_gamma,
    b76_theta,
    b76_vanna,
    b76_volga,
    normalize_iv,
)
from core.domain.vol_surface import dynamic_delta_sigma
from core.domain.constants import TRADING_DAYS_PER_YEAR


def _portfolio_pnl(
    delta_f: float,
    strikes: list[float],
    calls: list[float],
    puts: list[float],
    ivs: list[float],
    F: float,
    T: float,
    poly_coeffs: np.ndarray,
) -> float:
    """Evaluate portfolio PnL at a given δF scenario (Section 11.3).

    PnL(ΔF) = Σ_K [
        (θ_K/T_basis + ½Γ_K·(ΔF)² + ½Volga_K·(Δσ_K)²) × (Call+Put)
      + (Vanna_K · ΔF · Δσ_K) × (Call−Put)
    ]

    DGC = where dealer (short gamma) has max PnL = where long portfolio
    PnL is minimised. Returns total directly so scipy.minimize finds
    the long-portfolio PnL minimum (= dealer optimum).
    """
    total = 0.0
    atm_iv = normalize_iv(ivs[len(ivs) // 2]) if ivs else 0.20

    for K, call, put, iv_raw in zip(strikes, calls, puts, ivs):
        iv = normalize_iv(iv_raw)
        if iv < 0.001 or (call + put) == 0:
            continue

        gamma_k = b76_gamma(F, K, T, iv)
        theta_k = b76_theta(F, K, T, iv)
        vanna_k = b76_vanna(F, K, T, iv)
        volga_k = b76_volga(F, K, T, iv)

        # Dynamic Δσ at this strike
        d_sigma = dynamic_delta_sigma(poly_coeffs, F, K, T, atm_iv, delta_f)

        # Symmetric terms × (Call + Put)
        sym = (call + put) * (
            theta_k / TRADING_DAYS_PER_YEAR
            + 0.5 * gamma_k * delta_f ** 2
            + 0.5 * volga_k * d_sigma ** 2
        )

        # Directional term × (Call − Put)
        dir_term = (call - put) * vanna_k * delta_f * d_sigma

        total += sym + dir_term

    # Long portfolio PnL: θ (negative) + ½Γ(ΔF)² (positive for movement).
    # Dealer (short gamma) PnL = −total. Minimising total = maximising dealer PnL.
    return total


def calculate_polynomial_dgc(
    strikes: list[float],
    calls: list[float],
    puts: list[float],
    ivs: list[float],
    F: float,
    T: float,
    poly_coeffs: np.ndarray,
    search_range: float | None = None,
) -> float | None:
    """Find Polynomial DGC — the ΔF* that minimises long-portfolio PnL
    (= maximises dealer PnL).

    Uses scipy.optimize.minimize_scalar with Brent's method.

    Args:
        strikes: Strike prices with active OI
        calls: Call OI per strike
        puts: Put OI per strike
        ivs: Vol Settle per strike (decimal or percentage)
        F: Futures price (ATM)
        T: Time to expiry (years)
        poly_coeffs: Vol surface polynomial coefficients
        search_range: Search bound in price points (default ±3σ)

    Returns:
        DGC price (F + ΔF*), or None if optimisation fails.
    """
    if len(strikes) < 3 or T <= 0:
        return None

    atm_iv = normalize_iv(ivs[len(ivs) // 2]) if ivs else 0.20

    if search_range is None:
        # Default: ±3σ daily move
        search_range = 3.0 * F * atm_iv / math.sqrt(TRADING_DAYS_PER_YEAR)

    try:
        result = minimize_scalar(
            _portfolio_pnl,
            bounds=(-search_range, search_range),
            method='bounded',
            args=(strikes, calls, puts, ivs, F, T, poly_coeffs),
        )
        if result.success:
            dgc = F + result.x
            # Sanity: DGC should be within reasonable range of ATM
            if abs(dgc - F) > search_range * 1.5:
                return None
            return dgc
    except (ValueError, RuntimeError):
        pass

    return None
