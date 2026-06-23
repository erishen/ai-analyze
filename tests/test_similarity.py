"""Tests for similarity module - CodeBlock, SimilarityResult, SimilarityDetector"""


from src.analyzers.similarity import CodeBlock, SimilarityResult, SimilarityDetector


class TestCodeBlock:
    def test_line_count(self):
        block = CodeBlock(file_path="a.py", start_line=1, end_line=10, content="x=1")
        assert block.line_count == 10

    def test_hash(self):
        block = CodeBlock(file_path="a.py", start_line=1, end_line=1, content="hello")
        assert isinstance(block.hash, str)
        assert len(block.hash) == 64  # SHA-256 hex digest length

    def test_normalize(self):
        block = CodeBlock(
            file_path="a.py",
            start_line=1,
            end_line=3,
            content="x = 1\n# comment\ny = 2",
        )
        norm = block.normalize()
        assert "# comment" not in norm
        assert "x = 1" in norm

    def test_normalize_empty(self):
        block = CodeBlock(file_path="a.py", start_line=1, end_line=1, content="")
        norm = block.normalize()
        assert norm == ""


class TestSimilarityResult:
    def test_is_duplicate(self):
        b1 = CodeBlock(file_path="a.py", start_line=1, end_line=1, content="x")
        b2 = CodeBlock(file_path="b.py", start_line=1, end_line=1, content="x")
        result = SimilarityResult(block1=b1, block2=b2, similarity=0.98)
        assert result.is_duplicate is True

    def test_not_duplicate(self):
        b1 = CodeBlock(file_path="a.py", start_line=1, end_line=1, content="x")
        b2 = CodeBlock(file_path="b.py", start_line=1, end_line=1, content="y")
        result = SimilarityResult(block1=b1, block2=b2, similarity=0.5)
        assert result.is_duplicate is False


class TestSimilarityDetector:
    def test_add_and_detect(self):
        detector = SimilarityDetector()
        b1 = CodeBlock(file_path="a.py", start_line=1, end_line=5, content="def foo():\n    pass\n")
        b2 = CodeBlock(file_path="b.py", start_line=1, end_line=5, content="def foo():\n    pass\n")
        detector.add_code_block(b1)
        detector.add_code_block(b2)
        results = detector.detect_all()
        assert "duplicates" in results
        assert "similar" in results
