"""Smoke test for the full Kisasa AI PM pipeline.

Usage:
    # Mock mode (no API keys needed):
    python -m tests.smoke_test

    # Live mode (requires ANTHROPIC_API_KEY in .env):
    python -m tests.smoke_test --live
"""

from __future__ import annotations

import asyncio
import json
import sys
import os
from unittest.mock import patch, MagicMock

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

SAMPLE_INPUT = """
Hey team, just got off a call with Nexura Health. They're a mid-size healthtech
company running a patient portal built on Rails 5 — it's been in production since
2018 and they're hitting scaling walls. 20k daily active users now, expecting 100k
by end of year after their Series B expansion.

They want to:
1. Migrate the portal to a modern stack (React frontend, API backend)
2. Add real-time messaging between patients and providers
3. Get HIPAA-compliant infrastructure set up on AWS

Budget is $750k over 9 months. Their VP of Engineering (Dana Park) and Chief
Medical Officer (Dr. Ray Santos) are co-sponsoring. Big risk: they have zero
cloud experience — entire team has only worked on Heroku.

Timeline is tight because they're launching in two new states in Q4.
"""

# --- Mock responses for each stage ---

MOCK_BRIEF = {
    "title": "Nexura Health Patient Portal Modernization",
    "client": "Nexura Health",
    "division": "labs",
    "problem_statement": "Legacy Rails 5 patient portal hitting scaling limits at 20k DAU, needs to support 100k by EOY",
    "goals": [
        "Migrate to modern stack (React + API backend)",
        "Add real-time patient-provider messaging",
        "HIPAA-compliant AWS infrastructure",
    ],
    "constraints": ["$750k budget", "9-month timeline", "Team has no cloud experience", "HIPAA compliance required"],
    "scope": "Full portal migration, real-time messaging, AWS infrastructure setup, team upskilling",
    "stakeholders": ["Dana Park (VP Eng)", "Dr. Ray Santos (CMO)"],
    "suggested_timeline": "9 months",
    "risk_flags": [
        "Team has zero cloud/AWS experience",
        "HIPAA compliance adds complexity",
        "Tight timeline with Q4 state expansion deadline",
    ],
    "confidence_score": 0.88,
}

MOCK_REPORT = {
    "project_title": "Nexura Health Patient Portal Modernization",
    "market_overview": "Healthtech modernization is a growing market. HIPAA-compliant cloud migration is well-understood.",
    "competitors": [
        {
            "name": "Current Rails Portal",
            "description": "Existing system",
            "strengths": ["Known codebase", "Stable"],
            "weaknesses": ["Cannot scale", "Outdated stack"],
            "relevance": "Baseline",
        }
    ],
    "technical_feasibility": "Feasible with strangler fig migration pattern. React + Node/Python API is well-supported for healthtech.",
    "recommended_tech_stack": ["React", "Node.js", "PostgreSQL", "AWS ECS", "Redis", "WebSockets"],
    "risks": [
        {
            "category": "regulatory",
            "description": "HIPAA compliance requires careful data handling",
            "severity": "high",
            "mitigation": "Engage HIPAA compliance consultant in Phase 1",
        },
        {
            "category": "resource",
            "description": "Team has no AWS experience",
            "severity": "medium",
            "mitigation": "AWS training bootcamp in first month",
        },
    ],
    "go_no_go_recommendation": "conditional_go",
    "conditions": ["HIPAA compliance consultant engaged", "AWS training scheduled"],
    "estimated_complexity": "high",
    "next_steps": ["Engage HIPAA consultant", "Schedule AWS training", "Define API boundaries"],
}

