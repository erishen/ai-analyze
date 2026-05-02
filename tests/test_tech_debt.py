#!/usr/bin/env python3
"""Tests for tech_debt module"""

import sys
from pathlib import Path

_project_root = str(Path(__file__).parent.parent)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from src.tech_debt import TechDebtAnalyzer, DebtItem, TechDebtResult  # noqa: E402


class TestTechDebtAnalyzer:
    def setup_method(self):
        self.analyzer = TechDebtAnalyzer()

    def test_detect_todo(self):
        code = "# TODO: fix this later\n# FIXME: broken\n"
        items = self.analyzer.analyze_file("todo.py", code)
        assert len(items) >= 2
        assert any(i.name == "Unresolved TODO" for i in items)

    def test_detect_bare_except(self):
        code = "try:\n    x = 1\nexcept:\n    pass\n"
        items = self.analyzer.analyze_file("bad.py", code)
        assert any(i.name == "Bare Except" for i in items)

    def test_detect_large_file(self):
        code = "\n".join(["x = 1"] * 600)
        items = self.analyzer.analyze_file("big.py", code)
        assert any(i.name == "Large File" for i in items)

    def test_clean_file(self):
        code = "def hello():\n    return 'world'\n"
        items = self.analyzer.analyze_file("clean.py", code)
        assert len(items) == 0

    def test_analyze_project(self):
        files = {
            "todo.py": "# TODO: implement\n",
            "clean.py": "x = 1\n",
        }
        result = self.analyzer.analyze_project(files)
        assert result.total_files == 2
        assert len(result.items) >= 1

    def test_debt_score_empty(self):
        result = TechDebtResult()
        assert result.debt_score == 0.0

    def test_debt_score_with_items(self):
        items = [
            DebtItem("todo", "TODO", "a.py", 1, "test", 2.0, "low"),
            DebtItem("error", "Bare Except", "b.py", 5, "test", 1.0, "high"),
        ]
        result = TechDebtResult(items=items, total_lines_of_code=100)
        assert result.debt_score > 0
        assert result.total_effort_hours == 3.0

    def test_category_summaries(self):
        items = [
            DebtItem("todo", "TODO", "a.py", 1, "test", 2.0, "low"),
            DebtItem("todo", "FIXME", "b.py", 2, "test", 1.0, "low"),
            DebtItem("error", "Bare", "c.py", 3, "test", 3.0, "high"),
        ]
        result = TechDebtResult(items=items, total_lines_of_code=100)
        summaries = result.category_summaries
        assert len(summaries) == 2
        assert summaries[0].category in ("todo", "error")

    def test_top_debt_items(self):
        items = [
            DebtItem("a", "A", "a.py", 1, "test", 1.0, "low"),
            DebtItem("b", "B", "b.py", 1, "test", 5.0, "high"),
            DebtItem("c", "C", "c.py", 1, "test", 3.0, "medium"),
        ]
        result = TechDebtResult(items=items, total_lines_of_code=100)
        top = result.top_debt_items
        assert top[0].effort_hours == 5.0

    def test_complexity_debt(self):
        code = "def simple():\n    pass\n"
        items = self.analyzer.analyze_file(
            "complex.py", code, {"cyclomatic_complexity": 25}
        )
        assert any(i.name == "High Cyclomatic Complexity" for i in items)

    def test_result_to_dict(self):
        result = TechDebtResult()
        d = result.to_dict()
        assert "debt_score" in d
        assert "total_items" in d
