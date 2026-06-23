"""Tests for unified_analyzer module - comprehensive"""

from datetime import datetime

from src.tools.unified_analyzer import UnifiedFileAnalysis, UnifiedProjectAnalysis, UnifiedAnalyzer


class TestUnifiedFileAnalysis:
    def test_creation(self):
        analysis = UnifiedFileAnalysis(file_path="test.py", language="python", total_lines=100)
        assert analysis.file_path == "test.py"
        assert analysis.language == "python"
        assert analysis.total_lines == 100
        assert analysis.code_smells == []
        assert analysis.overall_complexity is None

    def test_with_complexity(self):
        analysis = UnifiedFileAnalysis(
            file_path="test.py", language="python", total_lines=200, overall_complexity=15.5, code_smells=3
        )
        assert analysis.overall_complexity == 15.5
        assert analysis.code_smells == 3


class TestUnifiedProjectAnalysis:
    def test_creation(self):
        analysis = UnifiedProjectAnalysis(project_path="/tmp/test", generated_at=datetime.now().isoformat())
        assert analysis.project_path == "/tmp/test"
        assert len(analysis.files) == 0

    def test_add_file(self):
        project = UnifiedProjectAnalysis(project_path="/tmp/test", generated_at=datetime.now().isoformat())
        file_analysis = UnifiedFileAnalysis(file_path="a.py", language="python", total_lines=50)
        project.files.append(file_analysis)
        assert len(project.files) == 1

    def test_language_stats_default(self):
        project = UnifiedProjectAnalysis(project_path="/tmp/test", generated_at=datetime.now().isoformat())
        assert project.language_stats == {}


class TestUnifiedAnalyzer:
    def test_init(self):
        analyzer = UnifiedAnalyzer(project_path="/tmp/test")
        assert str(analyzer.project_path) == "/tmp/test"

    def test_build_ast_index(self):
        analyzer = UnifiedAnalyzer(project_path="/tmp/test")
        ast_report = {
            "files": [
                {"file_path": "a.py", "language": "python"},
                {"file_path": "b.js", "language": "javascript"},
            ]
        }
        index = analyzer._build_ast_index(ast_report)
        assert "a.py" in index
        assert "b.js" in index

    def test_build_ast_index_empty(self):
        analyzer = UnifiedAnalyzer(project_path="/tmp/test")
        index = analyzer._build_ast_index({})
        assert index == {}