MOCK_ROADMAP = {
    "project_title": "Nexura Health Patient Portal Modernization",
    "client": "Nexura Health",
    "total_duration": "9 months",
    "milestones": [
        {
            "name": "Phase 1: Foundation & Training",
            "target_date": "Month 2",
            "stories": [
                {
                    "title": "AWS infrastructure setup",
                    "description": "Provision HIPAA-compliant AWS environment with ECS, RDS, and VPC",
                    "acceptance_criteria": ["HIPAA-compliant VPC configured", "ECS cluster running", "RDS PostgreSQL provisioned"],
                    "effort_estimate": "large",
                    "priority_score": 95.0,
                    "labels": ["infrastructure", "hipaa"],
                },
                {
                    "title": "Team AWS training bootcamp",
                    "description": "2-week intensive AWS training for engineering team",
                    "acceptance_criteria": ["All engineers complete AWS fundamentals", "Hands-on lab exercises done"],
                    "effort_estimate": "medium",
                    "priority_score": 90.0,
                    "labels": ["training"],
                },
            ],
            "success_criteria": ["AWS environment operational", "Team can deploy independently"],
        },
        {
            "name": "Phase 2: API & Frontend Migration",
            "target_date": "Month 6",
            "stories": [
                {
                    "title": "Build patient API",
                    "description": "RESTful API for patient data with HIPAA-compliant auth",
                    "acceptance_criteria": ["CRUD endpoints for patient records", "OAuth2 + RBAC auth", "Audit logging"],
                    "effort_estimate": "xlarge",
                    "priority_score": 88.0,
                    "labels": ["api", "hipaa"],
                },
                {
                    "title": "React frontend shell",
                    "description": "React app with routing, auth, and patient dashboard",
                    "acceptance_criteria": ["Login flow working", "Patient dashboard renders", "Mobile responsive"],
                    "effort_estimate": "large",
                    "priority_score": 85.0,
                    "labels": ["frontend"],
                },
            ],
            "success_criteria": ["API serving patient data", "React frontend deployed to staging"],
        },
        {
            "name": "Phase 3: Real-time Messaging & Launch",
            "target_date": "Month 9",
            "stories": [
                {
                    "title": "Real-time messaging system",
                    "description": "WebSocket-based messaging between patients and providers",
                    "acceptance_criteria": ["Messages deliver in <1s", "Message history persisted", "HIPAA-compliant encryption"],
                    "effort_estimate": "xlarge",
                    "priority_score": 82.0,
                    "labels": ["messaging", "hipaa"],
                },
            ],
            "success_criteria": ["Messaging live in production", "All HIPAA audits passed"],
        },
    ],
    "dependencies": ["AWS environment must be ready before API work", "API must be ready before frontend integration"],
    "assumptions": ["HIPAA consultant available", "Nexura team allocated full-time"],
    "out_of_scope": ["Mobile native apps", "Billing system changes", "Legacy data migration beyond patient records"],
}


def mock_claude_response(data):
    msg = MagicMock()
    content = MagicMock()
    content.text = json.dumps(data)
    msg.content = [content]
    return msg


def print_section(title: str, content: str = ""):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")
    if content:
        print(content)


async def run_smoke_test_mock():
    """Run full pipeline with mocked Claude responses."""
    from src.pipeline.orchestrator import run_planning_pipeline, run_qa
    from src.pipeline.roadmap.models import Roadmap
    from src.data.models import Base
    from src.data.repository import ProjectRepository, EmbeddingRepository
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    print_section("SMOKE TEST — MOCK MODE")
    print("Testing full pipeline chain without API keys.\n")

    # --- Stage 1-3: Planning Pipeline ---
    print_section("Stages 1-3: Intake -> Research -> Roadmap")

    with patch("src.pipeline.orchestrator.process_intake") as mock_intake, \
         patch("src.pipeline.orchestrator.process_research") as mock_research, \
         patch("src.pipeline.orchestrator.process_roadmap") as mock_roadmap:

        from src.pipeline.intake.models import ProjectBrief
        from src.pipeline.research.models import FeasibilityReport

        mock_intake.return_value = ProjectBrief(**MOCK_BRIEF)
        mock_research.return_value = FeasibilityReport(**MOCK_REPORT)
        mock_roadmap.return_value = Roadmap(**MOCK_ROADMAP)

        result = await run_planning_pipeline(raw_input=SAMPLE_INPUT)

    brief = result["brief"]
    report = result["report"]
    roadmap = result["roadmap"]

    print(f"  Project:        {brief['title']}")
    print(f"  Client:         {brief['client']}")
    print(f"  Division:       {brief['division']}")
    print(f"  Confidence:     {brief['confidence_score']:.0%}")
    print(f"  Recommendation: {report['go_no_go_recommendation']}")
    print(f"  Complexity:     {report['estimated_complexity']}")
    print(f"  Milestones:     {len(roadmap['milestones'])}")
    total_stories = sum(len(m["stories"]) for m in roadmap["milestones"])
    print(f"  Stories:        {total_stories}")
    print(f"  Status:         {result['status']}")

    assert result["status"] == "ready_to_build", f"Expected ready_to_build, got {result['status']}"
    print("\n  [PASS] Planning pipeline completed successfully")

    # --- Stage 5: QA ---
    print_section("Stage 5: QA & Validation")

    mock_test_cases = [
        {
            "id": "TC-001",
            "title": "AWS VPC compliance check",
            "description": "Verify VPC meets HIPAA requirements",
            "steps": ["Check VPC config", "Verify encryption"],
            "expected_result": "HIPAA-compliant VPC",
            "story_reference": "AWS infrastructure setup",
        }
    ]

    with patch("src.pipeline.qa.agent.anthropic.Anthropic") as mock_anthropic:
        mock_client = MagicMock()
        mock_client.messages.create.return_value = mock_claude_response(mock_test_cases)
        mock_anthropic.return_value = mock_client

        qa_result = run_qa(
            Roadmap(**MOCK_ROADMAP),
            milestone_index=0,
            test_results=[
                {
                    "test_case_id": "TC-001",
                    "status": "pass",
                    "actual_result": "VPC is compliant",
                    "notes": "All checks passed",
                }
            ],
        )

    validation = qa_result["validation"]
    print(f"  Pass rate:      {validation['pass_rate']:.0%}")
    print(f"  Ready to launch: {validation['ready_for_launch']}")
    print(f"  Blockers:       {len(validation['blockers'])}")

    assert validation["ready_for_launch"], "Expected ready_for_launch=True"
    print("\n  [PASS] QA stage completed successfully")

    # --- Data Layer ---
    print_section("Data Layer: Persistence & RAG")

    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    repo = ProjectRepository(session=session)
    project = repo.create_project(brief["title"], brief["client"], brief["division"])
    repo.save_brief(project.id, SAMPLE_INPUT, "raw", brief, brief["confidence_score"])
    repo.save_feasibility_report(project.id, report, report["go_no_go_recommendation"])
    repo.save_roadmap(project.id, roadmap, len(roadmap["milestones"]), total_stories)
    repo.update_project_status(project.id, "roadmap")

    retrieved = repo.get_project(project.id)
    print(f"  Project saved:  {retrieved.title}")
    print(f"  Status:         {retrieved.status}")
    print(f"  Brief stored:   {retrieved.brief is not None}")
    print(f"  Report stored:  {retrieved.feasibility_report is not None}")
    print(f"  Roadmap stored: {retrieved.roadmap is not None}")

    embed_repo = EmbeddingRepository(session=session)
    embed_repo.store_embedding(project.id, "brief", brief["problem_statement"], [0.8, 0.2, 0.1])
    embed_repo.store_embedding(project.id, "report", report["market_overview"], [0.3, 0.7, 0.1])

    similar = embed_repo.search_similar([0.9, 0.1, 0.1], limit=1)
    print(f"  RAG search:     Found '{similar[0].content_type}' (closest match)")

    assert retrieved.status == "roadmap"
    assert len(similar) == 1
    print("\n  [PASS] Data layer working correctly")

    # --- Summary ---
    print_section("SMOKE TEST COMPLETE")
    print("  All pipeline stages wired correctly.")
    print("  Data persistence and RAG search working.")
    print("  No API keys required for this test.\n")
    print("  To run with live Claude API:")
    print("    python -m tests.smoke_test --live\n")


