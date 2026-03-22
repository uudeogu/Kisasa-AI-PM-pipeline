from __future__ import annotations

"""OpenTelemetry tracing for pipeline observability."""

import functools
import time
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import (
    BatchSpanProcessor,
    ConsoleSpanExporter,
)
from opentelemetry.sdk.resources import Resource

_initialized = False


def init_tracing(service_name: str = "kisasa-ai-pm-pipeline"):
    """Initialize OpenTelemetry tracing."""
    global _initialized
    if _initialized:
        return

    resource = Resource.create({"service.name": service_name})
    provider = TracerProvider(resource=resource)

    # Console exporter for development; swap for OTLP exporter in production
    processor = BatchSpanProcessor(ConsoleSpanExporter())
    provider.add_span_processor(processor)

    trace.set_tracer_provider(provider)
    _initialized = True


def get_tracer(name: str = "kisasa.pipeline"):
    """Get a tracer instance."""
    return trace.get_tracer(name)


def trace_stage(stage_name: str):
    """Decorator to trace a pipeline stage function."""
    def decorator(func):
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            tracer = get_tracer()
            with tracer.start_as_current_span(
                f"pipeline.{stage_name}",
                attributes={"pipeline.stage": stage_name},
            ) as span:
                start = time.time()
                try:
                    result = func(*args, **kwargs)
                    span.set_attribute("pipeline.status", "success")
                    return result
                except Exception as e:
                    span.set_attribute("pipeline.status", "error")
                    span.record_exception(e)
                    raise
                finally:
                    duration = time.time() - start
                    span.set_attribute("pipeline.duration_seconds", duration)

        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            tracer = get_tracer()
            with tracer.start_as_current_span(
                f"pipeline.{stage_name}",
                attributes={"pipeline.stage": stage_name},
            ) as span:
                start = time.time()
                try:
                    result = await func(*args, **kwargs)
                    span.set_attribute("pipeline.status", "success")
                    return result
                except Exception as e:
                    span.set_attribute("pipeline.status", "error")
                    span.record_exception(e)
                    raise
                finally:
                    duration = time.time() - start
                    span.set_attribute("pipeline.duration_seconds", duration)

        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    return decorator
