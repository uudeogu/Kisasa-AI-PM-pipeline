import json
import anthropic
from .models import HandoffPackage
from ..roadmap.models import Roadmap
from ..qa.models import ValidationReport
from ..intake.models import ProjectBrief
from ...utils.config import Config

HANDOFF_PROMPT = """You are a delivery lead for Kisasa.io preparing a client handoff package.

Given a project brief, roadmap, and validation report, generate:
- project_title: Project name
- client: Client name
- documentation: List of documents, each with title and sections (heading + content)
  - Include: Architecture overview, API reference, deployment guide, configuration guide
- runbook: Ordered deployment/operations steps, each with:
  - order, title, command_or_action, expected_outcome, rollback
- environment_details: Dict of environment info (urls, infra details, key references)
- known_issues: List of known issues or limitations
- monitoring_checklist: What to monitor post-launch
- onboarding_guide: Markdown guide for new team members joining the project

Be thorough but practical. Kisasa hands off real systems to real teams.
Respond with valid JSON matching the HandoffPackage schema."""


def generate_handoff(
    brief: ProjectBrief,
    roadmap: Roadmap,
    validation: ValidationReport,
) -> HandoffPackage:
    """Generate a complete client handoff package."""
    client = anthropic.Anthropic(api_key=Config.ANTHROPIC_API_KEY)

    context = json.dumps(
        {
            "brief": brief.model_dump(),
            "roadmap": roadmap.model_dump(),
            "validation": {
                "pass_rate": validation.pass_rate,
                "bugs_found": len(validation.bugs_found),
                "blockers": validation.blockers,
                "ready_for_launch": validation.ready_for_launch,
            },
        },
        indent=2,
    )

    message = client.messages.create(
        model=Config.MODEL,
        max_tokens=8192,
        system=HANDOFF_PROMPT,
        messages=[
            {
                "role": "user",
                "content": f"Generate a handoff package for:\n\n{context}",
            }
        ],
    )

    handoff_data = json.loads(message.content[0].text)
    return HandoffPackage(**handoff_data)
