"""Shared fixtures for all tests."""

import pytest
from src.pipeline.intake.models import ProjectBrief, Division
from src.pipeline.research.models import FeasibilityReport, CompetitorInfo, RiskItem
from src.pipeline.roadmap.models import Roadmap, Milestone, Story
from src.pipeline.qa.models import (
    TestCase, TestResult, TestStatus, BugTicket, UATFeedback, ValidationReport,
)


@pytest.fixture
def sample_brief():
    return ProjectBrief(
        title="Acme Corp Monolith Decomposition",
        client="Acme Corp",
        division=Division.LABS,
        problem_statement="Legacy Java monolith with 4-hour deploy cycles",
        goals=["Reduce deploy time to 15 min", "Move to Kubernetes"],
        constraints=["$500k budget", "Q3 deadline"],
        scope="Decompose monolith, set up K8s, upskill team",
        stakeholders=["Sarah (CTO)", "Marcus (VP Eng)"],
        suggested_timeline="6 months",
        risk_flags=["Team lacks container experience"],
        confidence_score=0.85,
    )


@pytest.fixture
def sample_feasibility_report():
    return FeasibilityReport(
        project_title="Acme Corp Monolith Decomposition",
        market_overview="Microservices adoption is standard for orgs at Acme's scale.",
        competitors=[
            CompetitorInfo(
                name="Existing monolith",
                description="Current system",
                strengths=["Known codebase"],
                weaknesses=["Slow deploys"],
                relevance="Baseline comparison",
            )
        ],
        technical_feasibility="Feasible with phased strangler fig approach.",
        recommended_tech_stack=["Kubernetes", "Java Spring Boot", "Istio", "ArgoCD"],
        risks=[
            RiskItem(
                category="resource",
                description="Team needs K8s training",
                severity="medium",
                mitigation="Run training in Phase 1",
            )
        ],
        go_no_go_recommendation="go",
        conditions=[],
        estimated_complexity="high",
        next_steps=["Define service boundaries", "Set up K8s cluster"],
    )


@pytest.fixture
def sample_roadmap():
    return Roadmap(
        project_title="Acme Corp Monolith Decomposition",
        client="Acme Corp",
        total_duration="6 months",
        milestones=[
            Milestone(
                name="Phase 1: Foundation",
                target_date="Month 2",
                stories=[
                    Story(
                        title="Set up Kubernetes cluster",
                        description="Provision K8s cluster on cloud provider",
                        acceptance_criteria=["Cluster is running", "kubectl access works"],
                        effort_estimate="large",
                        priority_score=90.0,
                        labels=["infrastructure"],
                    ),
                    Story(
                        title="Define service boundaries",
                        description="Map monolith domains to microservice boundaries",
                        acceptance_criteria=["Domain map documented", "Team alignment achieved"],
                        effort_estimate="medium",
                        priority_score=85.0,
                        labels=["architecture"],
                    ),
                ],
                success_criteria=["K8s cluster operational", "Service boundaries defined"],
            ),
            Milestone(
                name="Phase 2: Migration",
                target_date="Month 5",
                stories=[
                    Story(
                        title="Extract auth service",
                        description="Pull authentication into standalone microservice",
                        acceptance_criteria=["Auth service deployed", "Monolith uses new auth API"],
                        effort_estimate="xlarge",
                        priority_score=80.0,
                        labels=["migration"],
                    ),
                ],
                success_criteria=["Auth service live in production"],
            ),
        ],
        dependencies=["K8s cluster must be ready before migration"],
        assumptions=["Cloud provider account available", "Team allocated full-time"],
        out_of_scope=["Mobile app changes", "Database migration"],
    )


@pytest.fixture
def sample_test_cases():
    return [
        TestCase(
            id="TC-001",
            title="K8s cluster accessibility",
            description="Verify kubectl access to the new cluster",
            steps=["Run kubectl get nodes", "Verify node count"],
            expected_result="Nodes listed successfully",
            story_reference="Set up Kubernetes cluster",
        ),
    ]


@pytest.fixture
def sample_test_results():
    return [
        TestResult(
            test_case_id="TC-001",
            status=TestStatus.PASS,
            actual_result="3 nodes listed",
            notes="All healthy",
        ),
    ]


@pytest.fixture
def sample_validation_report(sample_test_cases, sample_test_results):
    return ValidationReport(
        milestone_name="Phase 1: Foundation",
        test_cases=sample_test_cases,
        test_results=sample_test_results,
        bugs_found=[],
        uat_feedback=[],
        pass_rate=1.0,
        ready_for_launch=True,
        blockers=[],
    )
