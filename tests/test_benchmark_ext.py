#!/usr/bin/env python3
"""benchmark.py 扩展测试 - 覆盖 PerformanceComparison、print 方法"""

import sys
import time
import unittest
from io import StringIO
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.benchmark import (  # noqa: E402
    Benchmark, BenchmarkResult, PerformanceComparison,
)


class TestBenchmarkResult(unittest.TestCase):
    """BenchmarkResult 数据类测试"""

    def test_empty_times(self):
        r = BenchmarkResult(name="test")
        self.assertEqual(r.min_time, 0.0)
        self.assertEqual(r.max_time, 0.0)
        self.assertEqual(r.mean_time, 0.0)
        self.assertEqual(r.median_time, 0.0)
        self.assertEqual(r.stdev_time, 0.0)
        self.assertEqual(r.total_time, 0.0)

    def test_single_time(self):
        r = BenchmarkResult(name="test", iterations=1, times=[0.5])
        self.assertEqual(r.min_time, 0.5)
        self.assertEqual(r.max_time, 0.5)
        self.assertEqual(r.mean_time, 0.5)

    def test_multiple_times(self):
        r = BenchmarkResult(name="test", iterations=3, times=[0.1, 0.2, 0.3])
        self.assertAlmostEqual(r.min_time, 0.1)
        self.assertAlmostEqual(r.max_time, 0.3)
        self.assertAlmostEqual(r.mean_time, 0.2)
        self.assertGreater(r.stdev_time, 0)

    def test_to_dict(self):
        r = BenchmarkResult(name="test", iterations=2, times=[0.1, 0.2])
        d = r.to_dict()
        self.assertEqual(d["name"], "test")
        self.assertEqual(d["iterations"], 2)


class TestBenchmarkPrintMethods(unittest.TestCase):
    """Benchmark 打印方法测试"""

    def test_print_results(self):
        bm = Benchmark("Test")
        bm.run(lambda: time.sleep(0.001), iterations=2, name="fast")
        captured = StringIO()
        with patch("sys.stdout", captured):
            bm.print_results()
        output = captured.getvalue()
        self.assertIn("Test", output)
        self.assertIn("fast", output)

    def test_print_results_empty(self):
        bm = Benchmark("Empty")
        captured = StringIO()
        with patch("sys.stdout", captured):
            bm.print_results()
        output = captured.getvalue()
        self.assertIn("没有测试结果", output)

    def test_print_comparison(self):
        bm = Benchmark("Compare")
        bm.run(lambda: time.sleep(0.01), iterations=2, name="slow")
        bm.run(lambda: time.sleep(0.001), iterations=2, name="fast")
        captured = StringIO()
        with patch("sys.stdout", captured):
            bm.print_comparison("slow", "fast")
        output = captured.getvalue()
        self.assertIn("基准测试比较", output)

    def test_compare_missing_results(self):
        bm = Benchmark("Test")
        with self.assertRaises(ValueError):
            bm.compare("nonexistent1", "nonexistent2")


class TestBenchmarkRunWithException(unittest.TestCase):
    def test_run_with_exception(self):
        bm = Benchmark("Exception Test")
        call_count = 0

        def failing_func():
            nonlocal call_count
            call_count += 1
            if call_count <= 2:
                raise RuntimeError("test error")
        result = bm.run(failing_func, iterations=5, name="failing")
        self.assertLessEqual(result.iterations, 5)


class TestPerformanceComparison(unittest.TestCase):
    """PerformanceComparison 测试"""

    def test_add_benchmark(self):
        pc = PerformanceComparison()
        bm1 = Benchmark("B1")
        bm1.run(lambda: time.sleep(0.001), iterations=2, name="t1")
        pc.add_benchmark("bm1", bm1)
        self.assertIn("bm1", pc.benchmarks)

    def test_compare_all(self):
        pc = PerformanceComparison()
        bm1 = Benchmark("B1")
        bm1.run(lambda: time.sleep(0.01), iterations=2, name="slow")
        pc.add_benchmark("slow_bm", bm1)
        bm2 = Benchmark("B2")
        bm2.run(lambda: time.sleep(0.001), iterations=2, name="fast")
        pc.add_benchmark("fast_bm", bm2)
        comparisons = pc.compare_all()
        self.assertIn("slow_bm vs fast_bm", comparisons)
        self.assertGreater(comparisons["slow_bm vs fast_bm"]["speedup"], 0)

    def test_compare_all_empty(self):
        pc = PerformanceComparison()
        self.assertEqual(pc.compare_all(), {})

    def test_compare_all_single_benchmark(self):
        pc = PerformanceComparison()
        bm = Benchmark("Only")
        bm.run(lambda: None, iterations=2, name="t")
        pc.add_benchmark("only", bm)
        self.assertEqual(pc.compare_all(), {})

    def test_print_comparison(self):
        pc = PerformanceComparison()
        bm1 = Benchmark("B1")
        bm1.run(lambda: time.sleep(0.01), iterations=2, name="t1")
        pc.add_benchmark("bm1", bm1)
        bm2 = Benchmark("B2")
        bm2.run(lambda: time.sleep(0.001), iterations=2, name="t2")
        pc.add_benchmark("bm2", bm2)
        captured = StringIO()
        with patch("sys.stdout", captured):
            pc.print_comparison()
        self.assertIn("性能对比结果", captured.getvalue())

    def test_print_comparison_empty(self):
        pc = PerformanceComparison()
        captured = StringIO()
        with patch("sys.stdout", captured):
            pc.print_comparison()
        self.assertIn("没有对比结果", captured.getvalue())


if __name__ == "__main__":
    unittest.main()
