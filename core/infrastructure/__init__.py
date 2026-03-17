# Infrastructure Layer — External services, data fetching, state management
#
# Note: SessionManager depends on Streamlit and should be imported directly
# where needed (from core.infrastructure.session_manager import SessionManager).
# github_client is framework-agnostic.
from core.infrastructure.github_client import (
    fetch_github_history,
    get_latest_commit_sha,
)
