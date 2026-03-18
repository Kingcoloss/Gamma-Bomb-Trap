"""
Gamma-Theta Breakeven Range (GTBR) Calculations
=================================================
Standard GTBR, Vanna-Volga Adjusted GTBR, Rule of 16, and Quartic solver.
"""
import math

import numpy as np

from core.domain.black76 import b76_gamma, b76_theta_atm, normalize_iv
from core.domain.models import GtbrResult, VannaVolgaGtbrResult, QuarticGtbrResult
from core.domain.constants import TRADING_DAYS_PER_YEAR


def calculate_gamma_theta_breakeven(
    F: float, atm_iv: float, dte: float,
) -> GtbrResult:
    """
    Black-76 Gamma-Theta Breakeven Range.

    Reference: Silic & Poulsen (2021) eq. 27-28; Bossu et al. (2005).

    For 1 calendar day  (Δt = 1/365):
      ΔF_daily  = F · σ / √365

    For remaining life  (Δt = DTE/365):
      ΔF_expiry = F · σ · √(DTE / 365)
    """
    T = max(dte / 365.0, 1e-10)

    delta_expiry = F * atm_iv * math.sqrt(T)
    delta_daily  = F * atm_iv / math.sqrt(365.0)

    return GtbrResult(
        lo_expiry=F - delta_expiry,
        hi_expiry=F + delta_expiry,
        lo_daily=F - delta_daily,
        hi_daily=F + delta_daily,
    )


def calculate_vanna_adjusted_gtbr(
    F: float, atm_iv: float, dte: float,
    net_vanna: float, net_volga: float, delta_iv: float,
    net_gamma: float | None = None,
    net_theta: float | None = None,
) -> VannaVolgaGtbrResult:
    """
    Vanna + Volga Adjusted Gamma-Theta Breakeven Range.

    Matches the FULL Carr & Wu (2020) PnL attribution (Appendix A1):

      dPnL = Theta·dt + Delta·dS + Vega·dI
             + ½·Gamma·(dS)² + ½·Volga·(dI)² + Vanna·(dS)·(dI)

    For a delta-hedged portfolio (Delta term = 0), setting PnL = 0:

      0 = θ/365 + ½·Γ·(ΔF)² + Vanna·(ΔF)·(Δσ) + ½·Volga·(Δσ)²

    Rearranging as quadratic in ΔF:

      a·(ΔF)² + b·(ΔF) + c = 0

    where:
      a = ½ · Γ
      b = Vanna · Δσ               (cross-derivative, no ½)
      c = θ/365 + ½ · Volga · (Δσ)²

    Aggregate Greeks (net_gamma, net_theta):
    ----------------------------------------
    When net_gamma and net_theta are provided (from GexResult.net_gamma_total /
    net_theta_total), all four quadratic coefficients use portfolio-aggregate
    values — internally consistent per Carr & Wu (2020):
        a = ½ · net_gamma_total          (aggregate, directional)
        b = net_vanna_total · Δσ         (aggregate, directional)
        c = net_theta_total/365 + ½ · net_volga_total · (Δσ)²

    Falls back to ATM-local Gamma/Theta when not provided (legacy behaviour).
    """
    T = max(dte / 365.0, 1e-10)

    # Prefer aggregate Greeks for internal consistency (Carr & Wu 2020).
    # Fall back to ATM-local when aggregate not available.
    if net_gamma is not None and net_gamma != 0.0:
        gamma_used = net_gamma
        theta_used = net_theta if net_theta is not None else b76_theta_atm(F, atm_iv, T)
    else:
        gamma_used = b76_gamma(F, F, T, atm_iv)
        theta_used = b76_theta_atm(F, atm_iv, T)

    if gamma_used == 0:
        d_exp = F * atm_iv * math.sqrt(T)
        d_day = F * atm_iv / math.sqrt(365.0)
        return VannaVolgaGtbrResult(
            lo_daily=F - d_day, hi_daily=F + d_day,
            lo_expiry=F - d_exp, hi_expiry=F + d_exp,
            shift_daily=0.0, shift_expiry=0.0,
        )

    # Daily (Δt = 1/365)
    theta_daily = theta_used / 365.0
    volga_pnl_daily = 0.5 * net_volga * delta_iv * delta_iv

    a_d = 0.5 * gamma_used
    b_d = net_vanna * delta_iv
    c_d = theta_daily + volga_pnl_daily

    disc_d = b_d * b_d - 4.0 * a_d * c_d

    if disc_d < 0 or a_d == 0:
        d_day = F * atm_iv / math.sqrt(365.0)
        lo_d, hi_d = F - d_day, F + d_day
        shift_d = 0.0
    else:
        sqrt_disc = math.sqrt(disc_d)
        root1 = (-b_d + sqrt_disc) / (2.0 * a_d)
        root2 = (-b_d - sqrt_disc) / (2.0 * a_d)
        lo_d = F + min(root1, root2)
        hi_d = F + max(root1, root2)
        shift_d = (lo_d + hi_d) / 2.0 - F

    # Expiry (Δt = T)
    theta_expiry = theta_used * T
    delta_iv_expiry = delta_iv * math.sqrt(dte / 365.0) if dte > 0 else 0.0
    volga_pnl_expiry = 0.5 * net_volga * delta_iv_expiry * delta_iv_expiry

    a_e = 0.5 * gamma_used
    b_e = net_vanna * delta_iv_expiry
    c_e = theta_expiry + volga_pnl_expiry

    disc_e = b_e * b_e - 4.0 * a_e * c_e

    if disc_e < 0 or a_e == 0:
        d_exp = F * atm_iv * math.sqrt(T)
        lo_e, hi_e = F - d_exp, F + d_exp
        shift_e = 0.0
    else:
        sqrt_disc_e = math.sqrt(disc_e)
        root1_e = (-b_e + sqrt_disc_e) / (2.0 * a_e)
        root2_e = (-b_e - sqrt_disc_e) / (2.0 * a_e)
        lo_e = F + min(root1_e, root2_e)
        hi_e = F + max(root1_e, root2_e)
        shift_e = (lo_e + hi_e) / 2.0 - F

    return VannaVolgaGtbrResult(
        lo_daily=lo_d, hi_daily=hi_d,
        lo_expiry=lo_e, hi_expiry=hi_e,
        shift_daily=shift_d, shift_expiry=shift_e,
    )


