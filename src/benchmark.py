"""
性能基准测试
用于测试和比较系统性能
"""

import time
import statistics
from typing import Callable, List, Dict, Any, Optional
from dataclasses import dataclass, field
import logging


@dataclass
class BenchmarkResult:
    """基准测试结果"""

    name: str
    iterations: int = 0
    times: List[float] = field(default_factory=list)

    @property
    def min_time(self) -> float:
        """最小时间"""
        return min(self.times) if self.times else 0.0

    @property
    def max_time(self) -> float:
        """最大时间"""
        return max(self.times) if self.times else 0.0

    @property
    def mean_time(self) -> float:
        """平均时间"""
        return statistics.mean(self.times) if self.times else 0.0

    @property
    def median_time(self) -> float:
        """中位数时间"""
        return statistics.median(self.times) if self.times else 0.0

    @property
    def stdev_time(self) -> float:
        """标准差"""
        if len(self.times) < 2:
            return 0.0
        return statistics.stdev(self.times)

    @property
    def total_time(self) -> float:
        """总时间"""
        return sum(self.times)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "name": self.name,
            "iterations": self.iterations,
            "min_time": self.min_time,
            "max_time": self.max_time,
            "mean_time": self.mean_time,
            "median_time": self.median_time,
            "stdev_time": self.stdev_time,
            "total_time": self.total_time,
        }


class Benchmark:
    """基准测试"""

    def __init__(self, name: str = "Benchmark"):
        """初始化基准测试

        Args:
            name: 基准测试名称
        """
        self.name = name
        self.logger = logging.getLogger("ai-analyze.benchmark")
        self.results: Dict[str, BenchmarkResult] = {}

    def run(self, func: Callable, iterations: int = 10, name: Optional[str] = None, *args, **kwargs) -> BenchmarkResult:
        """运行基准测试

        Args:
            func: 要测试的函数
            iterations: 迭代次数
            name: 测试名称
            *args: 函数参数
            **kwargs: 函数关键字参数

        Returns:
            BenchmarkResult: 测试结果
        """
        test_name = name or func.__name__
        times = []

        self.logger.info(f"开始基准测试: {test_name} ({iterations} 次迭代)")

        for i in range(iterations):
            start = time.perf_counter()
            try:
                func(*args, **kwargs)
            except Exception as e:
                self.logger.error(f"测试失败: {e}")
                continue
            end = time.perf_counter()
            times.append(end - start)

        result = BenchmarkResult(name=test_name, iterations=len(times), times=times)
        self.results[test_name] = result

        self.logger.info(
            f"完成基准测试: {test_name} "
            f"(平均: {result.mean_time:.4f}s, "
            f"中位数: {result.median_time:.4f}s, "
            f"标准差: {result.stdev_time:.4f}s)"
        )

        return result

    def compare(self, name1: str, name2: str) -> Dict[str, Any]:
        """比较两个测试结果

        Args:
            name1: 第一个测试名称
            name2: 第二个测试名称

        Returns:
            比较结果
        """
        if name1 not in self.results or name2 not in self.results:
            raise ValueError("测试结果不存在")

        result1 = self.results[name1]
        result2 = self.results[name2]

        speedup = result1.mean_time / result2.mean_time
        improvement = (1 - result2.mean_time / result1.mean_time) * 100

        return {
            "name1": name1,
            "name2": name2,
            "time1": result1.mean_time,
            "time2": result2.mean_time,
            "speedup": speedup,
            "improvement": improvement,
        }

    def print_results(self):
        """打印测试结果"""
        if not self.results:
            print("没有测试结果")
            return

        print("\n" + "=" * 80)
        print(f"基准测试结果: {self.name}")
        print("=" * 80)

        for name, result in self.results.items():
            print(f"\n{name}:")
            print(f"  迭代次数: {result.iterations}")
            print(f"  最小时间: {result.min_time:.4f}s")
            print(f"  最大时间: {result.max_time:.4f}s")
            print(f"  平均时间: {result.mean_time:.4f}s")
            print(f"  中位数时间: {result.median_time:.4f}s")
            print(f"  标准差: {result.stdev_time:.4f}s")
            print(f"  总时间: {result.total_time:.4f}s")

        print("\n" + "=" * 80 + "\n")

    def print_comparison(self, name1: str, name2: str):
        """打印比较结果

        Args:
            name1: 第一个测试名称
            name2: 第二个测试名称
        """
        comparison = self.compare(name1, name2)

        print("\n" + "=" * 80)
        print("基准测试比较")
        print("=" * 80)
        print(f"\n{comparison['name1']} vs {comparison['name2']}:")
        print(f"  {comparison['name1']} 平均时间: {comparison['time1']:.4f}s")
        print(f"  {comparison['name2']} 平均时间: {comparison['time2']:.4f}s")
        print(f"  加速比: {comparison['speedup']:.2f}x")
        print(f"  性能改进: {comparison['improvement']:+.1f}%")
        print("\n" + "=" * 80 + "\n")


