import httpx
import os
import contextlib
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from config import GITHUB_TOKEN

API_BASE = "https://api.github.com"


@contextlib.asynccontextmanager
async def github_mcp_session():
    """Context manager to establish a session with the GitHub MCP server."""
    if not GITHUB_TOKEN or GITHUB_TOKEN.startswith("your-"):
        yield None
        return

    server_params = StdioServerParameters(
        command="npx",
        args=["-y", "@modelcontextprotocol/server-github"],
        env={**os.environ, "GITHUB_PERSONAL_ACCESS_TOKEN": GITHUB_TOKEN}
    )

    session_established = False
    try:
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                session_established = True
                yield session
    except Exception as e:
        if not session_established:
            import sys
            print(f"Warning: Failed to connect to GitHub MCP server: {e}", file=sys.stderr)
            yield None
        else:
            raise


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
