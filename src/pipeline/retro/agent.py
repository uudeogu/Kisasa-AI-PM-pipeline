import json
import anthropic
from .models import RetroReport
from ..roadmap.models import Roadmap
from ..intake.models import ProjectBrief
from ...utils.config import Config

RETRO_PROMPT = """You are a delivery analyst for Kisasa.io conducting a project retrospective.

Given project data (brief, roadmap, actuals), produce a retrospective report:
- project_title, client: From the brief
- duration_planned: Original timeline
- duration_actual: How long it actually took
- estimate_accuracy: For each story, compare estimated vs actual effort
  - accuracy_pct: 100 = perfect match, >100 = took longer, <100 = finished early
- average_accuracy_pct: Average across all stories
- what_went_well: List of things that worked
- what_could_improve: List of areas for improvement
- insights: Actionable insights with category (process/technical/communication/estimation), observation, recommendation, and priority
- updated_estimation_rules: Concrete rules to improve future estimates (e.g., "Add 30% buffer for projects involving team upskilling")

Focus on actionable learnings that make the next project better. Kisasa improves by shipping and learning.
Respond with valid JSON matching the RetroReport schema."""


def generate_retro(
    brief: ProjectBrief,
    roadmap: Roadmap,
    actual_duration: str,
    story_actuals: list[dict],  # [{"title": str, "actual_effort": str}]
) -> RetroReport:
    """Generate a retrospective report comparing planned vs actual outcomes."""
    client = anthropic.Anthropic(api_key=Config.ANTHROPIC_API_KEY)

    context = json.dumps(
        {
            "brief": brief.model_dump(),
            "roadmap": roadmap.model_dump(),
            "actual_duration": actual_duration,
            "story_actuals": story_actuals,
        },
        indent=2,
    )

    message = client.messages.create(
        model=Config.MODEL,
        max_tokens=8192,
        system=RETRO_PROMPT,
        messages=[
            {
                "role": "user",
                "content": f"Generate a retrospective report:\n\n{context}",
            }
        ],
    )

    retro_data = json.loads(message.content[0].text)
    return RetroReport(**retro_data)
