"""Tests for all Pydantic models across pipeline stages."""

import pytest
from pydantic import ValidationError

from src.pipeline.intake.models import ProjectBrief, Division
from src.pipeline.research.models import FeasibilityReport, CompetitorInfo, RiskItem
from src.pipeline.roadmap.models import Roadmap, Milestone, Story
from src.pipeline.build.models import PRReview, ScopeCheck, ScopeStatus, BuildReport
from src.pipeline.qa.models import (
    TestCase, TestResult, TestStatus, BugTicket, UATFeedback, ValidationReport,
)
from src.pipeline.launch.models import RunbookStep, Documentation, HandoffPackage
from src.pipeline.retro.models import EstimateAccuracy, Insight, RetroReport


# ---------------------------------------------------------------------------
# Stage 1: Intake models
# ---------------------------------------------------------------------------

class TestDivision:
    def test_valid_divisions(self):
        assert Division.VENTURES == "ventures"
        assert Division.LABS == "labs"
        assert Division.STRATEGY == "strategy"

    def test_invalid_division(self):
        with pytest.raises(ValueError):
            Division("invalid")


class TestProjectBrief:
    def test_valid_brief(self, sample_brief):
        assert sample_brief.title == "Acme Corp Monolith Decomposition"
        assert sample_brief.division == Division.LABS
        assert sample_brief.confidence_score == 0.85

    def test_brief_requires_all_fields(self):
        with pytest.raises(ValidationError):
            ProjectBrief(title="Test")

    def test_brief_serialization(self, sample_brief):
        data = sample_brief.model_dump()
        assert data["division"] == "labs"
        roundtrip = ProjectBrief(**data)
        assert roundtrip == sample_brief


# ---------------------------------------------------------------------------
# Stage 2: Research models
# ---------------------------------------------------------------------------

class TestFeasibilityReport:
    def test_valid_report(self, sample_feasibility_report):
        assert sample_feasibility_report.go_no_go_recommendation == "go"
        assert len(sample_feasibility_report.competitors) == 1
        assert len(sample_feasibility_report.risks) == 1

    def test_risk_item(self):
        risk = RiskItem(
            category="technical",
            description="Untested library",
            severity="high",
            mitigation="Spike first",
        )
        assert risk.severity == "high"

    def test_competitor_info(self):
        comp = CompetitorInfo(
            name="Rival Co",
            description="Competitor product",
            strengths=["Fast"],
            weaknesses=["Expensive"],
            relevance="Direct competitor",
        )
        assert comp.name == "Rival Co"

    def test_report_serialization(self, sample_feasibility_report):
        data = sample_feasibility_report.model_dump()
        roundtrip = FeasibilityReport(**data)
        assert roundtrip == sample_feasibility_report


# ---------------------------------------------------------------------------
# Stage 3: Roadmap models
# ---------------------------------------------------------------------------

class TestRoadmap:
    def test_valid_roadmap(self, sample_roadmap):
        assert len(sample_roadmap.milestones) == 2
        assert sample_roadmap.total_duration == "6 months"

    def test_milestone_stories(self, sample_roadmap):
        phase1 = sample_roadmap.milestones[0]
        assert len(phase1.stories) == 2
        assert phase1.stories[0].priority_score == 90.0

    def test_story_model(self):
        story = Story(
            title="Test story",
            description="A test",
            acceptance_criteria=["It works"],
            effort_estimate="small",
            priority_score=50.0,
            labels=["test"],
        )
        assert story.effort_estimate == "small"

    def test_roadmap_serialization(self, sample_roadmap):
        data = sample_roadmap.model_dump()
        roundtrip = Roadmap(**data)
        assert roundtrip == sample_roadmap


# ---------------------------------------------------------------------------
# Stage 4: Build models
# ---------------------------------------------------------------------------

class TestBuildModels:
    def test_scope_status_enum(self):
        assert ScopeStatus.ON_TRACK == "on_track"
        assert ScopeStatus.SCOPE_CREEP == "scope_creep"

    def test_pr_review(self):
        review = PRReview(
            pr_number=42,
            pr_title="Add auth service",
            summary="Implements OAuth2 flow",
            issues=["Missing error handling in token refresh"],
            suggestions=["Add retry logic"],
            approval_recommendation="request_changes",
        )
        assert review.approval_recommendation == "request_changes"
        assert len(review.issues) == 1

    def test_scope_check(self):
        check = ScopeCheck(
            story_title="Extract auth service",
            status=ScopeStatus.AT_RISK,
            deviation="Adding OAuth2 support not in original scope",
            recommendation="Discuss with PM before proceeding",
        )
        assert check.status == ScopeStatus.AT_RISK

    def test_build_report(self):
        report = BuildReport(
            milestone_name="Phase 1",
            stories_completed=3,
            stories_total=5,
            pr_reviews=[],
            scope_checks=[],
            blockers=[],
            overall_health="green",
        )
        assert report.overall_health == "green"
        assert report.stories_completed == 3


