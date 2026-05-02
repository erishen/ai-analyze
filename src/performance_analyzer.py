#!/usr/bin/env python3
"""
性能瓶颈识别模块
基于 AST 和模式匹配分析潜在性能问题
"""

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class PerformanceCategory(Enum):
    """性能问题类别"""

    ALGORITHM = "algorithm"
    MEMORY = "memory"
    IO = "io"
    CONCURRENCY = "concurrency"
    DATABASE = "database"
    NETWORK = "network"
    CACHING = "caching"
    LOOP = "loop"


class ImpactLevel(Enum):
    """影响程度"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

    @property
    def weight(self) -> float:
        weights = {
            ImpactLevel.LOW: 0.25,
            ImpactLevel.MEDIUM: 0.5,
            ImpactLevel.HIGH: 0.75,
            ImpactLevel.CRITICAL: 1.0,
        }
        return weights[self]


@dataclass
class PerformanceIssue:
    """性能问题"""

    id: str
    name: str
    category: PerformanceCategory
    impact: ImpactLevel
    file_path: str
    line_number: int
    line_content: str
    description: str
    suggestion: str = ""
    estimated_improvement: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "category": self.category.value,
            "impact": self.impact.value,
            "file_path": self.file_path,
            "line_number": self.line_number,
            "line_content": self.line_content,
            "description": self.description,
            "suggestion": self.suggestion,
            "estimated_improvement": self.estimated_improvement,
        }


@dataclass
class PerformanceAnalysisResult:
    """性能分析结果"""

    issues: List[PerformanceIssue] = field(default_factory=list)
    total_files_analyzed: int = 0
    analysis_duration: float = 0.0

    @property
    def critical_count(self) -> int:
        return sum(1 for i in self.issues if i.impact == ImpactLevel.CRITICAL)

    @property
    def high_count(self) -> int:
        return sum(1 for i in self.issues if i.impact == ImpactLevel.HIGH)

    @property
    def performance_score(self) -> float:
        """性能评分 (0-100, 100 为最佳)"""
        if not self.issues:
            return 100.0
        weighted_sum = sum(i.impact.weight for i in self.issues)
        penalty = min(100, (weighted_sum / 8.0) * 100)
        return round(max(0, 100 - penalty), 1)

    @property
    def by_category(self) -> Dict[str, int]:
        """按类别统计"""
        counts: Dict[str, int] = {}
        for issue in self.issues:
            key = issue.category.value
            counts[key] = counts.get(key, 0) + 1
        return counts

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_issues": len(self.issues),
            "critical_count": self.critical_count,
            "high_count": self.high_count,
            "performance_score": self.performance_score,
            "by_category": self.by_category,
            "total_files_analyzed": self.total_files_analyzed,
            "analysis_duration": round(self.analysis_duration, 3),
            "issues": [i.to_dict() for i in self.issues],
        }


@dataclass
class PerformancePattern:
    """性能检测模式"""

    id: str
    name: str
    category: PerformanceCategory
    impact: ImpactLevel
    patterns: List[str]
    languages: List[str] = field(default_factory=lambda: ["all"])
    description: str = ""
    suggestion: str = ""
    estimated_improvement: str = ""
    enabled: bool = True


class PerformanceAnalyzer:
    """性能瓶颈分析器"""

    def __init__(
        self,
        custom_patterns: Optional[List[PerformancePattern]] = None,
    ):
        self.logger = logging.getLogger("ai-analyze.performance_analyzer")
        self._patterns: List[PerformancePattern] = self._builtin_patterns()
        if custom_patterns:
            self._patterns.extend(custom_patterns)

    @property
    def patterns(self) -> List[PerformancePattern]:
        return [p for p in self._patterns if p.enabled]

    def analyze_file(
        self, file_path: str, content: str
    ) -> List[PerformanceIssue]:
        """分析单个文件"""
        issues: List[PerformanceIssue] = []
        lines = content.split("\n")

        for pattern in self.patterns:
            if not self._matches_language(file_path, pattern.languages):
                continue

            for regex_str in pattern.patterns:
                try:
                    compiled = re.compile(regex_str)
                except re.error:
                    self.logger.warning(
                        "Invalid regex in pattern %s: %s", pattern.id, regex_str
                    )
                    continue

                for line_num, line in enumerate(lines, 1):
                    if compiled.search(line):
                        issues.append(
                            PerformanceIssue(
                                id=pattern.id,
                                name=pattern.name,
                                category=pattern.category,
                                impact=pattern.impact,
                                file_path=file_path,
                                line_number=line_num,
                                line_content=line.strip(),
                                description=pattern.description,
                                suggestion=pattern.suggestion,
                                estimated_improvement=pattern.estimated_improvement,
                            )
                        )

        return issues

    def analyze_project(
        self, files: Dict[str, str], max_issues: int = 300
    ) -> PerformanceAnalysisResult:
        """分析项目"""
        import time

        start = time.time()
        all_issues: List[PerformanceIssue] = []

        for file_path, content in files.items():
            if len(all_issues) >= max_issues:
                break
            issues = self.analyze_file(file_path, content)
            all_issues.extend(issues)

        impact_order = {
            ImpactLevel.CRITICAL: 0,
            ImpactLevel.HIGH: 1,
            ImpactLevel.MEDIUM: 2,
            ImpactLevel.LOW: 3,
        }
        all_issues.sort(key=lambda i: impact_order.get(i.impact, 99))

        duration = time.time() - start
        return PerformanceAnalysisResult(
            issues=all_issues[:max_issues],
            total_files_analyzed=len(files),
            analysis_duration=duration,
        )

    def _matches_language(self, file_path: str, languages: List[str]) -> bool:
        """检查文件是否匹配语言"""
        import os

        if "all" in languages:
            return True
        ext = os.path.splitext(file_path)[1].lstrip(".")
        return ext in languages

    def _builtin_patterns(self) -> List[PerformancePattern]:
        """内置性能检测模式"""
        return [
            # 循环内 I/O
            PerformancePattern(
                id="PERF001",
                name="I/O Inside Loop",
                category=PerformanceCategory.IO,
                impact=ImpactLevel.HIGH,
                patterns=[
                    r'for\s+.*:\s*\n.*open\s*\(',
                    r'for\s+.*:\s*\n.*\.read\s*\(',
                    r'for\s+.*:\s*\n.*\.write\s*\(',
                    r'for\s+.*:\s*\n.*requests\.',
                    r'for\s+.*:\s*\n.*urllib',
                ],
                languages=["py"],
                description="I/O operations inside loop can be batched",
                suggestion="Batch I/O operations outside loops",
                estimated_improvement="50-90%",
            ),
            # 列表推导 vs 循环 append
            PerformancePattern(
                id="PERF002",
                name="Append in Loop",
                category=PerformanceCategory.ALGORITHM,
                impact=ImpactLevel.LOW,
                patterns=[
                    r'\.append\s*\([^)]*\)\s*$',
                ],
                languages=["py"],
                description="List comprehension is faster than append in loop",
                suggestion="Use list comprehension when possible",
                estimated_improvement="10-30%",
            ),
            # 字符串拼接
            PerformancePattern(
                id="PERF003",
                name="String Concatenation in Loop",
                category=PerformanceCategory.ALGORITHM,
                impact=ImpactLevel.MEDIUM,
                patterns=[
                    r'\w+\s*\+=\s*["\']',
                ],
                languages=["py", "js", "ts"],
                description="String concatenation in loop is inefficient",
                suggestion="Use join() for multiple string concatenations",
                estimated_improvement="30-60%",
            ),
            # 同步数据库查询
            PerformancePattern(
                id="PERF004",
                name="Synchronous DB Query in Loop",
                category=PerformanceCategory.DATABASE,
                impact=ImpactLevel.CRITICAL,
                patterns=[
                    r'for\s+.*:\s*\n.*\.(execute|query|find|filter)\s*\(',
                    r'while\s+.*:\s*\n.*\.(execute|query|find|filter)\s*\(',
                ],
                languages=["py"],
                description="Database query inside loop causes N+1 problem",
                suggestion="Use bulk queries or prefetch related data",
                estimated_improvement="80-99%",
            ),
            # 全局变量在循环内
            PerformancePattern(
                id="PERF005",
                name="Global Lookup in Loop",
                category=PerformanceCategory.ALGORITHM,
                impact=ImpactLevel.LOW,
                patterns=[
                    r'global\s+\w+',
                ],
                languages=["py"],
                description="Global variable lookups are slower than local",
                suggestion="Cache global as local variable before loop",
                estimated_improvement="5-15%",
            ),
            # time.sleep
            PerformancePattern(
                id="PERF006",
                name="Blocking Sleep",
                category=PerformanceCategory.CONCURRENCY,
                impact=ImpactLevel.MEDIUM,
                patterns=[
                    r'time\.sleep\s*\(',
                ],
                languages=["py"],
                description="Blocking sleep wastes thread time",
                suggestion="Use asyncio.sleep() in async code",
                estimated_improvement="20-50%",
            ),
            # 大列表创建
            PerformancePattern(
                id="PERF007",
                name="Large List Creation",
                category=PerformanceCategory.MEMORY,
                impact=ImpactLevel.MEDIUM,
                patterns=[
                    r'range\s*\(\s*\d{5,}',
                    r'\[.*for.*in\s+range\s*\(\s*\d{5,}',
                ],
                languages=["py"],
                description="Creating large lists consumes memory",
                suggestion="Use generators instead of lists for large sequences",
                estimated_improvement="50-90% memory",
            ),
            # 未使用缓存
            PerformancePattern(
                id="PERF008",
                name="Repeated Computation",
                category=PerformanceCategory.CACHING,
                impact=ImpactLevel.MEDIUM,
                patterns=[
                    r'@property\s*\n\s*def\s+\w+.*\n.*\n.*for\s+',
                ],
                languages=["py"],
                description="Expensive property computed on every access",
                suggestion="Use @functools.cached_property or manual caching",
                estimated_improvement="50-99%",
            ),
            # 同步网络请求
            PerformancePattern(
                id="PERF009",
                name="Synchronous Network Request",
                category=PerformanceCategory.NETWORK,
                impact=ImpactLevel.HIGH,
                patterns=[
                    r'requests\.(get|post|put)\s*\([^)]*\)\s*$',
                ],
                languages=["py"],
                description="Synchronous HTTP call blocks the thread",
                suggestion="Use aiohttp or httpx with async/await",
                estimated_improvement="50-80% latency",
            ),
            # O(n^2) 嵌套循环
            PerformancePattern(
                id="PERF010",
                name="Nested Loop (O(n^2) Risk)",
                category=PerformanceCategory.ALGORITHM,
                impact=ImpactLevel.HIGH,
                patterns=[
                    r'for\s+.*:\s*\n(\s+)for\s+',
                ],
                languages=["py", "js", "ts", "go", "java"],
                description="Nested loops may indicate O(n^2) complexity",
                suggestion="Consider using dict/set for O(1) lookups",
                estimated_improvement="50-99%",
            ),
        ]
