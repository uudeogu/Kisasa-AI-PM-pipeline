import json
from .intake.agent import process_intake, ingest_from_slack, ingest_from_email, ingest_from_zoom
from .research.agent import process_research
from .roadmap.agent import process_roadmap
from ..integrations.linear import LinearConnector
from ..integrations.notion import NotionConnector


async def run_pipeline(
    raw_input: str | None = None,
    slack_channel_id: str | None = None,
    email_thread_id: str | None = None,
    zoom_meeting_id: str | None = None,
) -> dict:
    """Run the full pipeline from intake through roadmap generation.

    Provide one of: raw_input, slack_channel_id, email_thread_id, or zoom_meeting_id.
    """

    # Stage 1: Intake — gather raw input from the right source
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


async def sync_to_linear(roadmap_result: dict, team_id: str) -> list[dict]:
    """Push roadmap stories to Linear as issues."""
    linear = LinearConnector()
    roadmap = roadmap_result["roadmap"]
    created_issues = []

    # Create a project
    project = await linear.create_project(
        team_ids=[team_id],
        name=roadmap["project_title"],
        description=f"Client: {roadmap['client']}\nDuration: {roadmap['total_duration']}",
    )
    print(f"[Linear] Created project: {project.get('name')}")

    # Create issues for each story across milestones
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
