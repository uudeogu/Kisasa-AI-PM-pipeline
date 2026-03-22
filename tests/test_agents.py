"""Tests for pipeline agents with mocked Claude API calls."""

import json
import pytest
from unittest.mock import patch, MagicMock, AsyncMock

from src.pipeline.intake.agent import process_intake, ingest_from_slack
from src.pipeline.intake.models import ProjectBrief, Division
from src.pipeline.research.agent import process_research
from src.pipeline.research.models import FeasibilityReport
from src.pipeline.roadmap.agent import process_roadmap
from src.pipeline.build.agent import review_pr, check_scope
from src.pipeline.build.models import PRReview, ScopeCheck, ScopeStatus
from src.pipeline.qa.agent import generate_test_cases, triage_uat_feedback, triage_bug_report
from src.pipeline.qa.models import TestCase, UATFeedback, BugTicket
from src.pipeline.launch.agent import generate_handoff
from src.pipeline.launch.models import HandoffPackage
from src.pipeline.retro.agent import generate_retro
from src.pipeline.retro.models import RetroReport


def mock_claude_response(response_json: dict):
    """Create a mock Anthropic messages.create response."""
    mock_message = MagicMock()
    mock_content = MagicMock()
    mock_content.text = json.dumps(response_json)
    mock_message.content = [mock_content]
    return mock_message


# ---------------------------------------------------------------------------
# Stage 1: Intake Agent
# ---------------------------------------------------------------------------

class TestIntakeAgent:
    def test_process_intake(self):
        response = {
            "title": "Acme Modernization",
            "client": "Acme Corp",
            "division": "labs",
            "problem_statement": "Legacy system needs modernization",
            "goals": ["Faster deploys", "Better scalability"],
            "constraints": ["$500k budget"],
            "scope": "Monolith to microservices",
            "stakeholders": ["Sarah"],
            "suggested_timeline": "6 months",
            "risk_flags": [],
            "confidence_score": 0.9,
        }

        with patch("src.pipeline.intake.agent.anthropic.Anthropic") as mock_anthropic:
            mock_client = MagicMock()
            mock_client.messages.create.return_value = mock_claude_response(response)
            mock_anthropic.return_value = mock_client

            brief = process_intake("Some client conversation about modernization")
            assert isinstance(brief, ProjectBrief)
            assert brief.title == "Acme Modernization"
            assert brief.division == Division.LABS
            assert brief.confidence_score == 0.9

    def test_process_intake_low_confidence(self):
        response = {
            "title": "Unknown Project",
            "client": "Unknown",
            "division": "ventures",
            "problem_statement": "Unclear requirements",
            "goals": [],
            "constraints": [],
            "scope": "TBD",
            "stakeholders": [],
            "suggested_timeline": "Unknown",
            "risk_flags": ["Very vague input", "No client identified"],
            "confidence_score": 0.3,
        }

        with patch("src.pipeline.intake.agent.anthropic.Anthropic") as mock_anthropic:
            mock_client = MagicMock()
            mock_client.messages.create.return_value = mock_claude_response(response)
            mock_anthropic.return_value = mock_client

            brief = process_intake("maybe build something?")
            assert brief.confidence_score == 0.3
            assert len(brief.risk_flags) == 2

    @pytest.mark.asyncio
    async def test_ingest_from_slack(self):
        with patch("src.pipeline.intake.agent.SlackConnector") as MockSlack:
            mock_instance = MagicMock()
            mock_instance.format_conversation = AsyncMock(return_value="User: Let's build an app")
            MockSlack.return_value = mock_instance

            text = await ingest_from_slack("C123")
            assert "Let's build an app" in text


# ---------------------------------------------------------------------------
# Stage 2: Research Agent
# ---------------------------------------------------------------------------

