from __future__ import annotations

import base64
import httpx
from ..utils.config import Config


class GmailConnector:
    """Fetches email threads from Gmail API."""

    BASE_URL = "https://gmail.googleapis.com/gmail/v1"

    def __init__(self, access_token: str | None = None):
        self.token = access_token or Config.GMAIL_ACCESS_TOKEN
        self.headers = {"Authorization": f"Bearer {self.token}"}

    async def search_emails(self, query: str, max_results: int = 10) -> list[dict]:
        """Search emails by query (e.g., 'from:client@acme.com subject:project')."""
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{self.BASE_URL}/users/me/messages",
                headers=self.headers,
                params={"q": query, "maxResults": max_results},
            )
            data = resp.json()
            return data.get("messages", [])

    async def get_message(self, message_id: str) -> dict:
        """Fetch a single email message with full content."""
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{self.BASE_URL}/users/me/messages/{message_id}",
                headers=self.headers,
                params={"format": "full"},
            )
            return resp.json()

    async def get_thread(self, thread_id: str) -> list[dict]:
        """Fetch all messages in an email thread."""
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{self.BASE_URL}/users/me/threads/{thread_id}",
                headers=self.headers,
            )
            data = resp.json()
            return data.get("messages", [])

    def extract_body(self, message: dict) -> str:
        """Extract plain text body from a Gmail message."""
        payload = message.get("payload", {})
        parts = payload.get("parts", [])

        # Simple message (no parts)
        if not parts and payload.get("body", {}).get("data"):
            return base64.urlsafe_b64decode(payload["body"]["data"]).decode("utf-8")

        # Multipart message — find text/plain
        for part in parts:
            if part.get("mimeType") == "text/plain" and part.get("body", {}).get(
                "data"
            ):
                return base64.urlsafe_b64decode(part["body"]["data"]).decode("utf-8")

        return ""

    def extract_headers(self, message: dict) -> dict:
        """Extract key headers (from, to, subject, date) from a message."""
        headers = message.get("payload", {}).get("headers", [])
        result = {}
        for h in headers:
            name = h["name"].lower()
            if name in ("from", "to", "subject", "date"):
                result[name] = h["value"]
        return result

    async def format_thread(self, thread_id: str) -> str:
        """Fetch and format an email thread as readable text."""
        messages = await self.get_thread(thread_id)
        lines = []
        for msg in messages:
            headers = self.extract_headers(msg)
            body = self.extract_body(msg)
            lines.append(
                f"From: {headers.get('from', 'unknown')}\n"
                f"Date: {headers.get('date', '')}\n"
                f"Subject: {headers.get('subject', '')}\n"
                f"{body}\n---"
            )
        return "\n".join(lines)
