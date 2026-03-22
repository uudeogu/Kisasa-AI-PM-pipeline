"""Tests for the pipeline orchestrator."""

import json
import pytest
from unittest.mock import patch, MagicMock, AsyncMock

from src.pipeline.orchestrator import (
    run_planning_pipeline,
    run_build_monitor,
    run_qa,
    run_launch,
    run_retro,
    sync_to_linear,
    sync_to_notion,
)


def mock_claude_response(response_json):
    mock_message = MagicMock()
    mock_content = MagicMock()
    mock_content.text = json.dumps(response_json)
    mock_message.content = [mock_content]
    return mock_message


MOCK_BRIEF_RESPONSE = {
    "title": "Test Project",
    "client": "Test Client",
    "division": "labs",
    "problem_statement": "Need modernization",
    "goals": ["Modernize"],
    "constraints": ["Budget"],
    "scope": "Full system",
    "stakeholders": ["CTO"],
    "suggested_timeline": "3 months",
    "risk_flags": [],
    "confidence_score": 0.9,
}

MOCK_RESEARCH_RESPONSE = {
    "project_title": "Test Project",
    "market_overview": "Good market.",
    "competitors": [],
    "technical_feasibility": "Feasible.",
    "recommended_tech_stack": ["Python"],
    "risks": [],
    "go_no_go_recommendation": "go",
    "conditions": [],
    "estimated_complexity": "medium",
    "next_steps": ["Start building"],
}

MOCK_ROADMAP_RESPONSE = {
    "project_title": "Test Project",
    "client": "Test Client",
    "total_duration": "3 months",
    "milestones": [
        {
            "name": "Phase 1",
            "target_date": "Month 1",
            "stories": [
                {
                    "title": "Story 1",
                    "description": "Do the thing",
                    "acceptance_criteria": ["It works"],
                    "effort_estimate": "medium",
                    "priority_score": 80.0,
                    "labels": ["core"],
                }
            ],
            "success_criteria": ["Phase complete"],
        }
    ],
    "dependencies": [],
    "assumptions": ["Team available"],
    "out_of_scope": [],
}


class TestPlanningPipeline:
    @pytest.mark.asyncio
    async def test_full_planning_pipeline(self):
        """Test Stages 1-3 run end-to-end with mocked stage functions."""
        from src.pipeline.intake.models import ProjectBrief, Division
        from src.pipeline.research.models import FeasibilityReport
        from src.pipeline.roadmap.models import Roadmap

        mock_brief = ProjectBrief(**MOCK_BRIEF_RESPONSE)
        mock_report = FeasibilityReport(**MOCK_RESEARCH_RESPONSE)
        mock_roadmap = Roadmap(**MOCK_ROADMAP_RESPONSE)

        with patch("src.pipeline.orchestrator.process_intake", return_value=mock_brief), \
             patch("src.pipeline.orchestrator.process_research", return_value=mock_report), \
             patch("src.pipeline.orchestrator.process_roadmap", return_value=mock_roadmap):

            result = await run_planning_pipeline(raw_input="Client wants modernization")

            assert result["status"] == "ready_to_build"
            assert result["brief"]["title"] == "Test Project"
            assert result["report"]["go_no_go_recommendation"] == "go"
            assert len(result["roadmap"]["milestones"]) == 1

    @pytest.mark.asyncio
    async def test_pipeline_stops_on_no_go(self):
        """Test that pipeline stops when research recommends no-go."""
        from src.pipeline.intake.models import ProjectBrief
        from src.pipeline.research.models import FeasibilityReport

        mock_brief = ProjectBrief(**MOCK_BRIEF_RESPONSE)
        no_go_data = {**MOCK_RESEARCH_RESPONSE, "go_no_go_recommendation": "no_go"}
        mock_report = FeasibilityReport(**no_go_data)

        with patch("src.pipeline.orchestrator.process_intake", return_value=mock_brief), \
             patch("src.pipeline.orchestrator.process_research", return_value=mock_report):

            result = await run_planning_pipeline(raw_input="Vague idea")

            assert result["status"] == "no_go"
            assert result["stage"] == "research"
            assert "roadmap" not in result

    @pytest.mark.asyncio
    async def test_pipeline_requires_input(self):
        """Test that pipeline raises error when no input is provided."""
        with pytest.raises(ValueError, match="Provide raw_input"):
            await run_planning_pipeline()

    @pytest.mark.asyncio
    async def test_pipeline_with_slack_input(self):
        """Test pipeline with Slack as input source."""
        from src.pipeline.intake.models import ProjectBrief
        from src.pipeline.research.models import FeasibilityReport
        from src.pipeline.roadmap.models import Roadmap

        mock_brief = ProjectBrief(**MOCK_BRIEF_RESPONSE)
        mock_report = FeasibilityReport(**MOCK_RESEARCH_RESPONSE)
        mock_roadmap = Roadmap(**MOCK_ROADMAP_RESPONSE)

        with patch("src.pipeline.orchestrator.ingest_from_slack", new_callable=AsyncMock, return_value="Client: We need help"), \
             patch("src.pipeline.orchestrator.process_intake", return_value=mock_brief), \
             patch("src.pipeline.orchestrator.process_research", return_value=mock_report), \
             patch("src.pipeline.orchestrator.process_roadmap", return_value=mock_roadmap):

            result = await run_planning_pipeline(slack_channel_id="C123")
            assert result["status"] == "ready_to_build"