class TestResearchAgent:
    def test_process_research(self, sample_brief):
        response = {
            "project_title": "Acme Corp Monolith Decomposition",
            "market_overview": "Microservices is the standard approach.",
            "competitors": [],
            "technical_feasibility": "Feasible with phased approach.",
            "recommended_tech_stack": ["Kubernetes", "Spring Boot"],
            "risks": [
                {
                    "category": "resource",
                    "description": "Team needs training",
                    "severity": "medium",
                    "mitigation": "Phase 1 training",
                }
            ],
            "go_no_go_recommendation": "go",
            "conditions": [],
            "estimated_complexity": "high",
            "next_steps": ["Define service boundaries"],
        }

        with patch("src.pipeline.research.agent.anthropic.Anthropic") as mock_anthropic:
            mock_client = MagicMock()
            mock_client.messages.create.return_value = mock_claude_response(response)
            mock_anthropic.return_value = mock_client

            report = process_research(sample_brief)
            assert isinstance(report, FeasibilityReport)
            assert report.go_no_go_recommendation == "go"
            assert report.estimated_complexity == "high"

    def test_process_research_no_go(self, sample_brief):
        response = {
            "project_title": "Acme Corp Monolith Decomposition",
            "market_overview": "Market is saturated.",
            "competitors": [],
            "technical_feasibility": "Not feasible within constraints.",
            "recommended_tech_stack": [],
            "risks": [
                {
                    "category": "timeline",
                    "description": "Impossible in Q3",
                    "severity": "critical",
                    "mitigation": "Extend timeline to 12 months",
                }
            ],
            "go_no_go_recommendation": "no_go",
            "conditions": [],
            "estimated_complexity": "high",
            "next_steps": ["Revisit scope with client"],
        }

        with patch("src.pipeline.research.agent.anthropic.Anthropic") as mock_anthropic:
            mock_client = MagicMock()
            mock_client.messages.create.return_value = mock_claude_response(response)
            mock_anthropic.return_value = mock_client

            report = process_research(sample_brief)
            assert report.go_no_go_recommendation == "no_go"


# ---------------------------------------------------------------------------
# Stage 3: Roadmap Agent
# ---------------------------------------------------------------------------

class TestRoadmapAgent:
    def test_process_roadmap(self, sample_brief, sample_feasibility_report):
        response = {
            "project_title": "Acme Decomposition",
            "client": "Acme Corp",
            "total_duration": "6 months",
            "milestones": [
                {
                    "name": "Phase 1",
                    "target_date": "Month 2",
                    "stories": [
                        {
                            "title": "Setup K8s",
                            "description": "Provision cluster",
                            "acceptance_criteria": ["Cluster running"],
                            "effort_estimate": "large",
                            "priority_score": 90.0,
                            "labels": ["infra"],
                        }
                    ],
                    "success_criteria": ["K8s operational"],
                }
            ],
            "dependencies": [],
            "assumptions": ["Cloud account ready"],
            "out_of_scope": ["Mobile"],
        }

        with patch("src.pipeline.roadmap.agent.anthropic.Anthropic") as mock_anthropic:
            mock_client = MagicMock()
            mock_client.messages.create.return_value = mock_claude_response(response)
            mock_anthropic.return_value = mock_client

            roadmap = process_roadmap(sample_brief, sample_feasibility_report)
            assert len(roadmap.milestones) == 1
            assert roadmap.milestones[0].stories[0].title == "Setup K8s"


# ---------------------------------------------------------------------------
# Stage 4: Build Agent
# ---------------------------------------------------------------------------

class TestBuildAgent:
    def test_check_scope(self):
        response = {
            "story_title": "Extract auth service",
            "status": "on_track",
            "deviation": "",
            "recommendation": "Continue as planned",
        }

        with patch("src.pipeline.build.agent.anthropic.Anthropic") as mock_anthropic:
            mock_client = MagicMock()
            mock_client.messages.create.return_value = mock_claude_response(response)
            mock_anthropic.return_value = mock_client

            check = check_scope("Extract auth into microservice", "Building auth microservice with OAuth2")
            assert isinstance(check, ScopeCheck)
            assert check.status == ScopeStatus.ON_TRACK

    def test_check_scope_creep(self):
        response = {
            "story_title": "Extract auth service",
            "status": "scope_creep",
            "deviation": "Adding SSO support not in original scope",
            "recommendation": "Create separate story for SSO",
        }

        with patch("src.pipeline.build.agent.anthropic.Anthropic") as mock_anthropic:
            mock_client = MagicMock()
            mock_client.messages.create.return_value = mock_claude_response(response)
            mock_anthropic.return_value = mock_client

            check = check_scope("Extract auth into microservice", "Building auth with SSO and SAML")
            assert check.status == ScopeStatus.SCOPE_CREEP


# ---------------------------------------------------------------------------
# Stage 5: QA Agent
# ---------------------------------------------------------------------------

