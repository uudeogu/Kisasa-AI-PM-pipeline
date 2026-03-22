from __future__ import annotations

"""OpenTelemetry metrics for pipeline monitoring."""

from opentelemetry import metrics
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import (
    ConsoleMetricExporter,
    PeriodicExportingMetricReader,
)
from opentelemetry.sdk.resources import Resource

_initialized = False
_meter = None


def init_metrics(service_name: str = "kisasa-ai-pm-pipeline"):
    """Initialize OpenTelemetry metrics."""
    global _initialized, _meter
    if _initialized:
        return

    resource = Resource.create({"service.name": service_name})
    reader = PeriodicExportingMetricReader(ConsoleMetricExporter())
    provider = MeterProvider(resource=resource, metric_readers=[reader])

    metrics.set_meter_provider(provider)
    _meter = metrics.get_meter("kisasa.pipeline")
    _initialized = True


def get_meter():
    """Get the pipeline meter instance."""
    global _meter
    if _meter is None:
        _meter = metrics.get_meter("kisasa.pipeline")
    return _meter


# Pipeline metrics
def create_pipeline_metrics():
    """Create standard pipeline metrics."""
    meter = get_meter()

    return {
        "projects_created": meter.create_counter(
            "pipeline.projects.created",
            description="Number of projects created",
        ),
        "stage_duration": meter.create_histogram(
            "pipeline.stage.duration",
            description="Duration of each pipeline stage in seconds",
            unit="s",
        ),
        "stage_errors": meter.create_counter(
            "pipeline.stage.errors",
            description="Number of stage execution errors",
        ),
        "ai_calls": meter.create_counter(
            "pipeline.ai.calls",
            description="Number of Claude API calls made",
        ),
        "no_go_decisions": meter.create_counter(
            "pipeline.decisions.no_go",
            description="Number of no-go recommendations",
        ),
        "active_projects": meter.create_up_down_counter(
            "pipeline.projects.active",
            description="Number of currently active projects",
        ),
    }
