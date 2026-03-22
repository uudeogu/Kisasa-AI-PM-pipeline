import json
import anthropic
from ..intake.models import ProjectBrief
from ...utils.config import Config

INTAKE_SYSTEM_PROMPT = """You are an AI product manager for Kisasa.io, a software consulting firm that builds and ships alongside client teams.

Your job is to extract a structured project brief from raw client input (emails, meeting transcripts, Slack messages, or notes).

Kisasa has three divisions — route the project to the right one:
- **Ventures**: New product ideas, investment opportunities, building from scratch
- **Labs**: System modernization, architecture redesign, infrastructure upgrades
- **Strategy**: Developer ecosystem building, adoption planning, platform strategy

Extract the following into a structured JSON response:
- title: A concise project title
- client: Client name or organization
- division: Which Kisasa division should own this (ventures, labs, or strategy)
- problem_statement: What problem the client is trying to solve
- goals: List of specific goals
- constraints: Budget, timeline, technical, or regulatory constraints
- scope: What's in scope and what's explicitly out of scope
- stakeholders: Key people involved
- suggested_timeline: Rough timeline based on scope
- risk_flags: Any risks or concerns you've identified
- confidence_score: 0-1 rating of how confident you are in this extraction (lower if input is vague)

If information is missing, note it in risk_flags and set a lower confidence_score.
Always respond with valid JSON matching the ProjectBrief schema."""


def create_intake_agent():
    return anthropic.Anthropic(api_key=Config.ANTHROPIC_API_KEY)


def process_intake(raw_input: str) -> ProjectBrief:
    """Process raw client input and generate a structured project brief."""
    client = create_intake_agent()

    message = client.messages.create(
        model=Config.MODEL,
        max_tokens=2048,
        system=INTAKE_SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": f"Extract a project brief from the following client input:\n\n{raw_input}",
            }
        ],
    )

    response_text = message.content[0].text
    brief_data = json.loads(response_text)
    return ProjectBrief(**brief_data)


if __name__ == "__main__":
    sample_input = """
    Hey team, we just had a call with Acme Corp. They're running a legacy Java monolith
    that's been around since 2015 and it's getting painful to deploy — takes 4 hours
    for a full release. They want to break it into microservices, probably on Kubernetes.
    Budget is around $500k, and they need it done by Q3. Their CTO Sarah and VP of Eng
    Marcus are the main contacts. One concern — they have zero container experience on
    their team, so we'll need to upskill them too.
    """

    brief = process_intake(sample_input)
    print(json.dumps(brief.model_dump(), indent=2))