class TestQAAgent:
    def test_generate_test_cases(self, sample_roadmap):
        response = [
            {
                "id": "TC-001",
                "title": "Verify K8s cluster",
                "description": "Test cluster accessibility",
                "steps": ["Run kubectl get nodes"],
                "expected_result": "Nodes listed",
                "story_reference": "Set up Kubernetes cluster",
            }
        ]

        with patch("src.pipeline.qa.agent.anthropic.Anthropic") as mock_anthropic:
            mock_client = MagicMock()
            mock_client.messages.create.return_value = mock_claude_response(response)
            mock_anthropic.return_value = mock_client

            milestone = sample_roadmap.milestones[0]
            test_cases = generate_test_cases(milestone)
            assert len(test_cases) == 1
            assert isinstance(test_cases[0], TestCase)
            assert test_cases[0].id == "TC-001"

    def test_triage_uat_feedback(self):
        response = {
            "source": "Sarah (CTO)",
            "sentiment": "positive",
            "summary": "Deploys are much faster now",
            "action_items": ["Document new process"],
            "linked_stories": ["Set up Kubernetes cluster"],
        }

        with patch("src.pipeline.qa.agent.anthropic.Anthropic") as mock_anthropic:
            mock_client = MagicMock()
            mock_client.messages.create.return_value = mock_claude_response(response)
            mock_anthropic.return_value = mock_client

            feedback = triage_uat_feedback(
                "The deploys are so much faster, great job!", ["Set up Kubernetes cluster"]
            )
            assert isinstance(feedback, UATFeedback)
            assert feedback.sentiment == "positive"

    def test_triage_bug_report(self):
        response = {
            "title": "Auth timeout on Safari",
            "description": "OAuth redirect times out",
            "severity": "high",
            "steps_to_reproduce": ["Open Safari", "Click login"],
            "expected_behavior": "User logs in",
            "actual_behavior": "Timeout error",
            "story_reference": "Extract auth service",
        }

        with patch("src.pipeline.qa.agent.anthropic.Anthropic") as mock_anthropic:
            mock_client = MagicMock()
            mock_client.messages.create.return_value = mock_claude_response(response)
            mock_anthropic.return_value = mock_client

            bug = triage_bug_report(
                "Login doesn't work on Safari", ["Extract auth service"]
            )
            assert isinstance(bug, BugTicket)
            assert bug.severity == "high"


# ---------------------------------------------------------------------------
# Stage 6: Launch Agent
# ---------------------------------------------------------------------------

class TestLaunchAgent:
    def test_generate_handoff(self, sample_brief, sample_roadmap, sample_validation_report):
        response = {
            "project_title": "Acme Decomposition",
            "client": "Acme Corp",
            "documentation": [
                {
                    "title": "Architecture Overview",
                    "sections": [{"heading": "Overview", "content": "Microservices arch..."}],
                }
            ],
            "runbook": [
                {
                    "order": 1,
                    "title": "Deploy to staging",
                    "command_or_action": "kubectl apply -f staging/",
                    "expected_outcome": "Pods running",
                    "rollback": "kubectl rollout undo",
                }
            ],
            "environment_details": {"staging": "https://staging.acme.com"},
            "known_issues": ["Cold start latency"],
            "monitoring_checklist": ["Check p99 latency"],
            "onboarding_guide": "# Welcome to the project",
        }

        with patch("src.pipeline.launch.agent.anthropic.Anthropic") as mock_anthropic:
            mock_client = MagicMock()
            mock_client.messages.create.return_value = mock_claude_response(response)
            mock_anthropic.return_value = mock_client

            handoff = generate_handoff(sample_brief, sample_roadmap, sample_validation_report)
            assert isinstance(handoff, HandoffPackage)
            assert len(handoff.documentation) == 1
            assert len(handoff.runbook) == 1


# ---------------------------------------------------------------------------
# Stage 7: Retro Agent
# ---------------------------------------------------------------------------

class TestRetroAgent:
    def test_generate_retro(self, sample_brief, sample_roadmap):
        response = {
            "project_title": "Acme Decomposition",
            "client": "Acme Corp",
            "duration_planned": "6 months",
            "duration_actual": "7 months",
            "estimate_accuracy": [
                {
                    "story_title": "Set up K8s cluster",
                    "estimated_effort": "large",
                    "actual_effort": "xlarge",
                    "accuracy_pct": 130.0,
                }
            ],
            "average_accuracy_pct": 115.0,
            "what_went_well": ["Team upskilling"],
            "what_could_improve": ["Better estimation"],
            "insights": [
                {
                    "category": "estimation",
                    "observation": "Infra work underestimated",
                    "recommendation": "Add 30% buffer",
                    "priority": "high",
                }
            ],
            "updated_estimation_rules": ["Add 30% buffer for new tech"],
        }

        with patch("src.pipeline.retro.agent.anthropic.Anthropic") as mock_anthropic:
            mock_client = MagicMock()
            mock_client.messages.create.return_value = mock_claude_response(response)
            mock_anthropic.return_value = mock_client

            retro = generate_retro(
                sample_brief,
                sample_roadmap,
                "7 months",
                [{"title": "Set up K8s cluster", "actual_effort": "xlarge"}],
            )
            assert isinstance(retro, RetroReport)
            assert retro.average_accuracy_pct == 115.0
            assert len(retro.updated_estimation_rules) == 1
