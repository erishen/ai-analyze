#!/usr/bin/env python3
"""
AST 规则引擎单元测试
"""

import json
import sys
import tempfile
from pathlib import Path

# 添加项目根目录到路径，使用包导入
_project_root = str(Path(__file__).parent.parent)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from src.analyzers.ast_rules import (  # noqa: E402
    ASTRule,
    ASTRuleEngine,
    BuiltinRules,
    RuleCategory,
    RuleLanguage,
    RuleSeverity,
)


# ==================== 枚举测试 ====================


def test_rule_severity_values():
    """测试规则严重程度枚举"""
    assert RuleSeverity.INFO.value == "info"
    assert RuleSeverity.LOW.value == "low"
    assert RuleSeverity.MEDIUM.value == "medium"
    assert RuleSeverity.HIGH.value == "high"
    assert RuleSeverity.CRITICAL.value == "critical"


def test_rule_category_values():
    """测试规则类别枚举"""
    assert RuleCategory.COMPLEXITY.value == "complexity"
    assert RuleCategory.DESIGN.value == "design"
    assert RuleCategory.NAMING.value == "naming"
    assert RuleCategory.SECURITY.value == "security"
    assert RuleCategory.PERFORMANCE.value == "performance"
    assert RuleCategory.MAINTAINABILITY.value == "maintainability"


def test_rule_language_values():
    """测试规则语言枚举"""
    assert RuleLanguage.ALL.value == "all"
    assert RuleLanguage.PYTHON.value == "python"
    assert RuleLanguage.JAVASCRIPT.value == "javascript"
    assert RuleLanguage.GO.value == "go"


# ==================== ASTRule 测试 ====================


def test_ast_rule_creation():
    """测试规则创建"""
    rule = ASTRule(
        id="TEST001",
        name="Test Rule",
        description="A test rule",
        category=RuleCategory.COMPLEXITY,
        severity=RuleSeverity.MEDIUM,
        threshold=50,
        suggestion="Fix it",
    )
    assert rule.id == "TEST001"
    assert rule.name == "Test Rule"
    assert rule.enabled
    assert rule.threshold == 50


def test_ast_rule_default_values():
    """测试规则默认值"""
    rule = ASTRule(
        id="TEST001",
        name="Test",
        description="Desc",
        category=RuleCategory.STYLE,
        severity=RuleSeverity.LOW,
    )
    assert rule.enabled is True
    assert rule.language == RuleLanguage.ALL
    assert rule.threshold is None
    assert rule.suggestion == ""
    assert rule.tags == []


def test_ast_rule_serialization():
    """测试规则序列化/反序列化"""
    rule = ASTRule(
        id="TEST001",
        name="Test Rule",
        description="A test rule",
        category=RuleCategory.COMPLEXITY,
        severity=RuleSeverity.HIGH,
        language=RuleLanguage.PYTHON,
        threshold=100,
        suggestion="Refactor",
        tags=["test", "demo"],
    )
    d = rule.to_dict()
    assert d["id"] == "TEST001"
    assert d["category"] == "complexity"
    assert d["severity"] == "high"
    assert d["language"] == "python"
    assert d["threshold"] == 100
    assert d["tags"] == ["test", "demo"]

    # 反序列化
    restored = ASTRule.from_dict(d)
    assert restored.id == "TEST001"
    assert restored.category == RuleCategory.COMPLEXITY
    assert restored.severity == RuleSeverity.HIGH
    assert restored.language == RuleLanguage.PYTHON
    assert restored.threshold == 100


def test_ast_rule_roundtrip():
    """测试规则序列化往返"""
    rule = ASTRule(
        id="R001",
        name="Round Trip",
        description="Round trip test",
        category=RuleCategory.SECURITY,
        severity=RuleSeverity.CRITICAL,
    )
    restored = ASTRule.from_dict(rule.to_dict())
    assert restored.id == rule.id
    assert restored.name == rule.name
    assert restored.category == rule.category
    assert restored.severity == rule.severity


# ==================== BuiltinRules 测试 ====================


def test_builtin_rules_count():
    """测试内置规则数量"""
    rules = BuiltinRules.get_all()
    assert len(rules) >= 12  # 至少 12 条内置规则


def test_builtin_rules_have_ids():
    """测试内置规则 ID 唯一"""
    rules = BuiltinRules.get_all()
    ids = [r.id for r in rules]
    assert len(ids) == len(set(ids)), "内置规则 ID 有重复"


def test_builtin_rules_categories():
    """测试内置规则覆盖各类别"""
    rules = BuiltinRules.get_all()
    categories = set(r.category for r in rules)
    assert RuleCategory.COMPLEXITY in categories
    assert RuleCategory.DESIGN in categories
    assert RuleCategory.SECURITY in categories


def test_builtin_complex001():
    """测试 COMPLEX001 长函数规则"""
    rules = {r.id: r for r in BuiltinRules.get_all()}
    rule = rules.get("COMPLEX001")
    assert rule is not None
    assert rule.name == "Long Method"
    assert rule.threshold == 50
    assert rule.category == RuleCategory.COMPLEXITY


