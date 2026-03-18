"""
Black-76 Pricing Engine (Options on Futures)
=============================================

Black-76 (Black's Model) is the correct model for European options
written on futures contracts (GC / OG gold futures on CME).

Core distinction vs Black-Scholes:
  - No cost-of-carry — futures price F already discounts the forward
  - d1 = [ ln(F/K) + ½σ²T ] / (σ√T)   ← no risk-free rate in numerator
  - d2 = d1 − σ√T

Key Greeks:
  Gamma  = e^(−rT) · N′(d1) / (F · σ · √T)
  Theta  = −e^(−rT) · F · σ · N′(d1) / (2√T) − r·C        (call)

For relative GEX comparisons the e^(−rT) discount is common to every
strike and cancels, so r = 0 is used throughout.
"""
import math

from core.domain.constants import SQRT_2PI, IV_FLOOR


def norm_pdf(x: float) -> float:
    """Standard normal probability density function."""
    return math.exp(-0.5 * x * x) / SQRT_2PI


def b76_d1(F: float, K: float, T: float, sigma: float) -> float:
    """Black-76 d1: ln(F/K) term only — no risk-free drift."""
    return (math.log(F / K) + 0.5 * sigma ** 2 * T) / (sigma * math.sqrt(T))


def b76_gamma(F: float, K: float, T: float, sigma: float) -> float:
    """
    Black-76 Gamma for a European option on a futures contract (r = 0).

        Γ = N′(d1) / (F · σ · √T)

    F     : futures price (ATM from header)
    K     : strike price
    T     : time to expiry in years  (DTE / 365)
    sigma : implied volatility, decimal form
    """
    if T <= 0 or sigma <= 0 or F <= 0 or K <= 0:
        return 0.0
    try:
        d1 = b76_d1(F, K, T, sigma)
        return norm_pdf(d1) / (F * sigma * math.sqrt(T))
    except (ValueError, ZeroDivisionError):
        return 0.0


def normalize_iv(sigma_raw: float) -> float:
    """
    Normalize implied volatility to decimal form.
    CME Vol Settle may arrive as decimal (0.414) or percentage (41.4).
    If sigma > 1.0 it is treated as percentage and divided by 100.
    A minimum floor prevents division-by-zero in Greeks.
    """
    sigma = float(sigma_raw)
    if sigma > 1.0:
        sigma /= 100.0
    return max(sigma, IV_FLOOR)


def b76_vanna(F: float, K: float, T: float, sigma: float) -> float:
    """
    Black-76 Vanna — ∂Δ/∂σ  (sensitivity of delta to IV change).

    Vanna = −e^(−rT) · N′(d1) · d2 / σ

    With r = 0 (relative GEX convention):
        Vanna = −N′(d1) · d2 / σ

    Theory (from project papers):
      Carr & Wu (2020) full PnL attribution:
        dPnL = θ·dt + Δ·dS + ν·dI + ½Γ(dS)² + ½Volga(dI)² + Vanna(dS)(dI)

    In practical terms for dealer hedging:
      - When IV rises (dI > 0) and price falls (dS < 0):
        Vanna PnL = Vanna × (−) × (+) = negative additional loss
        → Dealer forced to sell MORE futures than gamma alone predicts

      - When IV falls (dI < 0) and price rises (dS > 0):
        Vanna PnL contribution reduces hedging pressure
    """
    if T <= 0 or sigma <= 0 or F <= 0 or K <= 0:
        return 0.0
    try:
        d1 = b76_d1(F, K, T, sigma)
        d2 = d1 - sigma * math.sqrt(T)
        return -norm_pdf(d1) * d2 / sigma
    except (ValueError, ZeroDivisionError):
        return 0.0


def b76_theta_atm(F: float, sigma: float, T: float) -> float:
    """
    Black-76 ATM Theta (annualised, r=0).
    θ_ATM ≈ −F · σ · N′(0) / (2√T)
    At ATM: d1 ≈ ½σ√T ≈ 0 for short DTE, so N′(d1) ≈ N′(0).
    """
    if T <= 0 or sigma <= 0 or F <= 0:
        return 0.0
    return -F * sigma * norm_pdf(0.0) / (2.0 * math.sqrt(T))


