from __future__ import annotations

import json
from .intake.agent import process_intake, ingest_from_slack, ingest_from_email, ingest_from_zoom
from .intake.models import ProjectBrief
from .research.agent import process_research
from .roadmap.agent import process_roadmap
from .roadmap.models import Roadmap
from .build.agent import generate_build_report
from .qa.agent import generate_test_cases, generate_validation_report
from .qa.models import TestResult, TestStatus
from .launch.agent import generate_handoff
from .retro.agent import generate_retro
from ..integrations.linear import LinearConnector
from ..integrations.notion import NotionConnector
from ..observability.tracing import trace_stage


# ---------------------------------------------------------------------------
# Stage 1-3: Intake → Research → Roadmap
# ---------------------------------------------------------------------------

@trace_stage("planning_pipeline")
async def run_planning_pipeline(
    raw_input: str | None = None,
    slack_channel_id: str | None = None,
    email_thread_id: str | None = None,
    zoom_meeting_id: str | None = None,
) -> dict:
    """Run Stages 1-3: Intake → Research → Roadmap.

    Provide one of: raw_input, slack_channel_id, email_thread_id, or zoom_meeting_id.
    """

    # Stage 1: Intake
    if slack_channel_id:
        raw_input = await ingest_from_slack(slack_channel_id)
    elif email_thread_id:
        raw_input = await ingest_from_email(email_thread_id)
    elif zoom_meeting_id:
        raw_input = await ingest_from_zoom(zoom_meeting_id)
    elif not raw_input:
        raise ValueError("Provide raw_input, slack_channel_id, email_thread_id, or zoom_meeting_id")

    brief = process_intake(raw_input)
    print(f"[Stage 1] Intake complete: {brief.title} → {brief.division.value}")

    # Stage 2: Research & Feasibility
    report = process_research(brief)
    print(f"[Stage 2] Research complete: {report.go_no_go_recommendation}")

    if report.go_no_go_recommendation == "no_go":
        print("[Pipeline] No-go recommendation. Stopping pipeline.")
        return {
            "stage": "research",
            "status": "no_go",
            "brief": brief.model_dump(),
            "report": report.model_dump(),
        }

    # Stage 3: Roadmap & Planning
    roadmap = process_roadmap(brief, report)
    total_stories = sum(len(m.stories) for m in roadmap.milestones)
    print(f"[Stage 3] Roadmap complete: {len(roadmap.milestones)} milestones, {total_stories} stories")

    return {
        "stage": "roadmap",
        "status": "ready_to_build",
        "brief": brief.model_dump(),
        "report": report.model_dump(),
        "roadmap": roadmap.model_dump(),
    }


# ---------------------------------------------------------------------------
# Stage 4: Build & Ship — monitor active development
# ---------------------------------------------------------------------------

@trace_stage("build_monitor")
async def run_build_monitor(
    roadmap: Roadmap,
    milestone_index: int,
    owner: str,
    repo: str,
    completed_story_count: int,
) -> dict:
    """Run Stage 4: Monitor build progress for a milestone."""
    milestone = roadmap.milestones[milestone_index]
    report = await generate_build_report(milestone, owner, repo, completed_story_count)
    print(f"[Stage 4] Build report: {report.overall_health} | {report.stories_completed}/{report.stories_total} stories")
    return {"stage": "build", "report": report.model_dump()}


# ---------------------------------------------------------------------------
# Stage 5: QA & Validation
# ---------------------------------------------------------------------------

@trace_stage("qa")
def run_qa(
    roadmap: Roadmap,
    milestone_index: int,
    test_results: list[dict] | None = None,
    bug_reports: list[dict] | None = None,
    uat_feedback_items: list[dict] | None = None,
) -> dict:
    """Run Stage 5: Generate test cases and compile validation report."""
    from .qa.models import BugTicket, UATFeedback

    milestone = roadmap.milestones[milestone_index]

    # Parse inputs
    results = [TestResult(**r) for r in test_results] if test_results else []
    bugs = [BugTicket(**b) for b in bug_reports] if bug_reports else []
    feedback = [UATFeedback(**f) for f in uat_feedback_items] if uat_feedback_items else []

    validation = generate_validation_report(milestone, results, bugs, feedback)
    print(f"[Stage 5] QA complete: {validation.pass_rate:.0%} pass rate | Ready: {validation.ready_for_launch}")
    return {"stage": "qa", "validation": validation.model_dump()}


