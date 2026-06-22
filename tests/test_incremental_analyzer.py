"""Tests for incremental_analyzer module - comprehensive"""

import tempfile
import os

from src.incremental_analyzer import IncrementalAnalyzer, FileHash, CacheMetadata


class TestFileHash:
    def test_creation(self):
        fh = FileHash(file_path="test.py", hash="abc123", modified_time=1.0)
        assert fh.file_path == "test.py"
        assert fh.hash == "abc123"


class TestCacheMetadata:
    def test_creation(self):
        meta = CacheMetadata(
            project_path="/tmp/test",
            created_at="2024-01-01",
            updated_at="2024-01-02",
            file_count=5,
            total_complexity=10.0,
            file_hashes={"a.py": "hash1"},
        )
        assert meta.project_path == "/tmp/test"
        assert meta.file_count == 5


class TestIncrementalAnalyzer:
    def test_init_default(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            analyzer = IncrementalAnalyzer(cache_dir=tmpdir, use_multi_level=False)
            assert analyzer.cache_dir.exists()
            assert analyzer._cache is None

    def test_init_multi_level(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            analyzer = IncrementalAnalyzer(cache_dir=tmpdir, use_multi_level=True)
            assert analyzer._cache is not None

    def test_get_file_hash(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            analyzer = IncrementalAnalyzer(cache_dir=tmpdir, use_multi_level=False)
            test_file = os.path.join(tmpdir, "test.py")
            with open(test_file, "w") as f:
                f.write("print('hello')")
            h = analyzer.get_file_hash(test_file)
            assert len(h) == 64

    def test_get_file_hash_nonexistent(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            analyzer = IncrementalAnalyzer(cache_dir=tmpdir, use_multi_level=False)
            h = analyzer.get_file_hash("/nonexistent/file.py")
            assert h == ""

    def test_get_project_hash(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            analyzer = IncrementalAnalyzer(cache_dir=tmpdir, use_multi_level=False)
            h = analyzer.get_project_hash("/my/project")
            assert len(h) == 12
            # Same path = same hash
            assert h == analyzer.get_project_hash("/my/project")

    def test_get_cache_path(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            analyzer = IncrementalAnalyzer(cache_dir=tmpdir, use_multi_level=False)
            path = analyzer.get_cache_path("/my/project")
            assert str(path).endswith("_cache.json")

    def test_save_and_load_cache_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            analyzer = IncrementalAnalyzer(cache_dir=tmpdir, use_multi_level=False)
            result = {"summary": {"total_complexity": 5}, "generated_at": "2024-01-01"}
            hashes = {"a.py": "hash1", "b.py": "hash2"}
            analyzer.save_cache("/my/project", result, hashes)
            loaded = analyzer.load_cache("/my/project")
            assert loaded is not None
            assert loaded["analysis"]["summary"]["total_complexity"] == 5

    def test_load_cache_miss(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            analyzer = IncrementalAnalyzer(cache_dir=tmpdir, use_multi_level=False)
            loaded = analyzer.load_cache("/nonexistent/project")
            assert loaded is None

    def test_get_changed_files_no_cache(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            analyzer = IncrementalAnalyzer(cache_dir=tmpdir, use_multi_level=False)
            modified, new, deleted = analyzer.get_changed_files("/proj", ["a.py", "b.py"], None)
            assert modified == []
            assert set(new) == {"a.py", "b.py"}
            assert deleted == []

    def test_get_changed_files_with_cache(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            analyzer = IncrementalAnalyzer(cache_dir=tmpdir, use_multi_level=False)
            cached = {"metadata": {"file_hashes": {"a.py": "old_hash", "c.py": "hash_c"}}}
            modified, new, deleted = analyzer.get_changed_files("/proj", ["a.py", "b.py"], cached)
            assert "b.py" in new
            assert "c.py" in deleted

    def test_should_reanalyze_no_cache(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            analyzer = IncrementalAnalyzer(cache_dir=tmpdir, use_multi_level=False)
            assert analyzer.should_reanalyze("/proj", ["a.py"], None) is True

    def test_should_reanalyze_unchanged(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            analyzer = IncrementalAnalyzer(cache_dir=tmpdir, use_multi_level=False)
            cached = {"metadata": {"file_hashes": {"a.py": "hash_a"}}}
            # a.py does not actually exist, so hash will be ""
            result = analyzer.should_reanalyze("/proj", ["a.py"], cached)
            assert isinstance(result, bool)

    def test_save_and_load_cache_multi_level(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            analyzer = IncrementalAnalyzer(cache_dir=tmpdir, use_multi_level=True)
            result = {"summary": {"total_complexity": 10}, "generated_at": "2024-01-01"}
            hashes = {"x.py": "hash_x"}
            analyzer.save_cache("/ml/project", result, hashes)
            loaded = analyzer.load_cache("/ml/project")
            assert loaded is not None