def b76_theta(F: float, K: float, T: float, sigma: float) -> float:
    """
    Black-76 Theta for arbitrary strike K (annualised, r=0).

        θ(F,K,T,σ) = −F · σ · N′(d1) / (2√T)

    General form of b76_theta_atm — works for any K, not just ATM.
    When K = F (ATM), d1 ≈ 0 for short DTE and N′(d1) → N′(0),
    reducing exactly to b76_theta_atm.

    Used for aggregate net_theta_total across all strikes so that
    the Vanna-Volga GTBR quadratic (Carr & Wu 2020) is internally
    consistent — all coefficients (a, b, c) at the same portfolio level.
    """
    if T <= 0 or sigma <= 0 or F <= 0 or K <= 0:
        return 0.0
    try:
        d1 = b76_d1(F, K, T, sigma)
        return -F * sigma * norm_pdf(d1) / (2.0 * math.sqrt(T))
    except (ValueError, ZeroDivisionError):
        return 0.0


def b76_volga(F: float, K: float, T: float, sigma: float) -> float:
    """
    Black-76 Volga (Vomma) — ∂²V/∂σ²  =  ∂Vega/∂σ

    Measures how Vega itself changes when IV changes — the "vol of vol"
    sensitivity. From Carr & Wu (2020) full PnL attribution, the Volga
    term is:  ½ · Volga · (dI)²

    Formula (r=0, Black-76):
        Volga = Vega · (d1 · d2) / σ

    where Vega = F · N′(d1) · √T  (Black-76, r=0)

    Sign behaviour (d1·d2 term):
      - ATM (K≈F): d1=+½σ√T, d2=−½σ√T → d1·d2 < 0 → Volga < 0 (Vega is at its
        peak so its slope is near-zero / slightly negative)
      - OTM (same-sign d1,d2): d1·d2 > 0 → Volga > 0; largest in the wings
      - Volga is NOT universally positive; it is zero at ATM and positive only OTM

    Practical meaning:
      - OTM options: Volga > 0 — Vega increases as IV rises ("convex in vol")
      - ATM options: Volga ≈ 0 (minimum of Volga curve)
      - When IV spikes: OTM Volga explodes, making short-wing positions far more
        expensive than originally modelled ("Shadow Vega" from Part 4 paper)
    """
    if T <= 0 or sigma <= 0 or F <= 0 or K <= 0:
        return 0.0
    try:
        d1 = b76_d1(F, K, T, sigma)
        d2 = d1 - sigma * math.sqrt(T)
        vega = F * norm_pdf(d1) * math.sqrt(T)
        return vega * d1 * d2 / sigma
    except (ValueError, ZeroDivisionError):
        return 0.0


def b76_speed(F: float, K: float, T: float, sigma: float) -> float:
    """
    Black-76 Speed — dΓ/dF (3rd derivative of option price w.r.t. F).

        Speed = −Γ/F · [1 + d₁/(σ√T)]

    Measures how Gamma itself changes as the underlying moves.
    Used in quartic PnL Taylor expansion (⅙·Speed·δF³ term).
    """
    if T <= 0 or sigma <= 0 or F <= 0 or K <= 0:
        return 0.0
    try:
        sigma = normalize_iv(sigma)
        d1 = b76_d1(F, K, T, sigma)
        gamma = b76_gamma(F, K, T, sigma)
        sqrt_T = math.sqrt(T)
        return -gamma / F * (1.0 + d1 / (sigma * sqrt_T))
    except (ValueError, ZeroDivisionError):
        return 0.0


def b76_snap(F: float, K: float, T: float, sigma: float) -> float:
    """
    Black-76 Snap — d(Speed)/dF (4th derivative of option price w.r.t. F).

        Snap = Γ/F² · [(d₁² − 1)/(σ²T) + 3·d₁/(F·σ√T) + 2/F²]

    Highest-order Greek in the quartic PnL expansion (1/24·Snap·δF⁴ term).
    """
    if T <= 0 or sigma <= 0 or F <= 0 or K <= 0:
        return 0.0
    try:
        sigma = normalize_iv(sigma)
        d1 = b76_d1(F, K, T, sigma)
        gamma = b76_gamma(F, K, T, sigma)
        sqrt_T = math.sqrt(T)
        sig_sqrtT = sigma * sqrt_T

        term1 = (d1 * d1 - 1.0) / (sigma * sigma * T)
        term2 = 3.0 * d1 / (F * sig_sqrtT)
        term3 = 2.0 / (F * F)
        return gamma / (F * F) * (term1 + term2 + term3)
    except (ValueError, ZeroDivisionError):
        return 0.0
