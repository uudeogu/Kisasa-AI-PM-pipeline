import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
    LINEAR_API_KEY = os.getenv("LINEAR_API_KEY")
    GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
    DATABASE_URL = os.getenv("DATABASE_URL")
    MODEL = "claude-sonnet-4-6-20250514"
