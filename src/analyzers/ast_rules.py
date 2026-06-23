#!/usr/bin/env python3
"""
AST 规则引擎
支持自定义代码质量检测规则，可配置阈值和检测策略
"""

import json
import logging
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class RuleSeverity(Enum):
    """规则严重程度"""

    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RuleCategory(Enum):
    """规则类别"""

    COMPLEXITY = "complexity"  # 复杂度
    DESIGN = "design"  # 设计模式
    NAMING = "naming"  # 命名规范
    DUPLICATION = "duplication"  # 重复代码
    PERFORMANCE = "performance"  # 性能
    SECURITY = "security"  # 安全
    MAINTAINABILITY = "maintainability"  # 可维护性
    STYLE = "style"  # 代码风格


class RuleLanguage(Enum):
    """规则适用语言"""

    ALL = "all"
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    GO = "go"
    JAVA = "java"


@dataclass
class ASTRule:
    """AST 检测规则"""

    id: str
    name: str
    description: str
    category: RuleCategory
    severity: RuleSeverity
    language: RuleLanguage = RuleLanguage.ALL
    enabled: bool = True
    threshold: Optional[int] = None  # 阈值（如函数行数上限）
    suggestion: str = ""  # 改进建议
    tags: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "category": self.category.value,
            "severity": self.severity.value,
            "language": self.language.value,
            "enabled": self.enabled,
            "threshold": self.threshold,
            "suggestion": self.suggestion,
            "tags": self.tags,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ASTRule":
        return cls(
            id=data["id"],
            name=data["name"],
            description=data["description"],
            category=RuleCategory(data["category"]),
            severity=RuleSeverity(data["severity"]),
            language=RuleLanguage(data.get("language", "all")),
            enabled=data.get("enabled", True),
            threshold=data.get("threshold"),
            suggestion=data.get("suggestion", ""),
            tags=data.get("tags", []),
        )


