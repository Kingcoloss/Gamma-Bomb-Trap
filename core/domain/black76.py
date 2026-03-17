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


def b76_volga(F: float, K: float, T: float, sigma: float) -> float:
    """
    Black-76 Volga (Vomma) — ∂²V/∂σ²  =  ∂Vega/∂σ

    Measures how Vega itself changes when IV changes — the "vol of vol"
    sensitivity. From Carr & Wu (2020) full PnL attribution, the Volga
    term is:  ½ · Volga · (dI)²

    Formula (r=0, Black-76):
        Volga = Vega · (d1 · d2) / σ

    where Vega = F · N′(d1) · √T  (Black-76, r=0)

    Practical meaning:
      - Volga > 0 for all options (convex in vol)
      - Largest for ATM options
      - When IV spikes: Volga amplifies the Vega P&L non-linearly
      - Short Vega + high Volga = exponential loss in IV spike
        (the "Shadow Vega" from Part 4 paper)
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
