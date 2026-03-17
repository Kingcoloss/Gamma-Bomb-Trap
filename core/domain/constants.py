"""
Domain constants used across the Gamma Bomb Trap application.
"""
import math

SQRT_2PI = math.sqrt(2.0 * math.pi)

# Bangkok timezone string
TIMEZONE_BANGKOK = "Asia/Bangkok"

# Session boundary hour (10:00 Bangkok)
SESSION_START_HOUR = 7

# Session window duration in hours
SESSION_WINDOW_HOURS = 21

# GEX scaling factor
GEX_SCALE = 0.01

# Block trade detection threshold (Vol/OI ratio)
BLOCK_TRADE_THRESHOLD = 2.0

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