def test_builtin_complex002():
    """测试 COMPLEX002 圈复杂度规则"""
    rules = {r.id: r for r in BuiltinRules.get_all()}
    rule = rules.get("COMPLEX002")
    assert rule is not None
    assert rule.name == "High Cyclomatic Complexity"
    assert rule.threshold == 10


def test_builtin_sec001():
    """测试 SEC001 eval 规则"""
    rules = {r.id: r for r in BuiltinRules.get_all()}
    rule = rules.get("SEC001")
    assert rule is not None
    assert rule.severity == RuleSeverity.CRITICAL
    assert rule.language == RuleLanguage.PYTHON


# ==================== ASTRuleEngine 测试 ====================


def test_engine_init():
    """测试引擎初始化"""
    engine = ASTRuleEngine()
    summary = engine.get_summary()
    assert summary["total_rules"] >= 12
    assert summary["enabled_rules"] >= 12


def test_engine_get_rule():
    """测试获取规则"""
    engine = ASTRuleEngine()
    rule = engine.get_rule("COMPLEX001")
    assert rule is not None
    assert rule.name == "Long Method"

    assert engine.get_rule("NONEXISTENT") is None


def test_engine_get_enabled_rules():
    """测试获取启用的规则"""
    engine = ASTRuleEngine()
    rules = engine.get_enabled_rules()
    assert len(rules) >= 12
    assert all(r.enabled for r in rules)


def test_engine_get_enabled_rules_by_category():
    """测试按类别获取规则"""
    engine = ASTRuleEngine()
    complexity_rules = engine.get_enabled_rules(category=RuleCategory.COMPLEXITY)
    assert len(complexity_rules) >= 4
    assert all(r.category == RuleCategory.COMPLEXITY for r in complexity_rules)


def test_engine_get_enabled_rules_by_language():
    """测试按语言获取规则"""
    engine = ASTRuleEngine()
    python_rules = engine.get_enabled_rules(language=RuleLanguage.PYTHON)
    # 应包含 ALL 和 PYTHON 的规则
    for r in python_rules:
        assert r.language in (RuleLanguage.ALL, RuleLanguage.PYTHON)


def test_engine_check_threshold_violation():
    """测试阈值违规检测"""
    engine = ASTRuleEngine()
    # COMPLEX001 threshold=50，传 60 应违规
    result = engine.check_threshold("COMPLEX001", 60)
    assert result is not None
    assert result["rule_id"] == "COMPLEX001"
    assert result["value"] == 60
    assert result["threshold"] == 50


def test_engine_check_threshold_ok():
    """测试阈值未违规"""
    engine = ASTRuleEngine()
    # COMPLEX001 threshold=50，传 30 不应违规
    result = engine.check_threshold("COMPLEX001", 30)
    assert result is None


def test_engine_check_threshold_equal():
    """测试阈值等于边界"""
    engine = ASTRuleEngine()
    # threshold=50，传 50 不应违规（> 才违规）
    result = engine.check_threshold("COMPLEX001", 50)
    assert result is None


def test_engine_check_threshold_nonexistent_rule():
    """测试检查不存在的规则"""
    engine = ASTRuleEngine()
    result = engine.check_threshold("FAKE001", 100)
    assert result is None


def test_engine_check_all_thresholds():
    """测试批量阈值检查"""
    engine = ASTRuleEngine()
    violations = engine.check_all_thresholds(
        {
            "COMPLEX001": 80,  # > 50, 违规
            "COMPLEX002": 5,  # < 10, 不违规
            "COMPLEX003": 6,  # > 4, 违规
        }
    )
    assert len(violations) == 2
    ids = [v["rule_id"] for v in violations]
    assert "COMPLEX001" in ids
    assert "COMPLEX003" in ids


def test_engine_disable_rule():
    """测试禁用规则"""
    engine = ASTRuleEngine()
    engine.apply_config({"disabled_rules": ["COMPLEX001"]})

    rule = engine.get_rule("COMPLEX001")
    assert rule is not None
    assert not rule.enabled

    # 禁用后 check_threshold 应返回 None
    result = engine.check_threshold("COMPLEX001", 999)
    assert result is None


def test_engine_custom_threshold():
    """测试自定义阈值"""
    engine = ASTRuleEngine()
    engine.apply_config({"thresholds": {"COMPLEX001": 100}})

    rule = engine.get_rule("COMPLEX001")
    assert rule.threshold == 100

    # 80 < 100，不违规
    result = engine.check_threshold("COMPLEX001", 80)
    assert result is None

    # 120 > 100，违规
    result = engine.check_threshold("COMPLEX001", 120)
    assert result is not None


def test_engine_custom_severity():
    """测试自定义严重程度"""
    engine = ASTRuleEngine()
    engine.apply_config({"severities": {"COMPLEX001": "critical"}})

    rule = engine.get_rule("COMPLEX001")
    assert rule.severity == RuleSeverity.CRITICAL