class BuiltinRules:
    """内置规则集"""

    @staticmethod
    def get_all() -> List[ASTRule]:
        return [
            # === 复杂度规则 ===
            ASTRule(
                id="COMPLEX001",
                name="Long Method",
                description="函数过长，降低可读性和可维护性",
                category=RuleCategory.COMPLEXITY,
                severity=RuleSeverity.MEDIUM,
                threshold=50,
                suggestion="将长函数拆分为更小的、职责单一的函数",
                tags=["complexity", "readability"],
            ),
            ASTRule(
                id="COMPLEX002",
                name="High Cyclomatic Complexity",
                description="圈复杂度过高，逻辑分支太多",
                category=RuleCategory.COMPLEXITY,
                severity=RuleSeverity.HIGH,
                threshold=10,
                suggestion="简化条件逻辑，提取独立的方法或使用策略模式",
                tags=["complexity", "testing"],
            ),
            ASTRule(
                id="COMPLEX003",
                name="Deep Nesting",
                description="代码嵌套层级过深",
                category=RuleCategory.COMPLEXITY,
                severity=RuleSeverity.MEDIUM,
                threshold=4,
                suggestion="使用提前返回（guard clause）减少嵌套",
                tags=["complexity", "readability"],
            ),
            ASTRule(
                id="COMPLEX004",
                name="Large Class",
                description="类过大，可能违反单一职责原则",
                category=RuleCategory.COMPLEXITY,
                severity=RuleSeverity.MEDIUM,
                threshold=200,
                suggestion="将大类拆分为更小的、职责单一的类",
                tags=["complexity", "design"],
            ),
            ASTRule(
                id="COMPLEX005",
                name="Too Many Parameters",
                description="函数参数过多",
                category=RuleCategory.COMPLEXITY,
                severity=RuleSeverity.LOW,
                threshold=5,
                suggestion="使用参数对象或 builder 模式减少参数数量",
                tags=["complexity", "api-design"],
            ),
            # === 设计规则 ===
            ASTRule(
                id="DESIGN001",
                name="Deep Inheritance",
                description="继承层级过深",
                category=RuleCategory.DESIGN,
                severity=RuleSeverity.HIGH,
                threshold=3,
                suggestion="优先使用组合而非继承",
                tags=["design", "oop"],
            ),
            ASTRule(
                id="DESIGN002",
                name="Too Many Methods",
                description="类方法过多",
                category=RuleCategory.DESIGN,
                severity=RuleSeverity.MEDIUM,
                threshold=15,
                suggestion="考虑拆分类或提取 mixin/trait",
                tags=["design", "oop"],
            ),
            # === 命名规则 ===
            ASTRule(
                id="NAMING001",
                name="Short Variable Name",
                description="变量名过短（排除循环变量 i/j/k）",
                category=RuleCategory.NAMING,
                severity=RuleSeverity.LOW,
                threshold=2,
                suggestion="使用更有描述性的变量名",
                language=RuleLanguage.ALL,
                tags=["naming", "readability"],
            ),
            # === 性能规则 ===
            ASTRule(
                id="PERF001",
                name="Nested Loop",
                description="嵌套循环可能导致 O(n^2) 或更高复杂度",
                category=RuleCategory.PERFORMANCE,
                severity=RuleSeverity.MEDIUM,
                threshold=2,
                suggestion="考虑使用哈希表、集合或其他数据结构优化查找",
                tags=["performance", "algorithm"],
            ),
            # === 可维护性规则 ===
            ASTRule(
                id="MAINT001",
                name="Magic Number",
                description="代码中存在魔术数字",
                category=RuleCategory.MAINTAINABILITY,
                severity=RuleSeverity.LOW,
                suggestion="将魔术数字提取为命名常量",
                tags=["maintainability", "readability"],
            ),
            ASTRule(
                id="MAINT002",
                name="Missing Docstring",
                description="公共函数/类缺少文档字符串",
                category=RuleCategory.MAINTAINABILITY,
                severity=RuleSeverity.LOW,
                language=RuleLanguage.PYTHON,
                suggestion="为公共 API 添加 docstring",
                tags=["maintainability", "documentation"],
            ),
            # === 安全规则 ===
            ASTRule(
                id="SEC001",
                name="Eval Usage",
                description="使用 eval() 可能存在安全风险",
                category=RuleCategory.SECURITY,
                severity=RuleSeverity.CRITICAL,
                language=RuleLanguage.PYTHON,
                suggestion="避免使用 eval()，使用 ast.literal_eval() 或其他安全替代",
                tags=["security", "python"],
            ),
            ASTRule(
                id="SEC002",
                name="Hardcoded Secret",
                description="代码中可能包含硬编码的密钥或密码",
                category=RuleCategory.SECURITY,
                severity=RuleSeverity.CRITICAL,
                suggestion="使用环境变量或配置文件管理敏感信息",
                tags=["security", "secrets"],
            ),
        ]


