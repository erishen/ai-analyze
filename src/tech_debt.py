#!/usr/bin/env python3
"""
技术债务量化评估模块
基于多维度指标计算技术债务评分和修复建议
"""

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


@dataclass
class DebtItem:
    """技术债务条目"""

    category: str
    name: str
    file_path: str
    line_number: int
    description: str
    effort_hours: float  # 修复预估工时
    priority: str  # low, medium, high, critical

    def to_dict(self) -> Dict[str, Any]:
        return {
            "category": self.category,
            "name": self.name,
            "file_path": self.file_path,
            "line_number": self.line_number,
            "description": self.description,
            "effort_hours": self.effort_hours,
            "priority": self.priority,
        }


@dataclass
class DebtCategorySummary:
    """债务类别汇总"""

    category: str
    count: int
    total_effort_hours: float
    average_effort: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "category": self.category,
            "count": self.count,
            "total_effort_hours": round(self.total_effort_hours, 1),
            "average_effort": round(self.average_effort, 1),
        }


@dataclass
class TechDebtResult:
    """技术债务评估结果"""

    items: List[DebtItem] = field(default_factory=list)
    total_lines_of_code: int = 0
    total_files: int = 0

    @property
    def debt_score(self) -> float:
        """技术债务评分 (0-100, 越低越好, 0=无债务)"""
        if not self.items or self.total_lines_of_code == 0:
            return 0.0
        # 每千行代码的债务工时作为核心指标
        debt_per_kloc = (self.total_effort_hours / self.total_lines_of_code) * 1000
        # 0小时/KLOC = 0分, 40小时/KLOC = 100分
        score = min(100, (debt_per_kloc / 40.0) * 100)
        return round(score, 1)

    @property
    def total_effort_hours(self) -> float:
        return sum(item.effort_hours for item in self.items)

    @property
    def critical_count(self) -> int:
        return sum(1 for i in self.items if i.priority == "critical")

    @property
    def high_count(self) -> int:
        return sum(1 for i in self.items if i.priority == "high")

    @property
    def category_summaries(self) -> List[DebtCategorySummary]:
        """按类别汇总"""
        cats: Dict[str, List[DebtItem]] = {}
        for item in self.items:
            cats.setdefault(item.category, []).append(item)

        summaries = []
        for cat, items in cats.items():
            total = sum(i.effort_hours for i in items)
            summaries.append(
                DebtCategorySummary(
                    category=cat,
                    count=len(items),
                    total_effort_hours=total,
                    average_effort=total / len(items),
                )
            )
        summaries.sort(key=lambda s: s.total_effort_hours, reverse=True)
        return summaries

    @property
    def top_debt_items(self) -> List[DebtItem]:
        """按工时排序的 Top 债务条目"""
        sorted_items = sorted(self.items, key=lambda i: i.effort_hours, reverse=True)
        return sorted_items[:10]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_items": len(self.items),
            "debt_score": self.debt_score,
            "total_effort_hours": round(self.total_effort_hours, 1),
            "critical_count": self.critical_count,
            "high_count": self.high_count,
            "total_lines_of_code": self.total_lines_of_code,
            "total_files": self.total_files,
            "category_summaries": [s.to_dict() for s in self.category_summaries],
            "top_debt_items": [i.to_dict() for i in self.top_debt_items],
        }


@dataclass
class DebtPattern:
    """债务检测模式"""

    category: str
    name: str
    description: str
    patterns: List[str]
    effort_hours: float
    priority: str
    languages: List[str] = field(default_factory=lambda: ["all"])


