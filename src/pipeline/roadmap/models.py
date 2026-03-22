from __future__ import annotations

from pydantic import BaseModel


class Story(BaseModel):
    title: str
    description: str
    acceptance_criteria: list[str]
    effort_estimate: str  # small, medium, large, xlarge
    priority_score: float  # RICE score
    labels: list[str]


class Milestone(BaseModel):
    name: str
    target_date: str
    stories: list[Story]
    success_criteria: list[str]


class Roadmap(BaseModel):
    project_title: str
    client: str
    total_duration: str
    milestones: list[Milestone]
    dependencies: list[str]
    assumptions: list[str]
    out_of_scope: list[str]