def test_engine_add_custom_rule():
    """测试添加自定义规则"""
    engine = ASTRuleEngine()
    custom = ASTRule(
        id="CUSTOM001",
        name="No Print",
        description="禁止使用 print()",
        category=RuleCategory.STYLE,
        severity=RuleSeverity.LOW,
        language=RuleLanguage.PYTHON,
    )
    engine.add_rule(custom)

    rule = engine.get_rule("CUSTOM001")
    assert rule is not None
    assert rule.name == "No Print"


def test_engine_remove_rule():
    """测试移除规则"""
    engine = ASTRuleEngine()
    assert engine.remove_rule("COMPLEX001")
    assert engine.get_rule("COMPLEX001") is None

    # 移除不存在的规则
    assert not engine.remove_rule("FAKE999")


def test_engine_get_rules_by_category():
    """测试按类别分组获取规则"""
    engine = ASTRuleEngine()
    by_category = engine.get_rules_by_category()
    assert RuleCategory.COMPLEXITY in by_category
    assert len(by_category[RuleCategory.COMPLEXITY]) >= 4


def test_engine_to_dict():
    """测试引擎导出为字典"""
    engine = ASTRuleEngine()
    d = engine.to_dict()
    assert "rules" in d
    assert "enabled_count" in d
    assert "disabled_count" in d
    assert d["enabled_count"] >= 12


def test_engine_get_summary():
    """测试引擎摘要"""
    engine = ASTRuleEngine()
    summary = engine.get_summary()
    assert "total_rules" in summary
    assert "enabled_rules" in summary
    assert "by_category" in summary
    assert "by_severity" in summary
    assert "complexity" in summary["by_category"]


# ==================== 配置文件持久化测试 ====================


def test_engine_save_load_config():
    """测试规则配置保存与加载"""
    engine = ASTRuleEngine()
    # 禁用一条规则，调整阈值
    engine.apply_config(
        {
            "disabled_rules": ["COMPLEX001"],
            "thresholds": {"COMPLEX002": 20},
        }
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = str(Path(tmpdir) / "rules_config.json")
        engine.save_config(config_path)

        # 从文件加载
        loaded = ASTRuleEngine.load_config(config_path)
        assert loaded.get_rule("COMPLEX001") is not None
        assert not loaded.get_rule("COMPLEX001").enabled
        assert loaded.get_rule("COMPLEX002").threshold == 20


def test_engine_save_config_includes_custom():
    """测试保存配置包含自定义规则"""
    engine = ASTRuleEngine()
    engine.add_rule(
        ASTRule(
            id="MYRULE001",
            name="My Rule",
            description="Custom",
            category=RuleCategory.STYLE,
            severity=RuleSeverity.INFO,
        )
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = str(Path(tmpdir) / "rules.json")
        engine.save_config(config_path)

        with open(config_path) as f:
            data = json.load(f)
        custom_ids = [r["id"] for r in data["custom_rules"]]
        assert "MYRULE001" in custom_ids


def test_engine_load_nonexistent_config():
    """测试加载不存在的配置文件"""
    engine = ASTRuleEngine.load_config("/nonexistent/path.json")
    # 应返回默认引擎
    assert engine.get_summary()["enabled_rules"] >= 12


# ==================== 运行所有测试 ====================


def run_all_tests():
    """运行所有测试"""
    tests = [
        test_rule_severity_values,
        test_rule_category_values,
        test_rule_language_values,
        test_ast_rule_creation,
        test_ast_rule_default_values,
        test_ast_rule_serialization,
        test_ast_rule_roundtrip,
        test_builtin_rules_count,
        test_builtin_rules_have_ids,
        test_builtin_rules_categories,
        test_builtin_complex001,
        test_builtin_complex002,
        test_builtin_sec001,
        test_engine_init,
        test_engine_get_rule,
        test_engine_get_enabled_rules,
        test_engine_get_enabled_rules_by_category,
        test_engine_get_enabled_rules_by_language,
        test_engine_check_threshold_violation,
        test_engine_check_threshold_ok,
        test_engine_check_threshold_equal,
        test_engine_check_threshold_nonexistent_rule,
        test_engine_check_all_thresholds,
        test_engine_disable_rule,
        test_engine_custom_threshold,
        test_engine_custom_severity,
        test_engine_add_custom_rule,
        test_engine_remove_rule,
        test_engine_get_rules_by_category,
        test_engine_to_dict,
        test_engine_get_summary,
        test_engine_save_load_config,
        test_engine_save_config_includes_custom,
        test_engine_load_nonexistent_config,
    ]

    print("🧪 开始运行 AST 规则引擎测试...\n")
    passed = 0
    failed = 0

    for test_fn in tests:
        try:
            test_fn()
            print(f"  ✅ {test_fn.__name__}")
            passed += 1
        except AssertionError as e:
            print(f"  ❌ {test_fn.__name__}: {e}")
            failed += 1
        except Exception as e:
            print(f"  ❌ {test_fn.__name__}: {e}")
            import traceback

            traceback.print_exc()
            failed += 1

    print(f"\n📊 结果: {passed} 通过, {failed} 失败, 共 {len(tests)} 个测试")
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
