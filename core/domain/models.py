"""
Domain Models — Data classes for analysis results.
No framework dependencies. Pure Python dataclasses.
"""
from dataclasses import dataclass, field
from typing import Optional

import pandas as pd


@dataclass
class GexResult:
    """Result of calculate_gex_analysis()."""
    flip: Optional[float] = None
    pos_wall: Optional[float] = None
    neg_wall: Optional[float] = None
    gex_df: pd.DataFrame = field(default_factory=pd.DataFrame)
    peak: Optional[float] = None
    net_vanna_total: float = 0.0
    net_volga_total: float = 0.0
    # Aggregate Greeks for internally-consistent Vanna-Volga GTBR quadratic
    # (Carr & Wu 2020): Σ Γ×(Call−Put) and Σ θ×(Call−Put) across all strikes
    net_gamma_total: float = 0.0
    net_theta_total: float = 0.0
    # Symmetric PnL aggregation (Section 11): Σ Greek × (Call+Put)
    # Separate from directional GEX system — used for PnL attribution only
    net_gamma_sym: float = 0.0
    net_theta_sym: float = 0.0
    net_speed_sym: float = 0.0
    net_snap_sym: float = 0.0


@dataclass
class GtbrResult:
    """Result of calculate_gamma_theta_breakeven()."""
    lo_expiry: float = 0.0
    hi_expiry: float = 0.0
    lo_daily: float = 0.0
    hi_daily: float = 0.0


@dataclass
class VannaVolgaGtbrResult:
    """Result of calculate_vanna_adjusted_gtbr()."""
    lo_daily: float = 0.0
    hi_daily: float = 0.0
    lo_expiry: float = 0.0
    hi_expiry: float = 0.0
    shift_daily: float = 0.0
    shift_expiry: float = 0.0


@dataclass
class QuarticGtbrResult:
    """Result of quartic (4th-order) GTBR breakeven solver."""
    roots: list[float] = field(default_factory=list)
    lo_daily: float = 0.0
    hi_daily: float = 0.0
    coefficients: list[float] = field(default_factory=list)


@dataclass
class AggregateGreeks:
    """Portfolio-level Greeks with correct aggregation (Section 11).

    Symmetric (Call+Put): gamma, theta, volga, speed, snap
    Directional (Call-Put): vanna
    """
    net_gamma_sym: float = 0.0
    net_theta_sym: float = 0.0
    net_volga_sym: float = 0.0
    net_speed_sym: float = 0.0
    net_snap_sym: float = 0.0
    net_vanna_dir: float = 0.0


@dataclass
class PlayerPnL:
    """PnL result for a single participant at a given δF scenario."""
    gamma_pnl: float = 0.0
    speed_pnl: float = 0.0
    snap_pnl: float = 0.0
    theta_income: float = 0.0
    vanna_cost: float = 0.0
    volga_cost: float = 0.0
    total: float = 0.0
    sigma_zone: str = ""


@dataclass
class ParticipantPnL:
    """PnL results for all 4 participants."""
    dealer: PlayerPnL = field(default_factory=PlayerPnL)
    mm: PlayerPnL = field(default_factory=PlayerPnL)
    hf: PlayerPnL = field(default_factory=PlayerPnL)
    propfirm: PlayerPnL = field(default_factory=PlayerPnL)
    regime: str = ""
    realized_move_sigma: float = 0.0


@dataclass
class SdRangeRow:
    """Single σ-level range."""
    sigma: int = 1
    lo_sym: float = 0.0
    hi_sym: float = 0.0
    lo_asym: float = 0.0
    hi_asym: float = 0.0
    probability: float = 68.27


@dataclass
class SdRangeResult:
    """1σ–5σ price ranges."""
    center: float = 0.0
    center_label: str = ""
    sd_base: float = 0.0
    ranges: list[SdRangeRow] = field(default_factory=list)
