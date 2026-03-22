"""Tests for observability (tracing and metrics)."""

import pytest
from unittest.mock import patch, MagicMock

from src.observability.tracing import trace_stage, get_tracer
from src.observability.metrics import create_pipeline_metrics, get_meter


class TestTraceStage:
    def test_sync_function_tracing(self):
        """Test that trace_stage works on sync functions."""
        @trace_stage("test_stage")
        def my_func(x):
            return x * 2

        result = my_func(5)
        assert result == 10

    def test_sync_function_preserves_exception(self):
        """Test that trace_stage re-raises exceptions."""
        @trace_stage("error_stage")
        def failing_func():
            raise ValueError("test error")

        with pytest.raises(ValueError, match="test error"):
            failing_func()

    @pytest.mark.asyncio
    async def test_async_function_tracing(self):
        """Test that trace_stage works on async functions."""
        @trace_stage("async_stage")
        async def my_async_func(x):
            return x + 1

        result = await my_async_func(10)
        assert result == 11

    @pytest.mark.asyncio
    async def test_async_function_preserves_exception(self):
        """Test that trace_stage re-raises exceptions from async functions."""
        @trace_stage("async_error_stage")
        async def failing_async():
            raise RuntimeError("async error")

        with pytest.raises(RuntimeError, match="async error"):
            await failing_async()

    def test_decorated_function_name_preserved(self):
        """Test that functools.wraps preserves the function name."""
        @trace_stage("named_stage")
        def original_name():
            pass

        assert original_name.__name__ == "original_name"


class TestMetrics:
    def test_get_meter(self):
        meter = get_meter()
        assert meter is not None

    def test_create_pipeline_metrics(self):
        metrics = create_pipeline_metrics()
        assert "projects_created" in metrics
        assert "stage_duration" in metrics
        assert "stage_errors" in metrics
        assert "ai_calls" in metrics
        assert "no_go_decisions" in metrics
        assert "active_projects" in metrics
