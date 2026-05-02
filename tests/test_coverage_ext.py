#!/usr/bin/env python3
"""similarity + quality_score + ast_analyzer 新功能 扩展测试"""

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.similarity import (  # noqa: E402
    CodeBlock, SimilarityDetector, SimilarityResult,
)
from src.quality_score import (  # noqa: E402
    QualityScorer, QualityMetrics, QualityScore,
)
from src.ast_analyzer import (  # noqa: E402
    BatchASTAnalyzer, PythonASTAnalyzer, detect_language,
)


class TestCodeBlock(unittest.TestCase):
    def test_line_count(self):
        block = CodeBlock(file_path="t.py", start_line=1, end_line=10, content="line\n" * 10)
        self.assertEqual(block.line_count, 10)

    def test_hash_deterministic(self):
        b1 = CodeBlock(file_path="t.py", start_line=1, end_line=5, content="hello")
        b2 = CodeBlock(file_path="t.py", start_line=1, end_line=5, content="hello")
        self.assertEqual(b1.hash, b2.hash)

    def test_normalize_removes_comments(self):
        block = CodeBlock(file_path="t.py", start_line=1, end_line=2, content="# comment\nx = 1\n")
        self.assertNotIn("# comment", block.normalize())
        self.assertIn("x = 1", block.normalize())

    def test_normalize_removes_blank_lines(self):
        block = CodeBlock(file_path="t.py", start_line=1, end_line=3, content="x = 1\n\ny = 2\n")
        lines = [ln for ln in block.normalize().split("\n") if ln]
        self.assertEqual(len(lines), 2)


class TestSimilarityDetector(unittest.TestCase):
    def setUp(self):
        self.detector = SimilarityDetector()

    def test_add_code_block(self):
        block = CodeBlock(file_path="t.py", start_line=1, end_line=10, content="line\n" * 10)
        self.detector.add_code_block(block)
        self.assertEqual(len(self.detector.code_blocks), 1)

    def test_add_code_block_below_min_size(self):
        detector = SimilarityDetector(min_block_size=10)
        block = CodeBlock(file_path="t.py", start_line=1, end_line=3, content="x\ny\nz\n")
        detector.add_code_block(block)
        self.assertEqual(len(detector.code_blocks), 0)

    def test_detect_duplicates(self):
        code = "def hello():\n    print('hello')\n    return 42\n    x = 1\n    y = 2\n"
        b1 = CodeBlock(file_path="a.py", start_line=1, end_line=5, content=code)
        b2 = CodeBlock(file_path="b.py", start_line=1, end_line=5, content=code)
        self.detector.add_code_block(b1)
        self.detector.add_code_block(b2)
        results = self.detector.detect_duplicates()
        self.assertIsInstance(results, list)

    def test_detect_duplicates_no_duplicates(self):
        b1 = CodeBlock(file_path="a.py", start_line=1, end_line=5, content="x = 1\ny = 2\nz = 3\na = 4\nb = 5\n")
        b2 = CodeBlock(file_path="b.py", start_line=1, end_line=5, content="p = 1\nq = 2\nr = 3\ns = 4\nt = 5\n")
        self.detector.add_code_block(b1)
        self.detector.add_code_block(b2)
        results = self.detector.detect_duplicates()
        self.assertEqual(len(results), 0)

    def test_empty_detector(self):
        results = self.detector.detect_duplicates()
        self.assertEqual(len(results), 0)

    def test_similarity_result_properties(self):
        b1 = CodeBlock(file_path="a.py", start_line=1, end_line=5, content="test")
        b2 = CodeBlock(file_path="b.py", start_line=1, end_line=5, content="test")
        result = SimilarityResult(block1=b1, block2=b2, similarity=0.98)
        self.assertTrue(result.is_duplicate)
        self.assertTrue(result.is_similar)

    def test_similarity_result_similar_only(self):
        b1 = CodeBlock(file_path="a.py", start_line=1, end_line=5, content="test")
        b2 = CodeBlock(file_path="b.py", start_line=1, end_line=5, content="test")
        result = SimilarityResult(block1=b1, block2=b2, similarity=0.75)
        self.assertFalse(result.is_duplicate)
        self.assertTrue(result.is_similar)


