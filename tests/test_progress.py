"""Tests for progress module - ProgressMetrics, ProgressBar, PerformanceMonitor"""

import time


from src.infrastructure.progress import ProgressMetrics, ProgressBar, PerformanceMonitor


class TestProgressMetrics:
    def test_default_values(self):
        m = ProgressMetrics()
        assert m.total == 0
        assert m.current == 0
        assert m.start_time == 0.0

    def test_percentage_zero_total(self):
        m = ProgressMetrics(total=0, current=0)
        assert m.percentage == 0.0

    def test_percentage(self):
        m = ProgressMetrics(total=100, current=50)
        assert m.percentage == 50.0

    def test_eta_zero_current(self):
        m = ProgressMetrics(total=100, current=0)
        assert m.eta == 0.0


class TestProgressBar:
    def test_init(self):
        bar = ProgressBar(total=100, title="test")
        assert bar.metrics.total == 100
        assert bar.title == "test"

    def test_update(self):
        bar = ProgressBar(total=100)
        bar.update(10)
        assert bar.metrics.current == 10


class TestPerformanceMonitor:
    def test_init(self):
        monitor = PerformanceMonitor(name="test")
        assert monitor.name == "test"

    def test_start_stop(self):
        monitor = PerformanceMonitor(name="test")
        monitor.start()
        time.sleep(0.05)
        elapsed = monitor.stop()
        assert elapsed >= 0.04

    def test_add_metric(self):
        monitor = PerformanceMonitor(name="test")
        monitor.add_metric("files", 10)
        monitor.add_metric("errors", 0)

    def test_get_metrics(self):
        monitor = PerformanceMonitor(name="test")
        monitor.start()
        monitor.add_metric("files", 10)
        time.sleep(0.01)
        monitor.stop()
        metrics = monitor.get_metrics()
        assert metrics["name"] == "test"
        assert "elapsed" in metrics
