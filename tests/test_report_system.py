#!/usr/bin/env python3
"""Tests for report_system module"""

import os
import sys
import tempfile
from pathlib import Path

_project_root = str(Path(__file__).parent.parent)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from src.reports.report_system import (  # noqa: E402
    HTMLReportGenerator,
    HistoryManager,
    ReportComparator,
    ReportMetadata,
    TrendAnalysis,
    TrendDataPoint,
    ComparisonResult,
)


class TestReportMetadata:
    def test_auto_timestamp(self):
        meta = ReportMetadata(project_name="test", report_type="full")
        assert meta.timestamp != ""

    def test_custom_timestamp(self):
        meta = ReportMetadata(
            project_name="test", report_type="full", timestamp="2026-01-01"
        )
        assert meta.timestamp == "2026-01-01"

    def test_to_dict(self):
        meta = ReportMetadata(project_name="test", report_type="full")
        d = meta.to_dict()
        assert d["project_name"] == "test"
        assert d["report_type"] == "full"


class TestTrendAnalysis:
    def test_empty_trend(self):
        trend = TrendAnalysis(metric_name="score")
        assert trend.latest_value == 0.0
        assert trend.trend_direction == "stable"

    def test_improving_trend(self):
        trend = TrendAnalysis(
            metric_name="score",
            data_points=[
                TrendDataPoint("2026-01-01", 70.0),
                TrendDataPoint("2026-02-01", 80.0),
                TrendDataPoint("2026-03-01", 90.0),
            ],
        )
        assert trend.latest_value == 90.0
        assert trend.trend_direction == "improving"
        assert trend.change_rate > 0

    def test_declining_trend(self):
        trend = TrendAnalysis(
            metric_name="score",
            data_points=[
                TrendDataPoint("2026-01-01", 90.0),
                TrendDataPoint("2026-02-01", 80.0),
            ],
        )
        assert trend.trend_direction == "declining"

    def test_stable_trend(self):
        trend = TrendAnalysis(
            metric_name="score",
            data_points=[
                TrendDataPoint("2026-01-01", 80.0),
                TrendDataPoint("2026-02-01", 80.2),
            ],
        )
        assert trend.trend_direction == "stable"

    def test_change_rate_zero_base(self):
        trend = TrendAnalysis(
            metric_name="score",
            data_points=[
                TrendDataPoint("2026-01-01", 0.0),
                TrendDataPoint("2026-02-01", 10.0),
            ],
        )
        assert trend.change_rate == 0.0

    def test_to_dict(self):
        trend = TrendAnalysis(metric_name="score")
        d = trend.to_dict()
        assert "metric_name" in d
        assert "trend_direction" in d


class TestComparisonResult:
    def test_improved(self):
        result = ComparisonResult("score", 70.0, 85.0)
        assert result.absolute_change == 15.0
        assert result.relative_change > 0
        assert result.is_improved is True

    def test_declined(self):
        result = ComparisonResult("score", 85.0, 70.0)
        assert result.absolute_change == -15.0
        assert result.is_improved is False

    def test_zero_base(self):
        result = ComparisonResult("score", 0.0, 10.0)
        assert result.relative_change == 0.0

    def test_to_dict(self):
        result = ComparisonResult("score", 70.0, 85.0)
        d = result.to_dict()
        assert d["is_improved"] is True


class TestHistoryManager:
    def test_save_and_load(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = HistoryManager(history_dir=tmpdir)
            report = {"timestamp": "2026-01-01", "score": 85.0}
            path = manager.save_report("test_project", report)
            assert os.path.exists(path)

            loaded = manager.load_history("test_project")
            assert len(loaded) == 1
            assert loaded[0]["score"] == 85.0

    def test_load_empty(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = HistoryManager(history_dir=tmpdir)
            loaded = manager.load_history("nonexistent")
            assert loaded == []

    def test_analyze_trend(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = HistoryManager(history_dir=tmpdir)
            manager.save_report("proj_a", {"score": 70.0, "timestamp": "2026-01-01"})
            manager.save_report("proj_b", {"score": 80.0, "timestamp": "2026-02-01"})

            trend = manager.analyze_trend("proj_a", "score")
            assert len(trend.data_points) == 1
            assert trend.data_points[0].value == 70.0


class TestReportComparator:
    def test_compare_default_metrics(self):
        before = {"quality_scores": {"overall_score": 70}, "total_files": 10}
        after = {"quality_scores": {"overall_score": 85}, "total_files": 15}
        results = ReportComparator.compare(before, after)
        assert len(results) >= 2

    def test_compare_custom_metrics(self):
        before = {"a": {"b": 10}}
        after = {"a": {"b": 20}}
        results = ReportComparator.compare(
            before, after, metric_paths=["a.b"]
        )
        assert len(results) == 1
        assert results[0].is_improved is True

    def test_compare_missing_metric(self):
        before = {"a": 10}
        after = {"b": 20}
        results = ReportComparator.compare(
            before, after, metric_paths=["a"]
        )
        assert len(results) == 0


class TestHTMLReportGenerator:
    def test_generate(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            gen = HTMLReportGenerator(output_dir=tmpdir)
            data = {
                "timestamp": "2026-01-01",
                "quality_scores": {"overall_score": 85.0},
            }
            path = gen.generate(data, "test_project")
            assert os.path.exists(path)
            with open(path, "r") as f:
                html = f.read()
            assert "AI-Analyze Report" in html
            assert "85.0" in html

    def test_generate_with_security(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            gen = HTMLReportGenerator(output_dir=tmpdir)
            data = {
                "security_scan": {
                    "risk_score": 30.0,
                    "findings": [
                        {
                            "severity": "high",
                            "rule_name": "Test",
                            "file_path": "a.py",
                            "line_number": 1,
                            "description": "test finding",
                        }
                    ],
                }
            }
            path = gen.generate(data, "sec_test")
            with open(path, "r") as f:
                html = f.read()
            assert "Security Findings" in html
