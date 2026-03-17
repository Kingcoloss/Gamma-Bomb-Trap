"""
GitHub Data Client
==================
Fetches CME options data from GitHub repository commit history.
"""
import concurrent.futures
from io import StringIO

import pandas as pd
import requests

from core.use_cases.data_helpers import get_session_date


def fetch_github_history(
    file_path: str,
    repo: str,
    token: str = "",
    max_commits: int = 200,
) -> pd.DataFrame:
    """
    Fetch historical snapshots of a CME data file from GitHub commits.

    Parameters
    ----------
    file_path   : path within the repo (e.g. "IntradayData.txt")
    repo        : GitHub repo in "owner/repo" format
    token       : GitHub personal access token
    max_commits : maximum number of commits to retrieve
    """
    headers = {'User-Agent': 'Mozilla/5.0'}
    if token.strip():
        headers['Authorization'] = f'token {token.strip()}'

    session_date = get_session_date()

    per_page = 100
    pages_to_fetch = (max_commits // per_page) + (1 if max_commits % per_page > 0 else 0)

    def _fetch_commits(date_filter):
        """
        Collect commit metadata from the GitHub API.

        date_filter : date | None
            When set, only commits on or after this date are kept.
            When None, no date filtering is applied (fallback mode).
        """
        metadata = []
        keep_fetching = True

        for page in range(1, pages_to_fetch + 1):
            if not keep_fetching:
                break
            api_url = (
                f"https://api.github.com/repos/{repo}/commits"
                f"?path={file_path}&per_page={per_page}&page={page}"
            )
            try:
                response = requests.get(api_url, headers=headers, timeout=10)
            except Exception as e:
                print(f"Error fetching commits from GitHub: {api_url}")
                print(f"Exception: {e}")
                break

            if response.status_code != 200:
                print(f"GitHub API error: {response.status_code} for URL: {api_url}")
                break
            commits = response.json()
            if not commits:
                break

            for commit in commits:
                sha      = commit['sha']
                date_str = commit['commit']['author']['date']
                dt_raw   = pd.to_datetime(date_str)
                dt = (
                    dt_raw.tz_convert('Asia/Bangkok') if dt_raw.tzinfo
                    else dt_raw.tz_localize('UTC').tz_convert('Asia/Bangkok')
                )

                if date_filter is not None and dt.date() < date_filter:
                    keep_fetching = False
                    break

                time_label = dt.strftime("%H:%M:%S")
                metadata.append((sha, time_label, dt))

                if len(metadata) >= max_commits:
                    keep_fetching = False
                    break

        return metadata

    # Primary: fetch commits for the current session date
    commit_metadata = _fetch_commits(date_filter=session_date)

    # Fallback: if no commits today (weekend / holiday / pre-market)
    if not commit_metadata:
        print(f"fetch_github_history: no commits for session_date={session_date}, "
              f"falling back to latest {max_commits} commits")
        commit_metadata = _fetch_commits(date_filter=None)

    def download_file(meta):
        sha, time_label, dt = meta
        raw_url = f"https://raw.githubusercontent.com/{repo}/{sha}/{file_path}"
        try:
            raw_response = requests.get(raw_url, headers=headers, timeout=10)
            if raw_response.status_code == 200:
                text_data = raw_response.text
                lines = text_data.split('\n')
                h1 = lines[0].strip() if len(lines) > 0 else ""
                h2 = lines[1].strip() if len(lines) > 1 else ""
                df = pd.read_csv(StringIO(text_data), skiprows=2)
                df['Time']     = time_label
                df['Datetime'] = dt
                df['Header1']  = h1
                df['Header2']  = h2
                return df
        except Exception as ex:
            print(f"Error downloading file from GitHub: {raw_url}")
            print(f"Exception: {ex}")
        return None

    all_data = []
    if commit_metadata:
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            results = executor.map(download_file, commit_metadata)
            for res in results:
                if res is not None:
                    all_data.append(res)

    if all_data:
        return pd.concat(all_data, ignore_index=True)
    return pd.DataFrame()


def get_latest_commit_sha(
    file_path: str,
    repo: str,
    token: str = "",
) -> str | None:
    """
    Lightweight GitHub check: fetch only the latest commit SHA for a file.
    Used by auto-refresh to detect new data without downloading content.
    """
    headers = {'User-Agent': 'Mozilla/5.0'}
    if token.strip():
        headers['Authorization'] = f'token {token.strip()}'
    try:
        r = requests.get(
            f"https://api.github.com/repos/{repo}/commits?path={file_path}&per_page=1",
            headers=headers, timeout=8,
        )
        if r.status_code == 200:
            data = r.json()
            if data:
                return data[0]['sha']
    except Exception:
        pass
    return None
