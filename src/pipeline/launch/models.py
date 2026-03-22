from __future__ import annotations

from pydantic import BaseModel


class RunbookStep(BaseModel):
    order: int
    title: str
    command_or_action: str
    expected_outcome: str
    rollback: str


class Documentation(BaseModel):
    title: str
    sections: list[dict]  # {"heading": str, "content": str}


class HandoffPackage(BaseModel):
    project_title: str
    client: str
    documentation: list[Documentation]
    runbook: list[RunbookStep]
    environment_details: dict  # urls, credentials references, infra
    known_issues: list[str]
    monitoring_checklist: list[str]
    onboarding_guide: str  # markdown content for new team members