class ASTRuleEngine:
    """
    AST 规则引擎
    管理规则配置，执行规则匹配
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self._rules: Dict[str, ASTRule] = {}
        self._load_builtin_rules()

        if config:
            self.apply_config(config)

    def _load_builtin_rules(self) -> None:
        """加载内置规则"""
        for rule in BuiltinRules.get_all():
            self._rules[rule.id] = rule
        logger.info(f"已加载 {len(self._rules)} 条内置规则")

    def apply_config(self, config: Dict[str, Any]) -> None:
        """
        应用规则配置
        支持启用/禁用规则、调整阈值
        """
        # 禁用规则列表
        disabled = config.get("disabled_rules", [])
        for rule_id in disabled:
            if rule_id in self._rules:
                self._rules[rule_id].enabled = False
                logger.debug(f"已禁用规则: {rule_id}")

        # 自定义阈值
        thresholds = config.get("thresholds", {})
        for rule_id, threshold in thresholds.items():
            if rule_id in self._rules:
                self._rules[rule_id].threshold = threshold
                logger.debug(f"已更新阈值: {rule_id} = {threshold}")

        # 自定义严重程度
        severities = config.get("severities", {})
        for rule_id, severity in severities.items():
            if rule_id in self._rules:
                self._rules[rule_id].severity = RuleSeverity(severity)
                logger.debug(f"已更新严重程度: {rule_id} = {severity}")

        # 自定义规则
        custom_rules = config.get("custom_rules", [])
        for rule_data in custom_rules:
            rule = ASTRule.from_dict(rule_data)
            self._rules[rule.id] = rule
            logger.debug(f"已添加自定义规则: {rule.id}")

    def get_rule(self, rule_id: str) -> Optional[ASTRule]:
        """获取规则"""
        return self._rules.get(rule_id)

    def get_enabled_rules(
        self,
        category: Optional[RuleCategory] = None,
        language: Optional[RuleLanguage] = None,
    ) -> List[ASTRule]:
        """获取启用的规则"""
        rules = [r for r in self._rules.values() if r.enabled]

        if category:
            rules = [r for r in rules if r.category == category]

        if language:
            rules = [r for r in rules if r.language == RuleLanguage.ALL or r.language == language]

        return rules

    def get_rules_by_category(self) -> Dict[RuleCategory, List[ASTRule]]:
        """按类别获取规则"""
        result: Dict[RuleCategory, List[ASTRule]] = {}
        for rule in self._rules.values():
            if rule.enabled:
                result.setdefault(rule.category, []).append(rule)
        return result

    def check_threshold(self, rule_id: str, value: int) -> Optional[Dict[str, Any]]:
        """
        检查值是否超过规则阈值

        Returns:
            如果超过阈值，返回违规信息；否则返回 None
        """
        rule = self._rules.get(rule_id)
        if not rule or not rule.enabled:
            return None

        if rule.threshold is not None and value > rule.threshold:
            return {
                "rule_id": rule.id,
                "rule_name": rule.name,
                "severity": rule.severity.value,
                "category": rule.category.value,
                "value": value,
                "threshold": rule.threshold,
                "description": rule.description,
                "suggestion": rule.suggestion,
            }
        return None

    def check_all_thresholds(self, metrics: Dict[str, int]) -> List[Dict[str, Any]]:
        """
        批量检查阈值

        Args:
            metrics: {rule_id: value} 格式的指标字典

        Returns:
            违规列表
        """
        violations = []
        for rule_id, value in metrics.items():
            result = self.check_threshold(rule_id, value)
            if result:
                violations.append(result)
        return violations

    def add_rule(self, rule: ASTRule) -> None:
        """添加自定义规则"""
        self._rules[rule.id] = rule
        logger.info(f"已添加规则: {rule.id} - {rule.name}")

    def remove_rule(self, rule_id: str) -> bool:
        """移除规则"""
        if rule_id in self._rules:
            del self._rules[rule_id]
            logger.info(f"已移除规则: {rule_id}")
            return True
        return False

    def to_dict(self) -> Dict[str, Any]:
        """导出规则配置"""
        return {
            "rules": {rid: rule.to_dict() for rid, rule in self._rules.items()},
            "enabled_count": sum(1 for r in self._rules.values() if r.enabled),
            "disabled_count": sum(1 for r in self._rules.values() if not r.enabled),
        }

    def save_config(self, filepath: str) -> None:
        """保存规则配置到文件"""
        path = Path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)

        config = {
            "disabled_rules": [rid for rid, r in self._rules.items() if not r.enabled],
            "thresholds": {rid: r.threshold for rid, r in self._rules.items() if r.threshold is not None},
            "custom_rules": [
                r.to_dict() for r in self._rules.values() if r.id not in {br.id for br in BuiltinRules.get_all()}
            ],
        }

        with open(path, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        logger.info(f"规则配置已保存到 {filepath}")

    @classmethod
    def load_config(cls, filepath: str) -> "ASTRuleEngine":
        """从文件加载规则配置"""
        path = Path(filepath)
        if not path.exists():
            logger.warning(f"规则配置文件不存在: {filepath}")
            return cls()

        with open(path, "r", encoding="utf-8") as f:
            config = json.load(f)

        engine = cls()
        engine.apply_config(config)
        logger.info(f"已从 {filepath} 加载规则配置")
        return engine

    def get_summary(self) -> Dict[str, Any]:
        """获取规则摘要"""
        by_category: Dict[str, int] = {}
        by_severity: Dict[str, int] = {}
        for rule in self._rules.values():
            if rule.enabled:
                by_category[rule.category.value] = by_category.get(rule.category.value, 0) + 1
                by_severity[rule.severity.value] = by_severity.get(rule.severity.value, 0) + 1

        return {
            "total_rules": len(self._rules),
            "enabled_rules": sum(1 for r in self._rules.values() if r.enabled),
            "by_category": by_category,
            "by_severity": by_severity,
        }
