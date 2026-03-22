from __future__ import annotations

import httpx
from ..utils.config import Config


class SlackConnector:
    """Fetches conversations from Slack channels and DMs."""

    BASE_URL = "https://slack.com/api"

    def __init__(self, token: str | None = None):
        self.token = token or Config.SLACK_BOT_TOKEN
        self.headers = {"Authorization": f"Bearer {self.token}"}

    async def fetch_channel_history(
        self, channel_id: str, limit: int = 100
    ) -> list[dict]:
        """Fetch recent messages from a Slack channel."""
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{self.BASE_URL}/conversations.history",
                headers=self.headers,
                params={"channel": channel_id, "limit": limit},
            )
            data = resp.json()
            if not data.get("ok"):
                raise Exception(f"Slack API error: {data.get('error')}")
            return data.get("messages", [])

    async def fetch_thread(self, channel_id: str, thread_ts: str) -> list[dict]:
        """Fetch all replies in a Slack thread."""
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{self.BASE_URL}/conversations.replies",
                headers=self.headers,
                params={"channel": channel_id, "ts": thread_ts},
            )
            data = resp.json()
            if not data.get("ok"):
                raise Exception(f"Slack API error: {data.get('error')}")
            return data.get("messages", [])

    async def get_user_name(self, user_id: str) -> str:
        """Resolve a Slack user ID to a display name."""
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{self.BASE_URL}/users.info",
                headers=self.headers,
                params={"user": user_id},
            )
            data = resp.json()
            if not data.get("ok"):
                return user_id
            user = data["user"]
            return user.get("real_name") or user.get("name", user_id)

    async def format_conversation(self, channel_id: str, limit: int = 100) -> str:
        """Fetch and format a channel conversation as readable text."""
        messages = await self.fetch_channel_history(channel_id, limit)
        lines = []
        for msg in reversed(messages):
            user = await self.get_user_name(msg.get("user", "unknown"))
            text = msg.get("text", "")
            lines.append(f"{user}: {text}")
        return "\n".join(lines)