async def run_smoke_test_live():
    """Run full pipeline with live Claude API calls."""
    from src.pipeline.orchestrator import run_planning_pipeline
    from src.utils.config import Config

    if not Config.ANTHROPIC_API_KEY:
        print("\n  ERROR: ANTHROPIC_API_KEY not set in .env")
        print("  Copy .env.example to .env and add your key.\n")
        sys.exit(1)

    print_section("SMOKE TEST — LIVE MODE")
    print("Running full pipeline with real Claude API calls.\n")
    print(f"  Model: {Config.MODEL}")
    print(f"  Input: {len(SAMPLE_INPUT)} chars\n")

    print_section("Stages 1-3: Intake -> Research -> Roadmap")
    print("  Calling Claude API (this may take 30-60 seconds)...\n")

    result = await run_planning_pipeline(raw_input=SAMPLE_INPUT)

    brief = result["brief"]
    report = result["report"]
    roadmap = result["roadmap"]

    print(f"  Project:        {brief['title']}")
    print(f"  Client:         {brief['client']}")
    print(f"  Division:       {brief['division']}")
    print(f"  Confidence:     {brief['confidence_score']:.0%}")
    print(f"  Recommendation: {report['go_no_go_recommendation']}")
    print(f"  Complexity:     {report['estimated_complexity']}")
    print(f"  Milestones:     {len(roadmap['milestones'])}")
    total_stories = sum(len(m["stories"]) for m in roadmap["milestones"])
    print(f"  Stories:        {total_stories}")
    print(f"  Tech Stack:     {', '.join(report['recommended_tech_stack'][:5])}")

    if report["risks"]:
        print(f"\n  Top risks:")
        for risk in report["risks"][:3]:
            print(f"    [{risk['severity']}] {risk['description']}")

    if roadmap["milestones"]:
        print(f"\n  Roadmap:")
        for ms in roadmap["milestones"]:
            print(f"    {ms['name']} ({ms['target_date']}) — {len(ms['stories'])} stories")

    print_section("LIVE SMOKE TEST COMPLETE")
    print(f"  Pipeline processed input and generated:")
    print(f"    - Project brief (confidence: {brief['confidence_score']:.0%})")
    print(f"    - Feasibility report ({report['go_no_go_recommendation']})")
    print(f"    - Roadmap ({len(roadmap['milestones'])} milestones, {total_stories} stories)\n")


if __name__ == "__main__":
    live = "--live" in sys.argv
    if live:
        asyncio.run(run_smoke_test_live())
    else:
        asyncio.run(run_smoke_test_mock())