class PerformanceComparison:
    """性能对比"""

    def __init__(self):
        """初始化性能对比"""
        self.logger = logging.getLogger("ai-analyze.benchmark")
        self.benchmarks: Dict[str, Benchmark] = {}

    def add_benchmark(self, name: str, benchmark: Benchmark):
        """添加基准测试

        Args:
            name: 基准测试名称
            benchmark: 基准测试对象
        """
        self.benchmarks[name] = benchmark

    def compare_all(self) -> Dict[str, Dict[str, Any]]:
        """比较所有基准测试

        Returns:
            比较结果
        """
        comparisons = {}

        names = list(self.benchmarks.keys())
        for i in range(len(names)):
            for j in range(i + 1, len(names)):
                name1 = names[i]
                name2 = names[j]

                benchmark1 = self.benchmarks[name1]
                benchmark2 = self.benchmarks[name2]

                # 比较第一个测试
                if benchmark1.results and benchmark2.results:
                    test_name1 = list(benchmark1.results.keys())[0]
                    test_name2 = list(benchmark2.results.keys())[0]

                    result1 = benchmark1.results[test_name1]
                    result2 = benchmark2.results[test_name2]

                    speedup = result1.mean_time / result2.mean_time
                    improvement = (1 - result2.mean_time / result1.mean_time) * 100

                    comparisons[f"{name1} vs {name2}"] = {
                        "benchmark1": name1,
                        "benchmark2": name2,
                        "time1": result1.mean_time,
                        "time2": result2.mean_time,
                        "speedup": speedup,
                        "improvement": improvement,
                    }

        return comparisons

    def print_comparison(self):
        """打印对比结果"""
        comparisons = self.compare_all()

        if not comparisons:
            print("没有对比结果")
            return

        print("\n" + "=" * 80)
        print("性能对比结果")
        print("=" * 80)

        for name, comparison in comparisons.items():
            print(f"\n{name}:")
            print(f"  {comparison['benchmark1']} 平均时间: {comparison['time1']:.4f}s")
            print(f"  {comparison['benchmark2']} 平均时间: {comparison['time2']:.4f}s")
            print(f"  加速比: {comparison['speedup']:.2f}x")
            print(f"  性能改进: {comparison['improvement']:+.1f}%")

        print("\n" + "=" * 80 + "\n")


if __name__ == "__main__":
    # 测试基准测试
    print("测试基准测试:")

    def slow_function():
        time.sleep(0.1)

    def fast_function():
        time.sleep(0.05)

    benchmark = Benchmark("Performance Test")

    # 运行测试
    result1 = benchmark.run(slow_function, iterations=5, name="slow")
    result2 = benchmark.run(fast_function, iterations=5, name="fast")

    # 打印结果
    benchmark.print_results()

    # 比较结果
    benchmark.print_comparison("slow", "fast")
