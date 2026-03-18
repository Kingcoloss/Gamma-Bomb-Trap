"""
Vol Surface Polynomial — CME QuikVol Approach
==============================================
Fits a 4th-order polynomial to the volatility smile:

    σ(δ) = D₀ + D₁δ + D₂δ² + D₃δ³ + D₄δ⁴

Input: per-strike (Delta, IV) pairs from CME Vol Settle data.

Dependency rules:
  - Domain layer: imports only from domain/ and stdlib
  - No Streamlit or framework dependencies
"""
import math

import numpy as np
from scipy.stats import norm

from core.domain.black76 import b76_d1, normalize_iv


def strike_to_delta(
    F: float, K: float, T: float, sigma: float,
) -> float:
    """Convert strike to Black-76 call delta: N(d1).

    Args:
        F: Futures price
        K: Strike price
        T: Time to expiry (years)
        sigma: Implied volatility (decimal or percentage — auto-normalised)

    Returns:
        Call delta in [0, 1].
    """
    if T <= 0 or sigma <= 0 or F <= 0 or K <= 0:
        return 0.5
    sigma = normalize_iv(sigma)
    try:
        d1 = b76_d1(F, K, T, sigma)
        return float(norm.cdf(d1))
    except (ValueError, ZeroDivisionError):
        return 0.5


def fit_vol_surface(
    strikes: list[float],
    vol_settles: list[float],
    F: float,
    T: float,
    delta_range: tuple[float, float] = (0.05, 0.95),
    degree: int = 4,
) -> np.ndarray | None:
    """Fit polynomial σ(δ) to (strike, vol_settle) pairs.

    Uses each strike's own IV for delta conversion (not flat ATM),
    then fits a least-squares polynomial over the delta range.

    Args:
        strikes: Strike prices
        vol_settles: Vol Settle values (decimal or percentage)
        F: Futures price (ATM)
        T: Time to expiry (years)
        delta_range: (min_delta, max_delta) filter — exclude extreme wings
        degree: Polynomial degree (default 4)

    Returns:
        Polynomial coefficients [D₄, D₃, D₂, D₁, D₀] (numpy convention,
        highest degree first) or None if insufficient data.
    """
    if len(strikes) < degree + 1:
        return None

    deltas = []
    ivs = []
    for K, iv_raw in zip(strikes, vol_settles):
        iv = normalize_iv(iv_raw)
        delta = strike_to_delta(F, K, T, iv)
        if delta_range[0] <= delta <= delta_range[1]:
            deltas.append(delta)
            ivs.append(iv)

    if len(deltas) < degree + 1:
        return None

    return np.polyfit(deltas, ivs, degree)


def eval_vol_at_delta(
    coeffs: np.ndarray, delta: float,
) -> float:
    """Evaluate polynomial IV at a given delta.

    Args:
        coeffs: Polynomial coefficients from fit_vol_surface()
        delta: Call delta in [0, 1]

    Returns:
        Implied volatility (decimal).
    """
    return float(np.polyval(coeffs, delta))


def dynamic_delta_sigma(
    coeffs: np.ndarray,
    F: float,
    K_atm: float,
    T: float,
    atm_iv: float,
    delta_f: float,
) -> float:
    """Calculate Δσ(ΔF) — IV shift from polynomial for a given price move.

    Δσ = σ(δ_new) − σ(δ_old)
    where δ_new = N(d1(F+ΔF, K_ATM, σ_ATM, T))

    Cap: |Δσ| ≤ 0.10 (10% absolute — safety bound per Section 15.3)

    Args:
        coeffs: Polynomial coefficients
        F: Current futures price
        K_atm: ATM strike (usually = F)
        T: Time to expiry (years)
        atm_iv: ATM implied volatility (decimal)
        delta_f: Price move scenario

    Returns:
        IV change (capped at ±0.10).
    """
    delta_old = strike_to_delta(F, K_atm, T, atm_iv)
    iv_old = eval_vol_at_delta(coeffs, delta_old)

    F_new = F + delta_f
    if F_new <= 0:
        return 0.0
    delta_new = strike_to_delta(F_new, K_atm, T, atm_iv)
    iv_new = eval_vol_at_delta(coeffs, delta_new)

    d_sigma = iv_new - iv_old
    return max(-0.10, min(0.10, d_sigma))
