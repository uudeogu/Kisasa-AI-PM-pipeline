from __future__ import annotations

import httpx
from ..utils.config import Config


class GitHubConnector:
    """Interacts with GitHub repos, PRs, and issues."""

    BASE_URL = "https://api.github.com"

    def __init__(self, token: str | None = None):
        self.token = token or Config.GITHUB_TOKEN
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/vnd.github+json",
        }

    async def list_repos(self, org: str) -> list[dict]:
        """List repositories for an organization."""
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{self.BASE_URL}/orgs/{org}/repos",
                headers=self.headers,
            )
            return resp.json()

    async def create_issue(
        self, owner: str, repo: str, title: str, body: str, labels: list[str] | None = None
    ) -> dict:
        """Create a GitHub issue."""
        async with httpx.AsyncClient() as client:
            payload = {"title": title, "body": body}
            if labels:
                payload["labels"] = labels
            resp = await client.post(
                f"{self.BASE_URL}/repos/{owner}/{repo}/issues",
                headers=self.headers,
                json=payload,
            )
            return resp.json()

    async def list_pull_requests(
        self, owner: str, repo: str, state: str = "open"
    ) -> list[dict]:
        """List pull requests for a repository."""
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{self.BASE_URL}/repos/{owner}/{repo}/pulls",
                headers=self.headers,
                params={"state": state},
            )
            return resp.json()

    async def get_pr_diff(self, owner: str, repo: str, pr_number: int) -> str:
        """Fetch the diff for a pull request."""
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{self.BASE_URL}/repos/{owner}/{repo}/pulls/{pr_number}",
                headers={**self.headers, "Accept": "application/vnd.github.diff"},
            )
            return resp.text

    async def list_actions_runs(
        self, owner: str, repo: str, status: str = ""
    ) -> list[dict]:
        """List recent GitHub Actions workflow runs."""
        async with httpx.AsyncClient() as client:
            params = {}
            if status:
                params["status"] = status
            resp = await client.get(
                f"{self.BASE_URL}/repos/{owner}/{repo}/actions/runs",
                headers=self.headers,
                params=params,
            )
            data = resp.json()
            return data.get("workflow_runs", [])
