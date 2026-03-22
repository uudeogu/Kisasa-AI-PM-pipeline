from __future__ import annotations

import httpx
from ..utils.config import Config


class ZoomConnector:
    """Fetches meeting recordings and transcripts from Zoom API."""

    BASE_URL = "https://api.zoom.us/v2"

    def __init__(self, access_token: str | None = None):
        self.token = access_token or Config.ZOOM_ACCESS_TOKEN
        self.headers = {"Authorization": f"Bearer {self.token}"}

    async def list_recordings(
        self, user_id: str = "me", from_date: str = "", to_date: str = ""
    ) -> list[dict]:
        """List cloud recordings for a user within a date range."""
        params = {}
        if from_date:
            params["from"] = from_date
        if to_date:
            params["to"] = to_date

        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{self.BASE_URL}/users/{user_id}/recordings",
                headers=self.headers,
                params=params,
            )
            data = resp.json()
            return data.get("meetings", [])

    async def get_transcript(self, meeting_id: str) -> str | None:
        """Fetch the transcript for a specific meeting recording."""
        async with httpx.AsyncClient() as client:
            # Get recording details to find transcript file
            resp = await client.get(
                f"{self.BASE_URL}/meetings/{meeting_id}/recordings",
                headers=self.headers,
            )
            data = resp.json()

            # Find the transcript file
            for file in data.get("recording_files", []):
                if file.get("file_type") == "TRANSCRIPT":
                    download_url = file.get("download_url")
                    if download_url:
                        transcript_resp = await client.get(
                            download_url,
                            headers=self.headers,
                        )
                        return transcript_resp.text

            return None

    async def get_meeting_details(self, meeting_id: str) -> dict:
        """Fetch metadata for a meeting (topic, date, participants)."""
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{self.BASE_URL}/meetings/{meeting_id}",
                headers=self.headers,
            )
            return resp.json()

    async def format_meeting(self, meeting_id: str) -> str:
        """Fetch and format meeting details + transcript as readable text."""
        details = await self.get_meeting_details(meeting_id)
        transcript = await self.get_transcript(meeting_id)

        header = (
            f"Meeting: {details.get('topic', 'Untitled')}\n"
            f"Date: {details.get('start_time', 'unknown')}\n"
            f"Duration: {details.get('duration', 'unknown')} minutes\n"
        )

        if transcript:
            return f"{header}\n--- Transcript ---\n{transcript}"
        else:
            return f"{header}\n[No transcript available]"
