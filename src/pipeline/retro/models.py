from pydantic import BaseModel


class EstimateAccuracy(BaseModel):
    story_title: str
    estimated_effort: str
    actual_effort: str
    accuracy_pct: float  # 100 = perfect, >100 = over, <100 = under


class Insight(BaseModel):
    category: str  # process, technical, communication, estimation
    observation: str
    recommendation: str
    priority: str  # high, medium, low


class RetroReport(BaseModel):
    project_title: str
    client: str
    duration_planned: str
    duration_actual: str
    estimate_accuracy: list[EstimateAccuracy]
    average_accuracy_pct: float
    what_went_well: list[str]
    what_could_improve: list[str]
    insights: list[Insight]
    updated_estimation_rules: list[str]  # learnings to feed back into Stage 3
