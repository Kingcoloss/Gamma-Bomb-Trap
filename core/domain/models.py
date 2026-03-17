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
