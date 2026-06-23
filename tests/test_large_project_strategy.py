#!/usr/bin/env python3
"""Tests for memory.py LargeProjectStrategy"""

import sys
from pathlib import Path

_project_root = str(Path(__file__).parent.parent)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from src.infrastructure.memory import LargeProjectStrategy  # noqa: E402


class TestLargeProjectStrategy:
    def test_small_project(self):
        strategy = LargeProjectStrategy(total_files=500)
        assert strategy.strategy == "full"
        assert strategy.is_large_project is False
        assert strategy.should_sample is False
        assert strategy.sample_rate == 1.0

    def test_medium_project(self):
        strategy = LargeProjectStrategy(total_files=2000)
        assert strategy.strategy == "batched"
        assert strategy.is_large_project is False
        assert strategy.should_sample is False

    def test_large_project(self):
        strategy = LargeProjectStrategy(total_files=8000)
        assert strategy.strategy == "streaming"
        assert strategy.is_large_project is True
        assert strategy.should_sample is True
        assert strategy.sample_rate == 0.2

    def test_very_large_project(self):
        strategy = LargeProjectStrategy(total_files=30000)
        assert strategy.strategy == "streaming"
        assert strategy.sample_rate == 0.05

    def test_batch_size_full(self):
        strategy = LargeProjectStrategy(total_files=500)
        assert strategy.recommended_batch_size == 500

    def test_batch_size_batched(self):
        strategy = LargeProjectStrategy(total_files=2000, batch_size=200)
        assert strategy.recommended_batch_size == 200

    def test_batch_size_streaming(self):
        strategy = LargeProjectStrategy(total_files=8000, batch_size=100)
        assert strategy.recommended_batch_size == 20

    def test_total_batches(self):
        strategy = LargeProjectStrategy(total_files=2000, batch_size=200)
        assert strategy.total_batches == 10

    def test_get_file_batches(self):
        strategy = LargeProjectStrategy(total_files=2000, batch_size=3)
        files = [f"file{i}.py" for i in range(10)]
        batches = strategy.get_file_batches(files)
        assert len(batches) == 4  # 3+3+3+1
        assert len(batches[0]) == 3

    def test_get_sampled_files_no_sample(self):
        strategy = LargeProjectStrategy(total_files=500)
        files = ["a.py", "b.py", "c.py"]
        result = strategy.get_sampled_files(files)
        assert result == files

    def test_get_sampled_files_with_sample(self):
        strategy = LargeProjectStrategy(total_files=8000)
        files = [f"file{i}.py" for i in range(100)]
        result = strategy.get_sampled_files(files)
        assert len(result) == 20  # 20% of 100

    def test_should_gc_after_batch(self):
        strategy = LargeProjectStrategy(total_files=2000)
        assert strategy.should_gc_after_batch(4) is True  # (4+1) % 5 == 0
        assert strategy.should_gc_after_batch(0) is False
        strategy_full = LargeProjectStrategy(total_files=500)
        assert strategy_full.should_gc_after_batch(4) is False

    def test_to_dict(self):
        strategy = LargeProjectStrategy(total_files=2000)
        d = strategy.to_dict()
        assert d["strategy"] == "batched"
        assert d["total_files"] == 2000