# ---------------------------------------------------------------------------
# Stage 5: QA models
# ---------------------------------------------------------------------------

class TestQAModels:
    def test_test_status_enum(self):
        assert TestStatus.PASS == "pass"
        assert TestStatus.FAIL == "fail"
        assert TestStatus.SKIP == "skip"

    def test_test_case(self, sample_test_cases):
        tc = sample_test_cases[0]
        assert tc.id == "TC-001"
        assert len(tc.steps) == 2

    def test_test_result(self, sample_test_results):
        tr = sample_test_results[0]
        assert tr.status == TestStatus.PASS

    def test_bug_ticket(self):
        bug = BugTicket(
            title="Login fails on Safari",
            description="OAuth redirect broken in Safari 17",
            severity="high",
            steps_to_reproduce=["Open Safari", "Click login", "Observe error"],
            expected_behavior="User is logged in",
            actual_behavior="Blank page after redirect",
            story_reference="Extract auth service",
        )
        assert bug.severity == "high"
        assert len(bug.steps_to_reproduce) == 3

    def test_uat_feedback(self):
        feedback = UATFeedback(
            source="Sarah (CTO)",
            sentiment="positive",
            summary="Deploy process is much faster now",
            action_items=["Document the new process"],
            linked_stories=["Set up Kubernetes cluster"],
        )
        assert feedback.sentiment == "positive"

    def test_validation_report(self, sample_validation_report):
        assert sample_validation_report.pass_rate == 1.0
        assert sample_validation_report.ready_for_launch is True
        assert len(sample_validation_report.blockers) == 0


# ---------------------------------------------------------------------------
# Stage 6: Launch models
# ---------------------------------------------------------------------------

class TestLaunchModels:
    def test_runbook_step(self):
        step = RunbookStep(
            order=1,
            title="Deploy to staging",
            command_or_action="kubectl apply -f staging/",
            expected_outcome="Pods running in staging namespace",
            rollback="kubectl rollout undo deployment/app",
        )
        assert step.order == 1

    def test_documentation(self):
        doc = Documentation(
            title="Architecture Overview",
            sections=[
                {"heading": "Overview", "content": "The system uses microservices..."},
                {"heading": "Components", "content": "Auth, API Gateway, ..."},
            ],
        )
        assert len(doc.sections) == 2

    def test_handoff_package(self):
        package = HandoffPackage(
            project_title="Acme Decomposition",
            client="Acme Corp",
            documentation=[],
            runbook=[],
            environment_details={"staging_url": "https://staging.acme.com"},
            known_issues=["Occasional timeout on cold start"],
            monitoring_checklist=["Check latency dashboard"],
            onboarding_guide="# Welcome\nStart here...",
        )
        assert package.client == "Acme Corp"
        assert "staging_url" in package.environment_details


# ---------------------------------------------------------------------------
# Stage 7: Retro models
# ---------------------------------------------------------------------------

class TestRetroModels:
    def test_estimate_accuracy(self):
        ea = EstimateAccuracy(
            story_title="Set up K8s cluster",
            estimated_effort="large",
            actual_effort="xlarge",
            accuracy_pct=130.0,
        )
        assert ea.accuracy_pct == 130.0

    def test_insight(self):
        insight = Insight(
            category="estimation",
            observation="K8s setup took 30% longer than estimated",
            recommendation="Add buffer for infra work when team is new to tech",
            priority="high",
        )
        assert insight.category == "estimation"

    def test_retro_report(self):
        report = RetroReport(
            project_title="Acme Decomposition",
            client="Acme Corp",
            duration_planned="6 months",
            duration_actual="7 months",
            estimate_accuracy=[],
            average_accuracy_pct=115.0,
            what_went_well=["Team upskilling was effective"],
            what_could_improve=["Better initial estimation"],
            insights=[],
            updated_estimation_rules=["Add 30% buffer for new tech adoption"],
        )
        assert report.average_accuracy_pct == 115.0
        assert len(report.updated_estimation_rules) == 1