class TestQualityScorer(unittest.TestCase):
    def setUp(self):
        self.scorer = QualityScorer()

    def test_simple_score(self):
        m = QualityMetrics(cyclomatic_complexity=3.0, lines_of_code=100)
        score = self.scorer.calculate_score(m)
        self.assertIsInstance(score, QualityScore)
        self.assertGreater(score.overall_score, 0)
        self.assertLessEqual(score.overall_score, 100)

    def test_high_complexity_lowers_score(self):
        m1 = QualityMetrics(cyclomatic_complexity=3.0, lines_of_code=100)
        m2 = QualityMetrics(cyclomatic_complexity=20.0, lines_of_code=500)
        s1 = self.scorer.calculate_score(m1)
        s2 = self.scorer.calculate_score(m2)
        self.assertGreater(s1.overall_score, s2.overall_score)

    def test_code_smells_lowers_score(self):
        m1 = QualityMetrics(code_smells=0)
        m2 = QualityMetrics(code_smells=10)
        s1 = self.scorer.calculate_score(m1)
        s2 = self.scorer.calculate_score(m2)
        self.assertGreater(s1.overall_score, s2.overall_score)

    def test_grade_assignment(self):
        m = QualityMetrics(cyclomatic_complexity=2.0, lines_of_code=50)
        score = self.scorer.calculate_score(m)
        self.assertIn(score.grade, ["A", "B", "C", "D", "F"])

    def test_recommendations(self):
        m = QualityMetrics(cyclomatic_complexity=15.0, code_smells=5)
        score = self.scorer.calculate_score(m)
        self.assertIsInstance(score.recommendations, list)

    def test_metrics_to_dict(self):
        m = QualityMetrics(cyclomatic_complexity=5.0, lines_of_code=100)
        d = m.to_dict()
        self.assertEqual(d["cyclomatic_complexity"], 5.0)


class TestDetectLanguage(unittest.TestCase):
    def test_python(self):
        self.assertEqual(detect_language("test.py").value, "python")

    def test_javascript(self):
        self.assertEqual(detect_language("test.js").value, "javascript")

    def test_typescript(self):
        self.assertEqual(detect_language("test.ts").value, "typescript")

    def test_unknown(self):
        self.assertIsNone(detect_language("test.rb"))


class TestBatchASTAnalyzer(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.project_dir = Path(self.temp_dir) / "project"
        self.project_dir.mkdir()
        for i in range(5):
            (self.project_dir / f"mod_{i}.py").write_text(
                f"def func_{i}(x):\n    return x + {i}\n", encoding="utf-8"
            )

    def test_sequential(self):
        analyzer = BatchASTAnalyzer()
        files = [str(f) for f in sorted(self.project_dir.glob("*.py"))]
        results = analyzer.analyze_files(files, parallel=False)
        self.assertEqual(len(results), 5)

    def test_parallel(self):
        analyzer = BatchASTAnalyzer()
        files = [str(f) for f in sorted(self.project_dir.glob("*.py"))]
        results = analyzer.analyze_files(files, parallel=True)
        self.assertEqual(len(results), 5)

    def test_single_file(self):
        analyzer = BatchASTAnalyzer()
        files = [str(sorted(self.project_dir.glob("*.py"))[0])]
        results = analyzer.analyze_files(files, parallel=True)
        self.assertEqual(len(results), 1)

    def test_empty_list(self):
        analyzer = BatchASTAnalyzer()
        self.assertEqual(analyzer.analyze_files([]), [])

    def test_nonexistent_file(self):
        analyzer = BatchASTAnalyzer()
        results = analyzer.analyze_files(["/nonexistent/file.py"])
        self.assertEqual(len(results), 0)

    def test_optimal_workers(self):
        self.assertGreaterEqual(BatchASTAnalyzer._optimal_workers(), 2)


class TestCognitiveComplexity(unittest.TestCase):
    def setUp(self):
        self.analyzer = PythonASTAnalyzer()

    def _analyze(self, code):
        import ast
        tree = ast.parse(code)
        return self.analyzer._compute_cognitive_complexity(tree)

    def test_simple_function(self):
        self.assertEqual(self._analyze("def f():\n    x = 1\n"), 0)

    def test_if_statement(self):
        self.assertGreater(self._analyze("def f(x):\n    if x:\n        pass\n"), 0)

    def test_nested_if(self):
        code = "def f(x, y):\n    if x:\n        if y:\n            pass\n"
        self.assertGreater(self._analyze(code), 2)

    def test_for_loop(self):
        self.assertGreater(self._analyze("def f(items):\n    for i in items:\n        pass\n"), 0)

    def test_bool_op(self):
        cc = self._analyze("def f(x, y):\n    if x and y:\n        pass\n")
        self.assertGreaterEqual(cc, 2)

    def test_except_handler(self):
        self.assertGreaterEqual(self._analyze("try:\n    pass\nexcept Exception:\n    pass\n"), 1)

    def test_analyze_file_uses_cognitive(self):
        tmpdir = tempfile.mkdtemp()
        code = ("def f(x):\n    if x > 0:\n"
                "        for i in range(x):\n"
                "            if i % 2:\n"
                "                pass\n    return x\n")
        path = Path(tmpdir) / "test.py"
        path.write_text(code, encoding="utf-8")
        result = self.analyzer.analyze_file(str(path))
        self.assertGreater(result.overall_complexity.cognitive_complexity, 0)


if __name__ == "__main__":
    unittest.main()
