from __future__ import annotations

import json
import anthropic
from .models import TestCase, BugTicket, UATFeedback, ValidationReport, TestResult, TestStatus
from ..roadmap.models import Milestone
from ...utils.config import Config
from ...utils.json_extract import extract_json

TEST_GEN_PROMPT = """You are a QA engineer for Kisasa.io.

Given a milestone with stories and acceptance criteria, generate test cases.
Each test case should have:
- id: Unique identifier (e.g., "TC-001")
- title: Short descriptive title
- description: What this test validates
- steps: Ordered list of steps to execute
- expected_result: What should happen
- story_reference: Which story this validates

Generate thorough but practical test cases. Cover happy paths, edge cases, and error scenarios.
Respond with a JSON array of test cases."""

UAT_TRIAGE_PROMPT = """You are a product manager for Kisasa.io triaging client UAT feedback.

Analyze the raw feedback and produce structured output:
- source: Who gave the feedback
- sentiment: "positive", "neutral", or "negative"
- summary: One-line summary of the feedback
- action_items: List of specific actions to take
- linked_stories: Which stories this feedback relates to (best guess from context)

Respond with valid JSON."""

BUG_TRIAGE_PROMPT = """You are a QA engineer for Kisasa.io.

Analyze this issue report and produce a structured bug ticket:
- title: Concise bug title
- description: Detailed description
- severity: "critical", "high", "medium", or "low"
- steps_to_reproduce: Ordered list of steps
- expected_behavior: What should happen
- actual_behavior: What actually happens
- story_reference: Which story this relates to (best guess)

Respond with valid JSON."""


def generate_test_cases(milestone: Milestone) -> list[TestCase]:
    """Generate test cases from a milestone's stories and acceptance criteria."""
    client = anthropic.Anthropic(api_key=Config.ANTHROPIC_API_KEY)

    milestone_text = json.dumps(milestone.model_dump(), indent=2)

    message = client.messages.create(
        model=Config.MODEL,
        max_tokens=8192,
        system=TEST_GEN_PROMPT,
        messages=[
            {
                "role": "user",
                "content": f"Generate test cases for this milestone:\n\n{milestone_text}",
            }
        ],
    )

    test_data = extract_json(message.content[0].text)
    return [TestCase(**tc) for tc in test_data]


def triage_uat_feedback(raw_feedback: str, story_titles: list[str]) -> UATFeedback:
    """Analyze and structure raw UAT feedback from a client."""
    client = anthropic.Anthropic(api_key=Config.ANTHROPIC_API_KEY)

    message = client.messages.create(
        model=Config.MODEL,
        max_tokens=2048,
        system=UAT_TRIAGE_PROMPT,
        messages=[
            {
                "role": "user",
                "content": (
                    f"Available stories: {json.dumps(story_titles)}\n\n"
                    f"Raw feedback:\n{raw_feedback}"
                ),
            }
        ],
    )

    feedback_data = extract_json(message.content[0].text)
    return UATFeedback(**feedback_data)


def triage_bug_report(raw_report: str, story_titles: list[str]) -> BugTicket:
    """Analyze a raw bug report and produce a structured bug ticket."""
    client = anthropic.Anthropic(api_key=Config.ANTHROPIC_API_KEY)

    message = client.messages.create(
        model=Config.MODEL,
        max_tokens=2048,
        system=BUG_TRIAGE_PROMPT,
        messages=[
            {
                "role": "user",
                "content": (
                    f"Available stories: {json.dumps(story_titles)}\n\n"
                    f"Raw bug report:\n{raw_report}"
                ),
            }
        ],
    )

    bug_data = extract_json(message.content[0].text)
    return BugTicket(**bug_data)


def generate_validation_report(
    milestone: Milestone,
    test_results: list[TestResult],
    bugs: list[BugTicket],
    uat_feedback: list[UATFeedback],
) -> ValidationReport:
    """Compile a full validation report for a milestone."""
    test_cases = generate_test_cases(milestone)

    pass_count = sum(1 for r in test_results if r.status == TestStatus.PASS)
    total = len(test_results) if test_results else 1
    pass_rate = pass_count / total

    critical_bugs = [b for b in bugs if b.severity in ("critical", "high")]
    negative_feedback = [f for f in uat_feedback if f.sentiment == "negative"]

    blockers = [f"Critical bug: {b.title}" for b in critical_bugs]
    blockers += [f"Negative UAT: {f.summary}" for f in negative_feedback]

    return ValidationReport(
        milestone_name=milestone.name,
        test_cases=test_cases,
        test_results=test_results,
        bugs_found=bugs,
        uat_feedback=uat_feedback,
        pass_rate=pass_rate,
        ready_for_launch=len(blockers) == 0 and pass_rate >= 0.9,
        blockers=blockers,
    )
