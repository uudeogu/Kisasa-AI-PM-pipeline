from __future__ import annotations

import httpx
from ..utils.config import Config


class LinearConnector:
    """Creates and manages issues, projects, and roadmaps in Linear."""

    BASE_URL = "https://api.linear.app/graphql"

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or Config.LINEAR_API_KEY
        self.headers = {
            "Authorization": self.api_key,
            "Content-Type": "application/json",
        }

    async def _query(self, query: str, variables: dict | None = None) -> dict:
        """Execute a GraphQL query against Linear."""
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                self.BASE_URL,
                headers=self.headers,
                json={"query": query, "variables": variables or {}},
            )
            data = resp.json()
            if "errors" in data:
                raise Exception(f"Linear API error: {data['errors']}")
            return data.get("data", {})

    async def create_issue(
        self, team_id: str, title: str, description: str, priority: int = 0
    ) -> dict:
        """Create a new issue in Linear."""
        query = """
        mutation CreateIssue($input: IssueCreateInput!) {
            issueCreate(input: $input) {
                success
                issue { id identifier title url }
            }
        }
        """
        variables = {
            "input": {
                "teamId": team_id,
                "title": title,
                "description": description,
                "priority": priority,
            }
        }
        result = await self._query(query, variables)
        return result.get("issueCreate", {}).get("issue", {})

    async def create_project(self, team_ids: list[str], name: str, description: str) -> dict:
        """Create a new project in Linear."""
        query = """
        mutation CreateProject($input: ProjectCreateInput!) {
            projectCreate(input: $input) {
                success
                project { id name url }
            }
        }
        """
        variables = {
            "input": {
                "teamIds": team_ids,
                "name": name,
                "description": description,
            }
        }
        result = await self._query(query, variables)
        return result.get("projectCreate", {}).get("project", {})

    async def list_teams(self) -> list[dict]:
        """List all teams in the workspace."""
        query = """
        query { teams { nodes { id name key } } }
        """
        result = await self._query(query)
        return result.get("teams", {}).get("nodes", [])

    async def list_projects(self) -> list[dict]:
        """List all projects."""
        query = """
        query { projects { nodes { id name state { name } } } }
        """
        result = await self._query(query)
        return result.get("projects", {}).get("nodes", [])
