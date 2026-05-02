#!/usr/bin/env python3
"""Tests for progress.py TaskCancellationToken and CancellableTask"""

import sys
from pathlib import Path

import pytest

_project_root = str(Path(__file__).parent.parent)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from src.progress import TaskCancellationToken, TaskCancelledError, CancellableTask  # noqa: E402


class TestTaskCancellationToken:
    def test_initial_state(self):
        token = TaskCancellationToken()
        assert token.is_cancelled is False
        assert token.reason == ""

    def test_cancel(self):
        token = TaskCancellationToken()
        token.cancel("user request")
        assert token.is_cancelled is True
        assert token.reason == "user request"

    def test_cancel_without_reason(self):
        token = TaskCancellationToken()
        token.cancel()
        assert token.is_cancelled is True
        assert token.reason == ""

    def test_check_raises_when_cancelled(self):
        token = TaskCancellationToken()
        token.cancel("timeout")
        with pytest.raises(TaskCancelledError) as exc_info:
            token.check()
        assert exc_info.value.reason == "timeout"

    def test_check_no_raise_when_not_cancelled(self):
        token = TaskCancellationToken()
        token.check()  # Should not raise

    def test_reset(self):
        token = TaskCancellationToken()
        token.cancel("test")
        token.reset()
        assert token.is_cancelled is False
        assert token.reason == ""


class TestTaskCancelledError:
    def test_with_reason(self):
        err = TaskCancelledError("timeout")
        assert err.reason == "timeout"
        assert "timeout" in str(err)

    def test_without_reason(self):
        err = TaskCancelledError()
        assert err.reason == ""
        assert "Task cancelled" in str(err)


class TestCancellableTask:
    def test_normal_execution(self):
        task = CancellableTask("test")
        result = task.run(lambda: 42)
        assert result == 42

    def test_cancel_before_run(self):
        task = CancellableTask("test")
        task.cancel("aborted")
        with pytest.raises(TaskCancelledError):
            task.run(lambda: 42)

    def test_cancel_during_run(self):
        task = CancellableTask("test")

        def func():
            task.cancel("mid-run")
            return 42

        with pytest.raises(TaskCancelledError):
            task.run(func)

    def test_check_cancelled(self):
        task = CancellableTask("test")
        task.cancel("test")
        with pytest.raises(TaskCancelledError):
            task.check_cancelled()
