#!/usr/bin/env python3
"""Tests for performance_analyzer module"""

import sys
from pathlib import Path

_project_root = str(Path(__file__).parent.parent)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from src.analyzers.performance_analyzer import (  # noqa: E402
    PerformanceAnalyzer,
    PerformanceCategory,
    ImpactLevel,
    PerformanceIssue,
    PerformanceAnalysisResult,
    PerformancePattern,
)


class TestPerformanceAnalyzer:
    def setup_method(self):
        self.analyzer = PerformanceAnalyzer()

    def test_builtin_patterns_count(self):
        assert len(self.analyzer._patterns) >= 10

    def test_detect_time_sleep(self):
        code = "import time\ntime.sleep(5)\n"
        issues = self.analyzer.analyze_file("worker.py", code)
        assert any(i.id == "PERF006" for i in issues)

    def test_detect_global(self):
        code = "count = 0\ndef inc():\n    global count\n    count += 1\n"
        issues = self.analyzer.analyze_file("counter.py", code)
        assert any(i.id == "PERF005" for i in issues)

    def test_detect_large_range(self):
        code = "data = list(range(100000))\n"
        issues = self.analyzer.analyze_file("data.py", code)
        assert any(i.id == "PERF007" for i in issues)

    def test_clean_file(self):
        code = "def hello():\n    return 'world'\n"
        issues = self.analyzer.analyze_file("clean.py", code)
        assert len(issues) == 0

    def test_analyze_project(self):
        files = {
            "slow.py": "import time\ntime.sleep(1)\n",
            "clean.py": "x = 1\n",
        }
        result = self.analyzer.analyze_project(files)
        assert result.total_files_analyzed == 2
        assert len(result.issues) >= 1

    def test_performance_score_perfect(self):
        result = PerformanceAnalysisResult()
        assert result.performance_score == 100.0

    def test_performance_score_with_issues(self):
        issue = PerformanceIssue(
            id="PERF001",
            name="Test",
            category=PerformanceCategory.IO,
            impact=ImpactLevel.HIGH,
            file_path="test.py",
            line_number=1,
            line_content="test",
            description="test",
        )
        result = PerformanceAnalysisResult(issues=[issue])
        assert result.performance_score < 100
        assert result.high_count == 1

    def test_by_category(self):
        issue1 = PerformanceIssue(
            id="PERF006",
            name="Sleep",
            category=PerformanceCategory.CONCURRENCY,
            impact=ImpactLevel.MEDIUM,
            file_path="a.py",
            line_number=1,
            line_content="test",
            description="test",
        )
        result = PerformanceAnalysisResult(issues=[issue1])
        cats = result.by_category
        assert "concurrency" in cats

    def test_custom_pattern(self):
        custom = PerformancePattern(
            id="CUSTOM001",
            name="Custom Check",
            category=PerformanceCategory.ALGORITHM,
            impact=ImpactLevel.LOW,
            patterns=[r'bad_pattern_\d+'],
        )
        analyzer = PerformanceAnalyzer(custom_patterns=[custom])
        code = "bad_pattern_42\n"
        issues = analyzer.analyze_file("test.py", code)
        assert any(i.id == "CUSTOM001" for i in issues)

    def test_result_to_dict(self):
        result = PerformanceAnalysisResult()
        d = result.to_dict()
        assert "total_issues" in d
        assert "performance_score" in d
