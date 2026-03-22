from __future__ import annotations

from pydantic import BaseModel
from enum import Enum


class Division(str, Enum):
    VENTURES = "ventures"
    LABS = "labs"
    STRATEGY = "strategy"


class ProjectBrief(BaseModel):
    title: str
    client: str
    division: Division
    problem_statement: str
    goals: list[str]
    constraints: list[str]
    scope: str
    stakeholders: list[str]
    suggested_timeline: str
    risk_flags: list[str]
    confidence_score: float  # 0-1, how confident the AI is in the extraction
