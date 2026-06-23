"""Tests for benchmark module - BenchmarkResult and BenchmarkRunner"""

import pytest

from src.infrastructure.benchmark import BenchmarkResult, Benchmark


class TestBenchmarkResult:
    def test_empty_times(self):
        r = BenchmarkResult(name="test")
        assert r.min_time == 0.0
        assert r.max_time == 0.0
        assert r.mean_time == 0.0
        assert r.median_time == 0.0
        assert r.stdev_time == 0.0
        assert r.total_time == 0.0

    def test_with_times(self):
        r = BenchmarkResult(name="test", iterations=3, times=[0.1, 0.2, 0.3])
        assert r.min_time == 0.1
        assert r.max_time == 0.3
        assert abs(r.mean_time - 0.2) < 0.001
        assert r.total_time == pytest.approx(0.6)

    def test_stdev_single_value(self):
        r = BenchmarkResult(name="test", times=[0.1])
        assert r.stdev_time == 0.0

    def test_to_dict(self):
        r = BenchmarkResult(name="test", iterations=2, times=[0.1, 0.2])
        d = r.to_dict()
        assert d["name"] == "test"
        assert d["iterations"] == 2


class TestBenchmark:
    def test_run_benchmark(self):
        runner = Benchmark()

        def sample_func():
            return sum(range(100))

        result = runner.run(sample_func, name="sum_test", iterations=5)
        assert isinstance(result, BenchmarkResult)
        assert result.name == "sum_test"
        assert result.iterations == 5
        assert len(result.times) == 5

    def test_compare(self):
        runner = Benchmark()

        def fast():
            return 1

        def slow():
            return sum(range(1000))

        r1 = runner.run(fast, name="fast", iterations=3)
        r2 = runner.run(slow, name="slow", iterations=3)
        assert r1.mean_time <= r2.mean_time
