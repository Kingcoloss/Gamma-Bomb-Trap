"""
Domain constants used across the Gamma Bomb Trap application.
"""
import math

SQRT_2PI = math.sqrt(2.0 * math.pi)

# Bangkok timezone string
TIMEZONE_BANGKOK = "Asia/Bangkok"

# Session boundary hour (10:00 Bangkok)
SESSION_START_HOUR = 6

# Session window duration in hours
SESSION_WINDOW_HOURS = 23

# GEX scaling factor
GEX_SCALE = 0.01

# Block trade detection threshold (Vol/OI GEX ratio).
# Per institutional convention: Vol/OI approaching 1:1 signals a new structural
# opening (block trade). Threshold of 1.0 flags strikes where intraday GEX flow
# equals or exceeds structural OI GEX — indicative of fresh commitment, not churn.
BLOCK_TRADE_THRESHOLD = 1.0

# Wall convergence tolerance (strike points)
WALL_CONVERGENCE_TOLERANCE = 25

# Cap on ΔIV proxy (IV_intraday − IV_OI) used in Vanna-Volga GTBR.
# Prevents extreme Vanna-term distortion during vol regime jumps.
DELTA_IV_CAP = 0.05  # 5 vol points absolute

# IV normalization floor
IV_FLOOR = 0.0001

# Auto-refresh interval (seconds)
AUTO_REFRESH_INTERVAL = 60.0

# Animation frame delay (seconds)
ANIMATION_FRAME_DELAY = 0.6
