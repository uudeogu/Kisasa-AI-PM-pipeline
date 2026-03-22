from __future__ import annotations

import json
import anthropic
from .models import FeasibilityReport
from ..intake.models import ProjectBrief
from ...utils.config import Config

RESEARCH_SYSTEM_PROMPT = """You are a senior technical analyst for Kisasa.io, a software consulting firm.

Given a project brief, produce a feasibility report that includes:
- market_overview: Brief analysis of the market landscape relevant to this project
- competitors: Key competitors or existing solutions (name, description, strengths, weaknesses, relevance)
- technical_feasibility: Assessment of whether the project is technically achievable given constraints
- recommended_tech_stack: Suggested technologies and tools
- risks: List of risks with category (technical/market/resource/timeline/regulatory), severity (low/medium/high/critical), and mitigation strategies
- go_no_go_recommendation: "go", "conditional_go", or "no_go"
- conditions: If conditional_go, what must be true before proceeding
- estimated_complexity: "low", "medium", or "high"
- next_steps: Recommended actions to move forward

Be pragmatic and specific. Kisasa builds and ships real software — focus on actionable insights, not theory.
Always respond with valid JSON matching the FeasibilityReport schema."""


def process_research(brief: ProjectBrief) -> FeasibilityReport:
    """Analyze a project brief and produce a feasibility report."""
    client = anthropic.Anthropic(api_key=Config.ANTHROPIC_API_KEY)

    brief_text = json.dumps(brief.model_dump(), indent=2)

    message = client.messages.create(
        model=Config.MODEL,
        max_tokens=4096,
        system=RESEARCH_SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": f"Produce a feasibility report for the following project brief:\n\n{brief_text}",
            }
        ],
    )

    response_text = message.content[0].text
    report_data = json.loads(response_text)
    return FeasibilityReport(**report_data)


if __name__ == "__main__":
    sample_brief = ProjectBrief(
        title="Acme Corp Monolith Decomposition",
        client="Acme Corp",
        division="labs",
        problem_statement="Legacy Java monolith with 4-hour deployment cycles needs to be broken into microservices",
        goals=["Reduce deploy time to under 15 minutes", "Move to Kubernetes", "Enable independent team deployments"],
        constraints=["$500k budget", "Q3 deadline", "Team has no container experience"],
        scope="Decompose monolith into microservices, set up K8s infrastructure, upskill team",
        stakeholders=["Sarah (CTO)", "Marcus (VP Eng)"],
        suggested_timeline="6 months",
        risk_flags=["Team lacks container experience", "Aggressive timeline for monolith decomposition"],
        confidence_score=0.85,
    )

    report = process_research(sample_brief)
    print(json.dumps(report.model_dump(), indent=2))
