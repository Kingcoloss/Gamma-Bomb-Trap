"""
Chart Helper Functions
======================
Plotly vertical line helpers for GEX, GTBR, and ATM annotations.
"""


def add_gex_vlines(fig, gex_flip, pos_wall, neg_wall, label: str = "GEX"):
    """Add Gamma structural vertical lines to a Plotly figure.

    label : "GEX" for OI-based Gamma Exposure,
            "γ-Flow" for volume-weighted Gamma Flow.
    """
    if gex_flip is not None:
        fig.add_vline(
            x=gex_flip,
            line_dash="dot",
            line_color="#A855F7",
            line_width=2,
            opacity=0.9,
            annotation_text=f"{label} Flip",
            annotation_position="top right",
            annotation_font=dict(color="#A855F7", size=11),
        )
    if pos_wall is not None:
        fig.add_vline(
            x=pos_wall,
            line_dash="dashdot",
            line_color="#22C55E",
            line_width=1.5,
            opacity=0.7,
            annotation_text=f"+{label} Wall",
            annotation_position="top left",
            annotation_font=dict(color="#22C55E", size=10),
        )
    if neg_wall is not None:
        fig.add_vline(
            x=neg_wall,
            line_dash="dashdot",
            line_color="#F43F5E",
            line_width=1.5,
            opacity=0.7,
            annotation_text=f"-{label} Wall",
            annotation_position="top right",
            annotation_font=dict(color="#F43F5E", size=10),
        )


def add_theta_breakeven_vlines(fig, lo_exp, hi_exp, lo_day, hi_day):
    """
    Add Black-76 Gamma-Theta Breakeven vertical lines.

    Expiry range  (orange solid)  : F ± F·σ·√(DTE/365)
    Daily  range  (amber dotted)  : F ± F·σ/√365
    """
    for x_val, label, pos in [
        (lo_exp, "γ/θ Exp↓", "bottom left"),
        (hi_exp, "γ/θ Exp↑", "bottom right"),
    ]:
        fig.add_vline(
            x=x_val,
            line_dash="dash",
            line_color="#FB923C",
            line_width=2,
            opacity=0.9,
            annotation_text=label,
            annotation_position=pos,
            annotation_font=dict(color="#FB923C", size=10),
        )
    for x_val, label, pos in [
        (lo_day, "γ/θ 1D↓", "top left"),
        (hi_day, "γ/θ 1D↑", "top right"),
    ]:
        fig.add_vline(
            x=x_val,
            line_dash="dot",
            line_color="#FCD34D",
            line_width=1.5,
            opacity=0.75,
            annotation_text=label,
            annotation_position=pos,
            annotation_font=dict(color="#FCD34D", size=9),
        )


def add_atm_vline(fig, atm):
    """Add ATM vertical line."""
    fig.add_vline(
        x=atm,
        line_dash="dash",
        line_color="#888888",
        opacity=0.8,
        annotation_text="ATM",
        annotation_position="top",
    )
