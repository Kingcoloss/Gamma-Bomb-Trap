import base64

import requests

BASE_URL = "https://api.github.com"


async def FetchDataFromGithubAPI(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
        return None


def get_file(owner: str, repo: str, path: str, token: str, ref: str | None = None) -> dict | None:
    """Get a file from a GitHub public repo using a personal access token.

    Uses: GET /repos/{owner}/{repo}/contents/{path}
    Docs: https://docs.github.com/en/rest/repos/contents#get-repository-content

    Args:
        owner: Repository owner (user or org).
        repo:  Repository name.
        path:  Path to the file inside the repo (e.g. "src/main.py").
        token: GitHub personal access token.
        ref:   Optional git ref (branch, tag, or commit SHA). Defaults to the repo's default branch.

    Returns:
        A dict with "content" (decoded text), "sha", "size", "path", "encoding",
        and the full raw API "response" — or None on error.
    """
    url = f"{BASE_URL}/repos/{owner}/{repo}/contents/{path}"
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    params = {}
    if ref is not None:
        params["ref"] = ref

    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()

        if isinstance(data, list):
            # The path points to a directory, not a file.
            return {"type": "dir", "entries": data}

        content = ""
        if data.get("encoding") == "base64" and data.get("content"):
            content = base64.b64decode(data["content"]).decode("utf-8")

        return {
            "content": content,
            "sha": data.get("sha"),
            "size": data.get("size"),
            "path": data.get("path"),
            "encoding": data.get("encoding"),
            "download_url": data.get("download_url"),
            "response": data,
        }
    except requests.exceptions.HTTPError as e:
        print(f"GitHub API error ({response.status_code}): {e}")
        return None
    except requests.exceptions.RequestException as e:
        print(f"Request error: {e}")
        return None
