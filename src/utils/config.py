from __future__ import annotations

import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    # AI
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
    MODEL = "claude-sonnet-4-5-20250929"

    # Intake connectors
    SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
    GMAIL_ACCESS_TOKEN = os.getenv("GMAIL_ACCESS_TOKEN")
    ZOOM_ACCESS_TOKEN = os.getenv("ZOOM_ACCESS_TOKEN")

    # PM tools
    LINEAR_API_KEY = os.getenv("LINEAR_API_KEY")
    NOTION_API_KEY = os.getenv("NOTION_API_KEY")

    # Code
    GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

    # Data
    DATABASE_URL = os.getenv("DATABASE_URL")