class TestQAStage:
    def test_run_qa_with_passing_results(self, sample_roadmap):
        """Test QA stage with all tests passing."""
        test_cases_response = [
            {
                "id": "TC-001",
                "title": "Test cluster",
                "description": "Verify K8s",
                "steps": ["kubectl get nodes"],
                "expected_result": "Nodes listed",
                "story_reference": "Set up Kubernetes cluster",
            }
        ]

        with patch("src.pipeline.qa.agent.anthropic.Anthropic") as mock_anthropic:
            client = MagicMock()
            client.messages.create.return_value = mock_claude_response(test_cases_response)
            mock_anthropic.return_value = client

            result = run_qa(
                sample_roadmap,
                milestone_index=0,
                test_results=[
                    {
                        "test_case_id": "TC-001",
                        "status": "pass",
                        "actual_result": "3 nodes",
                        "notes": "OK",
                    }
                ],
            )

            assert result["stage"] == "qa"
            assert result["validation"]["pass_rate"] == 1.0
            assert result["validation"]["ready_for_launch"] is True

    def test_run_qa_with_failures(self, sample_roadmap):
        """Test QA stage with test failures and bugs."""
        test_cases_response = [
            {
                "id": "TC-001",
                "title": "Test cluster",
                "description": "Verify K8s",
                "steps": ["kubectl get nodes"],
                "expected_result": "Nodes listed",
                "story_reference": "Set up Kubernetes cluster",
            }
        ]

        with patch("src.pipeline.qa.agent.anthropic.Anthropic") as mock_anthropic:
            client = MagicMock()
            client.messages.create.return_value = mock_claude_response(test_cases_response)
            mock_anthropic.return_value = client

            result = run_qa(
                sample_roadmap,
                milestone_index=0,
                test_results=[
                    {
                        "test_case_id": "TC-001",
                        "status": "fail",
                        "actual_result": "Connection refused",
                        "notes": "Cluster not reachable",
                    }
                ],
                bug_reports=[
                    {
                        "title": "K8s unreachable",
                        "description": "Cannot connect to cluster",
                        "severity": "critical",
                        "steps_to_reproduce": ["Run kubectl"],
                        "expected_behavior": "Nodes listed",
                        "actual_behavior": "Connection refused",
                        "story_reference": "Set up Kubernetes cluster",
                    }
                ],
            )

            assert result["validation"]["pass_rate"] == 0.0
            assert result["validation"]["ready_for_launch"] is False
            assert len(result["validation"]["blockers"]) > 0


class TestRetroStage:
    def test_run_retro(self, sample_brief, sample_roadmap):
        """Test retrospective stage."""
        retro_response = {
            "project_title": "Acme Decomposition",
            "client": "Acme Corp",
            "duration_planned": "6 months",
            "duration_actual": "7 months",
            "estimate_accuracy": [],
            "average_accuracy_pct": 115.0,
            "what_went_well": ["Good collaboration"],
            "what_could_improve": ["Estimation"],
            "insights": [],
            "updated_estimation_rules": ["Add buffer for new tech"],
        }

        with patch("src.pipeline.retro.agent.anthropic.Anthropic") as mock_anthropic:
            client = MagicMock()
            client.messages.create.return_value = mock_claude_response(retro_response)
            mock_anthropic.return_value = client

            pipeline_result = {
                "brief": sample_brief.model_dump(),
                "roadmap": sample_roadmap.model_dump(),
            }

            result = run_retro(pipeline_result, "7 months", [])
            assert result["stage"] == "retro"
            assert result["retro"]["average_accuracy_pct"] == 115.0


class TestLinearSync:
    @pytest.mark.asyncio
    async def test_sync_to_linear(self):
        """Test syncing roadmap to Linear."""
        pipeline_result = {"roadmap": MOCK_ROADMAP_RESPONSE}

        with patch("src.pipeline.orchestrator.LinearConnector") as MockLinear:
            mock_linear = MagicMock()
            mock_linear.create_project = AsyncMock(return_value={"name": "Test Project", "id": "proj-1"})
            mock_linear.create_issue = AsyncMock(return_value={
                "id": "issue-1",
                "identifier": "KIS-1",
                "title": "Story 1",
                "url": "https://linear.app/kisasa/issue/KIS-1",
            })
            MockLinear.return_value = mock_linear

            issues = await sync_to_linear(pipeline_result, "team-1")
            assert len(issues) == 1
            assert issues[0]["identifier"] == "KIS-1"
            mock_linear.create_project.assert_called_once()


class TestNotionSync:
    @pytest.mark.asyncio
    async def test_sync_to_notion(self):
        """Test syncing roadmap to Notion."""
        pipeline_result = {
            "brief": MOCK_BRIEF_RESPONSE,
            "roadmap": MOCK_ROADMAP_RESPONSE,
        }

        with patch("src.pipeline.orchestrator.NotionConnector") as MockNotion:
            mock_notion = MagicMock()
            mock_notion.create_page = AsyncMock(return_value={"id": "page-123"})
            MockNotion.return_value = mock_notion

            page = await sync_to_notion(pipeline_result, "db-1")
            assert page["id"] == "page-123"
            mock_notion.create_page.assert_called_once()