# ---------------------------------------------------------------------------
# Stage 6: Launch & Handoff
# ---------------------------------------------------------------------------

@trace_stage("launch")
def run_launch(pipeline_result: dict) -> dict:
    """Run Stage 6: Generate handoff package."""
    from .qa.models import ValidationReport

    brief = ProjectBrief(**pipeline_result["brief"])
    roadmap = Roadmap(**pipeline_result["roadmap"])
    validation = ValidationReport(**pipeline_result["validation"])

    if not validation.ready_for_launch:
        print(f"[Stage 6] WARNING: Launching with {len(validation.blockers)} blocker(s)")

    handoff = generate_handoff(brief, roadmap, validation)
    print(f"[Stage 6] Handoff package generated: {len(handoff.documentation)} docs, {len(handoff.runbook)} runbook steps")
    return {"stage": "launch", "handoff": handoff.model_dump()}


# ---------------------------------------------------------------------------
# Stage 7: Retrospective & Learning
# ---------------------------------------------------------------------------

@trace_stage("retro")
def run_retro(
    pipeline_result: dict,
    actual_duration: str,
    story_actuals: list[dict],
) -> dict:
    """Run Stage 7: Generate retrospective report."""
    brief = ProjectBrief(**pipeline_result["brief"])
    roadmap = Roadmap(**pipeline_result["roadmap"])

    retro = generate_retro(brief, roadmap, actual_duration, story_actuals)
    print(f"[Stage 7] Retro complete: {retro.average_accuracy_pct:.0f}% estimation accuracy")
    print(f"[Stage 7] {len(retro.insights)} insights, {len(retro.updated_estimation_rules)} new estimation rules")
    return {"stage": "retro", "retro": retro.model_dump()}


# ---------------------------------------------------------------------------
# Integration helpers
# ---------------------------------------------------------------------------

async def sync_to_linear(roadmap_result: dict, team_id: str) -> list[dict]:
    """Push roadmap stories to Linear as issues."""
    linear = LinearConnector()
    roadmap = roadmap_result["roadmap"]
    created_issues = []

    project = await linear.create_project(
        team_ids=[team_id],
        name=roadmap["project_title"],
        description=f"Client: {roadmap['client']}\nDuration: {roadmap['total_duration']}",
    )
    print(f"[Linear] Created project: {project.get('name')}")

    for milestone in roadmap["milestones"]:
        for story in milestone["stories"]:
            priority_map = {"small": 4, "medium": 3, "large": 2, "xlarge": 1}
            priority = priority_map.get(story["effort_estimate"], 3)

            description = (
                f"{story['description']}\n\n"
                f"**Milestone:** {milestone['name']}\n"
                f"**Acceptance Criteria:**\n"
                + "\n".join(f"- [ ] {ac}" for ac in story["acceptance_criteria"])
            )

            issue = await linear.create_issue(
                team_id=team_id,
                title=story["title"],
                description=description,
                priority=priority,
            )
            created_issues.append(issue)
            print(f"[Linear] Created: {issue.get('identifier')} — {issue.get('title')}")

    return created_issues


async def sync_to_notion(roadmap_result: dict, database_id: str) -> dict:
    """Push the project brief and roadmap to Notion as a page."""
    notion = NotionConnector()
    brief = roadmap_result["brief"]
    roadmap = roadmap_result["roadmap"]

    blocks = [
        NotionConnector.heading_block("Project Brief", level=2),
        NotionConnector.text_block(f"Client: {brief['client']}"),
        NotionConnector.text_block(f"Division: {brief['division']}"),
        NotionConnector.text_block(f"Problem: {brief['problem_statement']}"),
        NotionConnector.heading_block("Roadmap", level=2),
        NotionConnector.text_block(f"Duration: {roadmap['total_duration']}"),
    ]

    for milestone in roadmap["milestones"]:
        blocks.append(NotionConnector.heading_block(milestone["name"], level=3))
        blocks.append(
            NotionConnector.text_block(
                f"Target: {milestone['target_date']} | "
                f"{len(milestone['stories'])} stories"
            )
        )

    page = await notion.create_page(
        parent_id=database_id,
        title=roadmap["project_title"],
        content_blocks=blocks,
    )
    print(f"[Notion] Created page: {page.get('id')}")
    return page
