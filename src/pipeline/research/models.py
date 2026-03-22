from __future__ import annotations

from pydantic import BaseModel


class CompetitorInfo(BaseModel):
    name: str
    description: str
    strengths: list[str]
    weaknesses: list[str]
    relevance: str


class RiskItem(BaseModel):
    category: str  # technical, market, resource, timeline, regulatory
    description: str
    severity: str  # low, medium, high, critical
    mitigation: str


class FeasibilityReport(BaseModel):
    project_title: str
    market_overview: str
    competitors: list[CompetitorInfo]
    technical_feasibility: str
    recommended_tech_stack: list[str]
    risks: list[RiskItem]
    go_no_go_recommendation: str  # go, conditional_go, no_go
    conditions: list[str]  # conditions for conditional_go
    estimated_complexity: str  # low, medium, high
    next_steps: list[str]