def calculate_gtbr_rule16(
    F: float,
    atm_iv: float,
) -> tuple[float, float, float]:
    """
    Rule of 16: Expected daily move on trading-day basis.

    ΔF_daily = F × σ / √252  (≈ F × σ / 16)

    Returns:
        (lo, hi, daily_move)
    """
    sigma = normalize_iv(atm_iv)
    daily_move = F * sigma / math.sqrt(TRADING_DAYS_PER_YEAR)
    return (F - daily_move, F + daily_move, daily_move)


def calculate_quartic_gtbr(
    net_gamma: float,
    net_speed: float,
    net_snap: float,
    net_theta: float,
    net_vanna: float,
    net_volga: float,
    delta_iv: float,
    F: float,
) -> QuarticGtbrResult:
    """
    Quartic PnL breakeven solver (4th-order Taylor expansion).

    Solves: a₄(δF)⁴ + a₃(δF)³ + a₂(δF)² + a₁(δF) + a₀ = 0

    Coefficients:
        a₄ = 1/24 · net_snap
        a₃ = 1/6  · net_speed
        a₂ = 1/2  · net_gamma
        a₁ = net_vanna · Δσ
        a₀ = net_theta/252 + 1/2 · net_volga · (Δσ)²

    Uses symmetric Greeks (Call+Put aggregation) for PnL accuracy.
    Falls back to empty result if no real roots found.
    """
    a4 = net_snap / 24.0
    a3 = net_speed / 6.0
    a2 = net_gamma / 2.0
    a1 = net_vanna * delta_iv
    a0 = net_theta / TRADING_DAYS_PER_YEAR + 0.5 * net_volga * delta_iv ** 2

    coeffs = [a4, a3, a2, a1, a0]

    # Handle degenerate case: all leading coefficients zero
    if a4 == 0 and a3 == 0 and a2 == 0:
        return QuarticGtbrResult(coefficients=coeffs)

    roots_complex = np.roots(coeffs)
    real_roots = sorted([r.real for r in roots_complex if abs(r.imag) < 1e-8])

    if not real_roots:
        return QuarticGtbrResult(coefficients=coeffs)

    lo = min(real_roots)
    hi = max(real_roots)

    return QuarticGtbrResult(
        roots=real_roots,
        lo_daily=F + lo,
        hi_daily=F + hi,
        coefficients=coeffs,
    )
