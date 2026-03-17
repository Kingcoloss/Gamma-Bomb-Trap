"""
Data Helpers — Parsing and filtering session data.
No Streamlit dependency. Pure pandas/datetime logic.
"""
import re
from datetime import datetime, timedelta

import pandas as pd

from core.domain.constants import (
    TIMEZONE_BANGKOK,
    SESSION_START_HOUR,
    SESSION_WINDOW_HOURS,
)


def extract_atm(header_text: str) -> float | None:
    """Extract ATM (futures) price from CME data header."""
    match = re.search(r'vs\s+([\d\.,]+)', str(header_text))
    if match:
        return float(match.group(1).replace(',', ''))
    return None


def extract_dte(header_text: str) -> float | None:
    """Extract DTE (days to expiry) from CME data header."""
    match = re.search(r'\(([\d\.]+)\s+DTE\)', str(header_text))
    if match:
        return float(match.group(1))
    return None


def get_session_date(now: pd.Timestamp | None = None) -> 'datetime.date':
    """
    Compute the current session date in Bangkok timezone.
    Before 10:00 → yesterday's date (overnight session still active).
    """
    if now is None:
        now = pd.Timestamp.now(tz=TIMEZONE_BANGKOK)
    if now.hour < SESSION_START_HOUR:
        return (now - timedelta(days=1)).date()
    return now.date()


def get_session_start(session_date) -> pd.Timestamp:
    """Build session start timestamp for a given date."""
    return pd.Timestamp(
        year=session_date.year,
        month=session_date.month,
        day=session_date.day,
        hour=SESSION_START_HOUR, minute=0, second=0,
        tz=TIMEZONE_BANGKOK,
    )


def filter_session_data(df: pd.DataFrame, data_type: str) -> pd.DataFrame:
    """
    Filter raw CME data to the current trading session window.

    Parameters
    ----------
    df        : raw DataFrame from fetch_github_history
    data_type : "Intraday" or "OI"

    Returns
    -------
    Filtered DataFrame sorted by Datetime, or empty DataFrame.
    """
    if df is None or df.empty:
        return pd.DataFrame()

    df['Datetime'] = pd.to_datetime(df['Datetime'])
    now = pd.Timestamp.now(tz=TIMEZONE_BANGKOK)
    session_date = get_session_date(now)

    # Filter by data_type first (before time window)
    if data_type == "Intraday":
        print(f"filter_session_data: Intraday filter applied, keeping only 'Intraday Volume' rows")
        df = df[df['Header1'].str.contains("Intraday Volume", case=False, na=False)]
    elif data_type == "OI":
        df = df[df['Header1'].str.contains("Open Interest", case=False, na=False)]

    if df.empty:
        return pd.DataFrame()

    # Build time window for current session date
    start_time = (
        pd.Timestamp(datetime.combine(session_date, datetime.min.time()))
        .tz_localize(TIMEZONE_BANGKOK) + timedelta(hours=SESSION_START_HOUR)
    )
    end_time = start_time + timedelta(hours=SESSION_WINDOW_HOURS)

    df_filtered = df[(df['Datetime'] >= start_time) & (df['Datetime'] <= end_time)]

    # Fallback: if no data in today's session window (weekend / holiday),
    # use the LATEST available date's session window instead.
    if df_filtered.empty:
        latest_dt = df['Datetime'].max()
        fallback_date = latest_dt.date()
        if latest_dt.hour < SESSION_START_HOUR:
            fallback_date = fallback_date - timedelta(days=1)

        fb_start = (
            pd.Timestamp(datetime.combine(fallback_date, datetime.min.time()))
            .tz_localize(TIMEZONE_BANGKOK) + timedelta(hours=SESSION_START_HOUR)
        )
        fb_end = fb_start + timedelta(hours=SESSION_WINDOW_HOURS)
        df_filtered = df[(df['Datetime'] >= fb_start) & (df['Datetime'] <= fb_end)]
        print(f"filter_session_data: no data for session_date={session_date}, "
              f"fallback to {fallback_date} ({len(df_filtered)} rows)")

    df_filtered = df_filtered.sort_values('Datetime').reset_index(drop=True)
    return df_filtered
