from pydantic import BaseModel
from enum import Enum


class TestStatus(str, Enum):
    PASS = "pass"
    FAIL = "fail"
    SKIP = "skip"


class TestCase(BaseModel):
    id: str
    title: str
    description: str
    steps: list[str]
    expected_result: str
    story_reference: str  # which story this validates


class TestResult(BaseModel):
    test_case_id: str
    status: TestStatus
    actual_result: str
    notes: str


class BugTicket(BaseModel):
    title: str
    description: str
    severity: str  # critical, high, medium, low
    steps_to_reproduce: list[str]
    expected_behavior: str
    actual_behavior: str
    story_reference: str


class UATFeedback(BaseModel):
    source: str  # who gave the feedback
    sentiment: str  # positive, neutral, negative
    summary: str
    action_items: list[str]
    linked_stories: list[str]


class ValidationReport(BaseModel):
    milestone_name: str
    test_cases: list[TestCase]
    test_results: list[TestResult]
    bugs_found: list[BugTicket]
    uat_feedback: list[UATFeedback]
    pass_rate: float
    ready_for_launch: bool
    blockers: list[str]
