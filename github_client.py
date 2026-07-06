import httpx

from config import GITHUB_TOKEN

API_BASE = "https://api.github.com"


def get_pr_diff(owner, repo, pr_number):
    url = f"{API_BASE}/repos/{owner}/{repo}/pulls/{pr_number}"
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3.diff",
    }
    response = httpx.get(url, headers=headers)
    response.raise_for_status()
    return response.text


def post_comment(owner, repo, pr_number, body):
    url = f"{API_BASE}/repos/{owner}/{repo}/issues/{pr_number}/comments"
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
    }
    response = httpx.post(url, headers=headers, json={"body": body})
    response.raise_for_status()
    return response.json()