class TechDebtAnalyzer:
    """技术债务分析器"""

    def __init__(self):
        self.logger = logging.getLogger("ai-analyze.tech_debt")
        self._patterns = self._builtin_patterns()

    def analyze_file(
        self,
        file_path: str,
        content: str,
        complexity_data: Optional[Dict[str, Any]] = None,
    ) -> List[DebtItem]:
        """分析单个文件的技术债务"""
        items: List[DebtItem] = []
        lines = content.split("\n")
        line_count = len(lines)

        for pattern in self._patterns:
            if not self._matches_language(file_path, pattern.languages):
                continue

            for regex_str in pattern.patterns:
                try:
                    compiled = re.compile(regex_str)
                except re.error:
                    continue

                for line_num, line in enumerate(lines, 1):
                    if compiled.search(line):
                        items.append(
                            DebtItem(
                                category=pattern.category,
                                name=pattern.name,
                                file_path=file_path,
                                line_number=line_num,
                                description=pattern.description,
                                effort_hours=pattern.effort_hours,
                                priority=pattern.priority,
                            )
                        )

        # 基于文件行数的债务
        if line_count > 500:
            items.append(
                DebtItem(
                    category="maintainability",
                    name="Large File",
                    file_path=file_path,
                    line_number=1,
                    description=f"File has {line_count} lines (threshold: 500)",
                    effort_hours=(line_count - 500) * 0.01,
                    priority="medium" if line_count < 1000 else "high",
                )
            )

        # 基于复杂度数据的债务
        if complexity_data:
            cc = complexity_data.get("cyclomatic_complexity", 0)
            if cc > 10:
                items.append(
                    DebtItem(
                        category="complexity",
                        name="High Cyclomatic Complexity",
                        file_path=file_path,
                        line_number=1,
                        description=f"Cyclomatic complexity is {cc} (threshold: 10)",
                        effort_hours=(cc - 10) * 0.5,
                        priority="high" if cc > 20 else "medium",
                    )
                )

        return items

    def analyze_project(
        self,
        files: Dict[str, str],
        complexity_data: Optional[Dict[str, Dict[str, Any]]] = None,
    ) -> TechDebtResult:
        """分析项目技术债务"""
        all_items: List[DebtItem] = []
        total_loc = 0

        for file_path, content in files.items():
            total_loc += len(content.split("\n"))
            c_data = complexity_data.get(file_path) if complexity_data else None
            items = self.analyze_file(file_path, content, c_data)
            all_items.extend(items)

        # 按优先级排序
        priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        all_items.sort(key=lambda i: priority_order.get(i.priority, 99))

        return TechDebtResult(
            items=all_items,
            total_lines_of_code=total_loc,
            total_files=len(files),
        )

    def _matches_language(self, file_path: str, languages: List[str]) -> bool:
        """检查文件是否匹配语言"""
        import os

        if "all" in languages:
            return True
        ext = os.path.splitext(file_path)[1].lstrip(".")
        return ext in languages

    def _builtin_patterns(self) -> List[DebtPattern]:
        """内置技术债务检测模式"""
        return [
            # TODO/FIXME/HACK
            DebtPattern(
                category="todo",
                name="Unresolved TODO",
                description="TODO comment indicates unfinished work",
                patterns=[r'#\s*TODO', r'#\s*FIXME', r'#\s*HACK', r'#\s*XXX'],
                effort_hours=2.0,
                priority="low",
            ),
            DebtPattern(
                category="todo",
                name="Unresolved TODO (JS/TS)",
                description="TODO comment indicates unfinished work",
                patterns=[r'//\s*TODO', r'//\s*FIXME', r'//\s*HACK'],
                effort_hours=2.0,
                priority="low",
                languages=["js", "ts", "java", "go"],
            ),
            # 被注释掉的代码
            DebtPattern(
                category="dead_code",
                name="Commented Out Code",
                description="Commented-out code should be removed",
                patterns=[r'^\s*#\s*(def|class|import|from|if|for|while|return)\s'],
                effort_hours=0.5,
                priority="low",
            ),
            # 过长函数（基于缩进估算）
            DebtPattern(
                category="maintainability",
                name="Long Function Hint",
                description="Too many nested blocks suggest long function",
                patterns=[r'^\s{16,}\w+'],
                effort_hours=3.0,
                priority="medium",
            ),
            # 空异常捕获
            DebtPattern(
                category="error_handling",
                name="Bare Except",
                description="Bare except catches all exceptions silently",
                patterns=[r'except\s*:', r'except\s+Exception\s*:'],
                effort_hours=1.0,
                priority="high",
            ),
            DebtPattern(
                category="error_handling",
                name="Pass in Except",
                description="Silently ignoring exceptions with pass",
                patterns=[r'except\s+\w+.*:\s*\n\s+pass'],
                effort_hours=1.5,
                priority="high",
            ),
            # 魔法数字
            DebtPattern(
                category="readability",
                name="Magic Number",
                description="Hardcoded numeric literal without explanation",
                patterns=[r'(?<!["\w])\d{2,}(?!["\w])'],
                effort_hours=0.25,
                priority="low",
            ),
            # 过多参数（简单启发式）
            DebtPattern(
                category="design",
                name="Many Function Parameters",
                description="Function with many parameters is hard to maintain",
                patterns=[r'def\s+\w+\s*\([^)]{80,}\)'],
                effort_hours=2.0,
                priority="medium",
            ),
            # 重复字符串常量
            DebtPattern(
                category="duplication",
                name="Hardcoded String Path",
                description="Hardcoded file path should be configurable",
                patterns=[r'["\']/(?:usr|etc|var|tmp|home)/'],
                effort_hours=1.0,
                priority="medium",
            ),
            # 过时的 API
            DebtPattern(
                category="deprecation",
                name="Deprecated API",
                description="Use of deprecated function or method",
                patterns=[r'\.warn\s*\(', r'deprecat', r'DeprecationWarning'],
                effort_hours=1.5,
                priority="medium",
            ),
        ]
