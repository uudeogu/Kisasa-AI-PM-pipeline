from __future__ import annotations

import httpx
from ..utils.config import Config


class NotionConnector:
    """Creates and manages pages and databases in Notion."""

    BASE_URL = "https://api.notion.com/v1"
    NOTION_VERSION = "2022-06-28"

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or Config.NOTION_API_KEY
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Notion-Version": self.NOTION_VERSION,
        }

    async def create_page(
        self, parent_id: str, title: str, content_blocks: list[dict]
    ) -> dict:
        """Create a new page in a Notion database or as a child page."""
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{self.BASE_URL}/pages",
                headers=self.headers,
                json={
                    "parent": {"database_id": parent_id},
                    "properties": {
                        "Name": {"title": [{"text": {"content": title}}]}
                    },
                    "children": content_blocks,
                },
            )
            return resp.json()

    async def query_database(
        self, database_id: str, filter_obj: dict | None = None
    ) -> list[dict]:
        """Query a Notion database with optional filters."""
        async with httpx.AsyncClient() as client:
            body = {}
            if filter_obj:
                body["filter"] = filter_obj
            resp = await client.post(
                f"{self.BASE_URL}/databases/{database_id}/query",
                headers=self.headers,
                json=body,
            )
            data = resp.json()
            return data.get("results", [])

    async def get_page(self, page_id: str) -> dict:
        """Fetch a Notion page by ID."""
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{self.BASE_URL}/pages/{page_id}",
                headers=self.headers,
            )
            return resp.json()

    async def append_blocks(self, page_id: str, blocks: list[dict]) -> dict:
        """Append content blocks to an existing Notion page."""
        async with httpx.AsyncClient() as client:
            resp = await client.patch(
                f"{self.BASE_URL}/blocks/{page_id}/children",
                headers=self.headers,
                json={"children": blocks},
            )
            return resp.json()

    @staticmethod
    def text_block(content: str) -> dict:
        """Helper to create a paragraph block."""
        return {
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [{"type": "text", "text": {"content": content}}]
            },
        }

    @staticmethod
    def heading_block(content: str, level: int = 2) -> dict:
        """Helper to create a heading block (level 1, 2, or 3)."""
        heading_type = f"heading_{level}"
        return {
            "object": "block",
            "type": heading_type,
            heading_type: {
                "rich_text": [{"type": "text", "text": {"content": content}}]
            },
        }
