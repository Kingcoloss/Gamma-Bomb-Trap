"""
Session State Manager
=====================
Encapsulates Streamlit session state logic for data persistence.
"""
import time

import pandas as pd
import streamlit as st

from core.use_cases.data_helpers import get_session_date, get_session_start
from core.infrastructure.github_client import fetch_github_history
from core.use_cases.data_helpers import filter_session_data


class SessionManager:
    """
    Manages Streamlit session state for the GBT dashboard.
    Handles initialization, staleness detection, and data refresh.
    """

    # Session state key names
    KEY_INTRADAY = 'my_intraday_data'
    KEY_OI = 'my_oi_data'
    KEY_LAST_FETCH = 'last_fetch_datetime'
    KEY_IS_PLAYING = 'is_playing'
    KEY_ANIM_IDX = 'anim_idx'
    KEY_FOCUS_SLIDER = 'focus_slider'
    KEY_FETCH_MODE = 'fetch_mode'
    KEY_LAST_AUTO_CHECK = 'last_auto_check'
    KEY_SHA_INTRA = 'sha_intra'
    KEY_SHA_OI = 'sha_oi'
    KEY_SELECTED_TIME = 'selected_time_state'
    KEY_PNL_VIEW = 'pnl_view'

    def __init__(self, repo: str, token: str):
        self.repo = repo
        self.token = token
        self._init_defaults()

    def _init_defaults(self):
        """Initialize all session state keys with defaults if not present."""
        defaults = {
            self.KEY_IS_PLAYING: False,
            self.KEY_ANIM_IDX: 0,
            self.KEY_FOCUS_SLIDER: False,
            self.KEY_FETCH_MODE: "📋 Manual",
            self.KEY_LAST_AUTO_CHECK: 0.0,
            self.KEY_SHA_INTRA: None,
            self.KEY_SHA_OI: None,
            self.KEY_LAST_FETCH: None,
            self.KEY_PNL_VIEW: "PropFirm Trader",
        }
        for key, default in defaults.items():
            if key not in st.session_state:
                st.session_state[key] = default

    def _get_data_last_fetch_dt(self) -> pd.Timestamp | None:
        """Return the max Datetime from intraday data as the last-fetch marker."""
        if (self.KEY_INTRADAY in st.session_state
                and not st.session_state[self.KEY_INTRADAY].empty):
            return st.session_state[self.KEY_INTRADAY]['Datetime'].max()
        return None

    @property
    def is_data_stale(self) -> bool:
        """Check if cached data is older than the current session start."""
        last_fetch = st.session_state.get(self.KEY_LAST_FETCH)
        if last_fetch is None or not hasattr(last_fetch, 'date'):
            return False
        session_start = get_session_start(get_session_date())
        return last_fetch < session_start

    @property
    def needs_intraday(self) -> bool:
        return (self.KEY_INTRADAY not in st.session_state
                or st.session_state[self.KEY_INTRADAY].empty)

    @property
    def needs_oi(self) -> bool:
        return (self.KEY_OI not in st.session_state
                or st.session_state[self.KEY_OI].empty)

    @property
    def df_intraday(self) -> pd.DataFrame:
        return st.session_state.get(self.KEY_INTRADAY, pd.DataFrame())

    @property
    def df_oi(self) -> pd.DataFrame:
        return st.session_state.get(self.KEY_OI, pd.DataFrame())

    @property
    def fetch_mode(self) -> str:
        return st.session_state.get(self.KEY_FETCH_MODE, "📋 Manual")

    def handle_stale_data(self):
        """Re-fetch both datasets if data is stale (date rollover)."""
        if not self.is_data_stale:
            return
        if self.KEY_INTRADAY not in st.session_state and self.KEY_OI not in st.session_state:
            return

        raw_intra = fetch_github_history("IntradayData.txt", self.repo, self.token, max_commits=200)
        raw_oi    = fetch_github_history("OIData.txt", self.repo, self.token, max_commits=1)
        st.session_state[self.KEY_INTRADAY] = filter_session_data(raw_intra, "Intraday")
        st.session_state[self.KEY_OI]       = filter_session_data(raw_oi, "OI")
        st.session_state[self.KEY_LAST_FETCH] = self._get_data_last_fetch_dt()
        st.session_state[self.KEY_SHA_INTRA] = None
        st.session_state[self.KEY_SHA_OI]    = None
        st.session_state[self.KEY_LAST_AUTO_CHECK] = 0.0

    def handle_initial_load(self):
        """Fetch each dataset independently if missing or empty."""
        need_intra = self.needs_intraday
        need_oi = self.needs_oi

        if not need_intra and not need_oi:
            return

        if need_intra:
            raw_intra = fetch_github_history("IntradayData.txt", self.repo, self.token, max_commits=10)
            st.session_state[self.KEY_INTRADAY] = filter_session_data(raw_intra, "Intraday")
            print(f"Initial intraday load: rows={len(raw_intra)}")

        if need_oi:
            raw_oi = fetch_github_history("OIData.txt", self.repo, self.token, max_commits=1)
            st.session_state[self.KEY_OI] = filter_session_data(raw_oi, "OI")
            print(f"Initial OI load: rows={len(raw_oi)}")

        st.session_state[self.KEY_LAST_FETCH] = self._get_data_last_fetch_dt()
        print(f"last_fetch_dt={st.session_state[self.KEY_LAST_FETCH]}")

    def manual_refresh(self):
        """Perform a full manual refresh of all data."""
        raw_intra = fetch_github_history("IntradayData.txt", self.repo, self.token, max_commits=200)
        raw_oi    = fetch_github_history("OIData.txt", self.repo, self.token, max_commits=1)
        st.session_state[self.KEY_INTRADAY] = filter_session_data(raw_intra, "Intraday")
        st.session_state[self.KEY_OI]       = filter_session_data(raw_oi, "OI")
        st.session_state[self.KEY_LAST_FETCH] = self._get_data_last_fetch_dt()

        if self.KEY_SELECTED_TIME in st.session_state:
            del st.session_state[self.KEY_SELECTED_TIME]
        st.session_state[self.KEY_IS_PLAYING] = False
        st.session_state[self.KEY_LAST_AUTO_CHECK] = 0.0
