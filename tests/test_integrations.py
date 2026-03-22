"""Tests for integration connectors with mocked HTTP calls."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import httpx

from src.integrations.slack import SlackConnector
from src.integrations.gmail import GmailConnector
from src.integrations.zoom import ZoomConnector
from src.integrations.linear import LinearConnector
from src.integrations.notion import NotionConnector
from src.integrations.github import GitHubConnector


# ---------------------------------------------------------------------------
# Slack
# ---------------------------------------------------------------------------

class TestSlackConnector:
    def test_init_with_token(self):
        connector = SlackConnector(token="xoxb-test-token")
        assert connector.token == "xoxb-test-token"
        assert "Bearer xoxb-test-token" in connector.headers["Authorization"]

    @pytest.mark.asyncio
    async def test_fetch_channel_history(self):
        connector = SlackConnector(token="xoxb-test")
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "ok": True,
            "messages": [
                {"user": "U123", "text": "Hello"},
                {"user": "U456", "text": "Hi there"},
            ],
        }

        with patch("httpx.AsyncClient.get", new_callable=AsyncMock, return_value=mock_response):
            messages = await connector.fetch_channel_history("C123")
            assert len(messages) == 2
            assert messages[0]["text"] == "Hello"

    @pytest.mark.asyncio
    async def test_fetch_channel_history_error(self):
        connector = SlackConnector(token="xoxb-test")
        mock_response = MagicMock()
        mock_response.json.return_value = {"ok": False, "error": "channel_not_found"}

        with patch("httpx.AsyncClient.get", new_callable=AsyncMock, return_value=mock_response):
            with pytest.raises(Exception, match="channel_not_found"):
                await connector.fetch_channel_history("C999")

    @pytest.mark.asyncio
    async def test_get_user_name(self):
        connector = SlackConnector(token="xoxb-test")
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "ok": True,
            "user": {"real_name": "Jane Doe", "name": "jane"},
        }

        with patch("httpx.AsyncClient.get", new_callable=AsyncMock, return_value=mock_response):
            name = await connector.get_user_name("U123")
            assert name == "Jane Doe"

    @pytest.mark.asyncio
    async def test_get_user_name_fallback(self):
        connector = SlackConnector(token="xoxb-test")
        mock_response = MagicMock()
        mock_response.json.return_value = {"ok": False, "error": "user_not_found"}

        with patch("httpx.AsyncClient.get", new_callable=AsyncMock, return_value=mock_response):
            name = await connector.get_user_name("U999")
            assert name == "U999"


# ---------------------------------------------------------------------------
# Gmail
# ---------------------------------------------------------------------------

class TestGmailConnector:
    def test_init_with_token(self):
        connector = GmailConnector(access_token="test-token")
        assert connector.token == "test-token"

    def test_extract_headers(self):
        connector = GmailConnector(access_token="test")
        message = {
            "payload": {
                "headers": [
                    {"name": "From", "value": "alice@acme.com"},
                    {"name": "To", "value": "team@kisasa.io"},
                    {"name": "Subject", "value": "Project kickoff"},
                    {"name": "Date", "value": "Mon, 1 Jan 2026"},
                ]
            }
        }
        headers = connector.extract_headers(message)
        assert headers["from"] == "alice@acme.com"
        assert headers["subject"] == "Project kickoff"

    def test_extract_body_simple(self):
        import base64
        connector = GmailConnector(access_token="test")
        body_text = "Hello, let's discuss the project."
        encoded = base64.urlsafe_b64encode(body_text.encode()).decode()
        message = {"payload": {"body": {"data": encoded}, "parts": []}}
        result = connector.extract_body(message)
        assert result == body_text

    def test_extract_body_multipart(self):
        import base64
        connector = GmailConnector(access_token="test")
        body_text = "Plain text body"
        encoded = base64.urlsafe_b64encode(body_text.encode()).decode()
        message = {
            "payload": {
                "body": {},
                "parts": [
                    {"mimeType": "text/html", "body": {"data": "html"}},
                    {"mimeType": "text/plain", "body": {"data": encoded}},
                ],
            }
        }
        result = connector.extract_body(message)
        assert result == body_text

    def test_extract_body_empty(self):
        connector = GmailConnector(access_token="test")
        message = {"payload": {"body": {}, "parts": []}}
        result = connector.extract_body(message)
        assert result == ""

    @pytest.mark.asyncio
    async def test_search_emails(self):
        connector = GmailConnector(access_token="test")
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "messages": [{"id": "msg1"}, {"id": "msg2"}]
        }

        with patch("httpx.AsyncClient.get", new_callable=AsyncMock, return_value=mock_response):
            results = await connector.search_emails("from:client@acme.com")
            assert len(results) == 2


# ---------------------------------------------------------------------------
# Zoom
# ---------------------------------------------------------------------------

class TestZoomConnector:
    def test_init_with_token(self):
        connector = ZoomConnector(access_token="zoom-test")
        assert connector.token == "zoom-test"

    @pytest.mark.asyncio
    async def test_get_meeting_details(self):
        connector = ZoomConnector(access_token="zoom-test")
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "topic": "Project Kickoff",
            "start_time": "2026-01-15T10:00:00Z",
            "duration": 60,
        }

        with patch("httpx.AsyncClient.get", new_callable=AsyncMock, return_value=mock_response):
            details = await connector.get_meeting_details("12345")
            assert details["topic"] == "Project Kickoff"
            assert details["duration"] == 60

    @pytest.mark.asyncio
    async def test_get_transcript_found(self):
        connector = ZoomConnector(access_token="zoom-test")
        recordings_response = MagicMock()
        recordings_response.json.return_value = {
            "recording_files": [
                {"file_type": "MP4", "download_url": "https://zoom.us/mp4"},
                {"file_type": "TRANSCRIPT", "download_url": "https://zoom.us/transcript"},
            ]
        }
        transcript_response = MagicMock()
        transcript_response.text = "Speaker 1: Let's discuss the project.\nSpeaker 2: Agreed."

        with patch("httpx.AsyncClient.get", new_callable=AsyncMock, side_effect=[recordings_response, transcript_response]):
            transcript = await connector.get_transcript("12345")
            assert "Let's discuss the project" in transcript

    @pytest.mark.asyncio
    async def test_get_transcript_not_found(self):
        connector = ZoomConnector(access_token="zoom-test")
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "recording_files": [{"file_type": "MP4", "download_url": "https://zoom.us/mp4"}]
        }

        with patch("httpx.AsyncClient.get", new_callable=AsyncMock, return_value=mock_response):
            transcript = await connector.get_transcript("12345")
            assert transcript is None


# ---------------------------------------------------------------------------
# Linear
# ---------------------------------------------------------------------------

class TestLinearConnector:
    def test_init_with_key(self):
        connector = LinearConnector(api_key="lin_test_key")
        assert connector.api_key == "lin_test_key"

    @pytest.mark.asyncio
    async def test_create_issue(self):
        connector = LinearConnector(api_key="lin_test")
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "data": {
                "issueCreate": {
                    "success": True,
                    "issue": {
                        "id": "issue-1",
                        "identifier": "KIS-42",
                        "title": "Set up K8s",
                        "url": "https://linear.app/kisasa/issue/KIS-42",
                    },
                }
            }
        }

        with patch("httpx.AsyncClient.post", new_callable=AsyncMock, return_value=mock_response):
            issue = await connector.create_issue("team-1", "Set up K8s", "Provision cluster")
            assert issue["identifier"] == "KIS-42"

    @pytest.mark.asyncio
    async def test_query_error(self):
        connector = LinearConnector(api_key="lin_test")
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "errors": [{"message": "Authentication failed"}]
        }

        with patch("httpx.AsyncClient.post", new_callable=AsyncMock, return_value=mock_response):
            with pytest.raises(Exception, match="Linear API error"):
                await connector.list_teams()


# ---------------------------------------------------------------------------
# Notion
# ---------------------------------------------------------------------------

class TestNotionConnector:
    def test_init_with_key(self):
        connector = NotionConnector(api_key="secret_test")
        assert connector.api_key == "secret_test"
        assert connector.headers["Notion-Version"] == "2022-06-28"

    def test_text_block(self):
        block = NotionConnector.text_block("Hello world")
        assert block["type"] == "paragraph"
        assert block["paragraph"]["rich_text"][0]["text"]["content"] == "Hello world"

    def test_heading_block_default(self):
        block = NotionConnector.heading_block("My Heading")
        assert block["type"] == "heading_2"

    def test_heading_block_level_1(self):
        block = NotionConnector.heading_block("Title", level=1)
        assert block["type"] == "heading_1"

    def test_heading_block_level_3(self):
        block = NotionConnector.heading_block("Subsection", level=3)
        assert block["type"] == "heading_3"

    @pytest.mark.asyncio
    async def test_create_page(self):
        connector = NotionConnector(api_key="secret_test")
        mock_response = MagicMock()
        mock_response.json.return_value = {"id": "page-123", "url": "https://notion.so/page-123"}

        with patch("httpx.AsyncClient.post", new_callable=AsyncMock, return_value=mock_response):
            page = await connector.create_page(
                "db-1", "Test Page", [NotionConnector.text_block("Content")]
            )
            assert page["id"] == "page-123"


# ---------------------------------------------------------------------------
# GitHub
# ---------------------------------------------------------------------------

class TestGitHubConnector:
    def test_init_with_token(self):
        connector = GitHubConnector(token="ghp_test")
        assert connector.token == "ghp_test"

    @pytest.mark.asyncio
    async def test_list_pull_requests(self):
        connector = GitHubConnector(token="ghp_test")
        mock_response = MagicMock()
        mock_response.json.return_value = [
            {"number": 1, "title": "Add auth", "state": "open"},
            {"number": 2, "title": "Fix bug", "state": "open"},
        ]

        with patch("httpx.AsyncClient.get", new_callable=AsyncMock, return_value=mock_response):
            prs = await connector.list_pull_requests("kisasa", "api")
            assert len(prs) == 2
            assert prs[0]["number"] == 1

    @pytest.mark.asyncio
    async def test_get_pr_diff(self):
        connector = GitHubConnector(token="ghp_test")
        mock_response = MagicMock()
        mock_response.text = "diff --git a/file.py b/file.py\n+new line"

        with patch("httpx.AsyncClient.get", new_callable=AsyncMock, return_value=mock_response):
            diff = await connector.get_pr_diff("kisasa", "api", 1)
            assert "diff --git" in diff

    @pytest.mark.asyncio
    async def test_create_issue(self):
        connector = GitHubConnector(token="ghp_test")
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "number": 10,
            "title": "Bug report",
            "html_url": "https://github.com/kisasa/api/issues/10",
        }

        with patch("httpx.AsyncClient.post", new_callable=AsyncMock, return_value=mock_response):
            issue = await connector.create_issue("kisasa", "api", "Bug report", "Details here")
            assert issue["number"] == 10
