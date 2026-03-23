from __future__ import annotations

import json
import anthropic
from .models import Roadmap
from ..research.models import FeasibilityReport
from ..intake.models import ProjectBrief
from ...utils.config import Config
from ...utils.json_extract import extract_json
from ...utils.normalize import normalize_roadmap
from ...utils.schemas import ROADMAP_SCHEMA, schema_instruction

ROADMAP_SYSTEM_PROMPT = """You are a senior product manager for Kisasa.io, a software consulting firm.

Given a project brief and feasibility report, produce a phased roadmap with:
- project_title: The project name
- client: Client name
- total_duration: Overall estimated timeline
- milestones: Phased milestones, each containing:
  - name: Milestone name (e.g., "Phase 1: Foundation")
  - target_date: Target completion date relative to project start
  - stories: User stories with:
    - title: Story title
    - description: What needs to be done
    - acceptance_criteria: List of testable criteria
    - effort_estimate: "small", "medium", "large", or "xlarge"
    - priority_score: RICE score (Reach x Impact x Confidence / Effort) normalized 0-100
    - labels: Relevant tags
  - success_criteria: What must be true for this milestone to be complete
- dependencies: Cross-milestone dependencies
- assumptions: Key assumptions the plan relies on
- out_of_scope: What is explicitly excluded

Use the RICE framework for prioritization. Be specific with acceptance criteria — they should be testable.
Always respond with valid JSON matching the Roadmap schema."""


def process_roadmap(brief: ProjectBrief, report: FeasibilityReport) -> Roadmap:
    """Generate a phased roadmap from a project brief and feasibility report."""
    client = anthropic.Anthropic(api_key=Config.ANTHROPIC_API_KEY)

    context = json.dumps(
        {"brief": brief.model_dump(), "feasibility_report": report.model_dump()},
        indent=2,
    )

    message = client.messages.create(
        model=Config.MODEL,
        max_tokens=16384,
        system=ROADMAP_SYSTEM_PROMPT + schema_instruction(ROADMAP_SCHEMA),
        messages=[
            {
                "role": "user",
                "content": f"Generate a phased roadmap for the following project:\n\n{context}",
            }
        ],
    )

    response_text = message.content[0].text
    roadmap_data = extract_json(response_text)
    roadmap_data = normalize_roadmap(roadmap_data)
    return Roadmap(**roadmap_data)
