"""
PnL Attribution per Market Participant
=======================================
Calculates PnL for Dealer, MM, HF, and PropFirm at a given δF scenario.
Uses symmetric Greek aggregation (Section 11) for PnL accuracy.

Dependency rules:
  - Imports from domain/ only (constants, models)
  - No Streamlit or framework dependencies
"""
from core.domain.constants import TRADING_DAYS_PER_YEAR, RULE_OF_16
from core.domain.models import AggregateGreeks, PlayerPnL, ParticipantPnL


def _sigma_zone(abs_delta_f: float, daily_move: float) -> str:
    """Map |δF| to σ-zone label."""
    if daily_move <= 0:
        return ""
    ratio = abs_delta_f / daily_move
    if ratio <= 1.0:
        return "1σ Safe"
    elif ratio <= 2.0:
        return "2σ Pressure"
    elif ratio <= 3.0:
        return "3σ Kill"
    elif ratio <= 4.0:
        return "4σ Extreme"
    else:
        return "5σ+ Black Swan"


def calculate_dealer_pnl(
    greeks: AggregateGreeks,
    delta_f: float,
    delta_iv: float,
    F: float,
    atm_iv: float,
) -> PlayerPnL:
    """
    Dealer PnL (short gamma — sells options).

    PnL = −[½Γ(δF)² + ⅙Speed(δF)³ + 1/24Snap(δF)⁴]
          + |θ|/252
          − Vanna·δF·Δσ
          − ½Volga·(Δσ)²
    """
    gamma_pnl = -0.5 * greeks.net_gamma_sym * delta_f ** 2
    speed_pnl = -(1.0 / 6.0) * greeks.net_speed_sym * delta_f ** 3
    snap_pnl = -(1.0 / 24.0) * greeks.net_snap_sym * delta_f ** 4
    theta_income = abs(greeks.net_theta_sym) / TRADING_DAYS_PER_YEAR
    vanna_cost = -greeks.net_vanna_dir * delta_f * delta_iv
    volga_cost = -0.5 * greeks.net_volga_sym * delta_iv ** 2

    total = gamma_pnl + speed_pnl + snap_pnl + theta_income + vanna_cost + volga_cost
    daily_move = F * atm_iv / RULE_OF_16

    return PlayerPnL(
        gamma_pnl=gamma_pnl,
        speed_pnl=speed_pnl,
        snap_pnl=snap_pnl,
        theta_income=theta_income,
        vanna_cost=vanna_cost,
        volga_cost=volga_cost,
        total=total,
        sigma_zone=_sigma_zone(abs(delta_f), daily_move),
    )


def calculate_hf_pnl(
    greeks: AggregateGreeks,
    delta_f: float,
    delta_iv: float,
    F: float,
    atm_iv: float,
) -> PlayerPnL:
    """HF PnL (long gamma — buys options). Mirror of dealer."""
    dealer = calculate_dealer_pnl(greeks, delta_f, delta_iv, F, atm_iv)
    return PlayerPnL(
        gamma_pnl=-dealer.gamma_pnl,
        speed_pnl=-dealer.speed_pnl,
        snap_pnl=-dealer.snap_pnl,
        theta_income=-dealer.theta_income,
        vanna_cost=-dealer.vanna_cost,
        volga_cost=-dealer.volga_cost,
        total=-dealer.total,
        sigma_zone=dealer.sigma_zone,
    )


def calculate_propfirm_pnl(
    delta_f: float,
    F: float,
    atm_iv: float,
    lot_size: int = 1,
) -> PlayerPnL:
    """PropFirm PnL (directional futures, no permanent book)."""
    daily_move = F * atm_iv / RULE_OF_16
    total = abs(delta_f) * lot_size
    return PlayerPnL(
        gamma_pnl=total,
        total=total,
        sigma_zone=_sigma_zone(abs(delta_f), daily_move),
    )


def calculate_all_participants(
    greeks: AggregateGreeks,
    delta_f: float,
    delta_iv: float,
    F: float,
    atm_iv: float,
    net_composite_gex: float,
) -> ParticipantPnL:
    """Calculate PnL for all 4 participants at given scenario."""
    daily_move = F * atm_iv / RULE_OF_16
    regime = "LONG γ" if net_composite_gex >= 0 else "SHORT γ"

    return ParticipantPnL(
        dealer=calculate_dealer_pnl(greeks, delta_f, delta_iv, F, atm_iv),
        mm=calculate_dealer_pnl(greeks, delta_f, delta_iv, F, atm_iv),
        hf=calculate_hf_pnl(greeks, delta_f, delta_iv, F, atm_iv),
        propfirm=calculate_propfirm_pnl(delta_f, F, atm_iv),
        regime=regime,
        realized_move_sigma=abs(delta_f) / daily_move if daily_move > 0 else 0.0,
    )
