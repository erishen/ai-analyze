#!/usr/bin/env python3
"""
SARIF 输出格式模块
将分析结果转换为 SARIF (Static Analysis Results Interchange Format) 格式
用于 GitHub Code Scanning 集成

SARIF 规范: https://docs.oasis-open.org/sarif/sarif/v2.1.0/sarif-v2.1.0.html
"""

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)

SARIF_VERSION = "2.1.0"
SARIF_SCHEMA = "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/main/sarif-2.1/schema/sarif-schema-2.1.0.json"

# 严重程度映射: ai-analyze → SARIF level
SEVERITY_TO_LEVEL = {
    "critical": "error",
    "high": "error",
    "medium": "warning",
    "low": "note",
    "info": "note",
}


def _make_sarif_run(project_path: str = ".", tool_version: str = "0.3.0") -> dict[str, Any]:
    """创建 SARIF run 基础结构"""
    return {
        "tool": {
            "driver": {
                "name": "ai-analyze",
                "version": tool_version,
                "semanticVersion": tool_version,
                "informationUri": "https://github.com/erishen/ai-analyze",
                "rules": [],
            }
        },
        "results": [],
        "invocations": [
            {
                "executionSuccessful": True,
                "startTimeUtc": datetime.now(timezone.utc).isoformat(),
            }
        ],
    }


def _code_smell_to_sarif_result(
    smell: dict[str, Any],
    rule_index: int,
    project_path: str,
) -> dict[str, Any]:
    """将 CodeSmell 转换为 SARIF result"""
    location_str = smell.get("location", "")
    file_path = location_str
    line_number = 1

    if ":" in location_str:
        parts = location_str.rsplit(":", 1)
        try:
            line_number = int(parts[1])
            file_path = parts[0]
        except (ValueError, IndexError):
            pass

    # 确保文件路径是相对的
    try:
        file_path = str(Path(file_path).relative_to(project_path))
    except (ValueError, TypeError):
        pass

    severity = smell.get("severity", "medium")
    level = SEVERITY_TO_LEVEL.get(severity, "warning")

    return {
        "ruleId": smell.get("name", "unknown"),
        "ruleIndex": rule_index,
        "level": level,
        "message": {
            "text": smell.get("description", smell.get("name", "Unknown issue")),
        },
        "locations": [
            {
                "physicalLocation": {
                    "artifactLocation": {
                        "uri": file_path,
                        "uriBaseId": "%SRCROOT%",
                    },
                    "region": {
                        "startLine": line_number,
                    },
                }
            }
        ],
    }


def _security_issue_to_sarif_result(
    issue: dict[str, Any],
    rule_index: int,
    project_path: str,
) -> dict[str, Any]:
    """将 SecurityScanner 结果转换为 SARIF result"""
    file_path = issue.get("file_path", "")
    line_number = issue.get("line_number", 1)

    try:
        file_path = str(Path(file_path).relative_to(project_path))
    except (ValueError, TypeError):
        pass

    severity = issue.get("severity", "medium")
    level = SEVERITY_TO_LEVEL.get(severity, "warning")

    return {
        "ruleId": issue.get("rule_id", issue.get("type", "security")),
        "ruleIndex": rule_index,
        "level": level,
        "message": {
            "text": issue.get("description", issue.get("message", "Security issue")),
        },
        "locations": [
            {
                "physicalLocation": {
                    "artifactLocation": {
                        "uri": file_path,
                        "uriBaseId": "%SRCROOT%",
                    },
                    "region": {
                        "startLine": line_number,
                    },
                }
            }
        ],
    }


def _add_rule(run: dict[str, Any], rule_id: str, description: str, severity: str) -> int:
    """添加规则到 SARIF run，返回规则索引"""
    driver = run["tool"]["driver"]
    rules = driver["rules"]

    # 检查规则是否已存在
    for i, rule in enumerate(rules):
        if rule["id"] == rule_id:
            return i

    level = SEVERITY_TO_LEVEL.get(severity, "warning")

    rules.append({
        "id": rule_id,
        "shortDescription": {
            "text": description,
        },
        "defaultConfiguration": {
            "level": level,
        },
        "properties": {
            "tags": ["maintainability"],
        },
    })

    return len(rules) - 1


def analysis_to_sarif(
    analysis_results: dict[str, Any],
    project_path: str = ".",
    tool_version: str = "0.3.0",
) -> dict[str, Any]:
    """将分析结果转换为 SARIF 格式

    Args:
        analysis_results: ai-analyze 分析结果字典
        project_path: 项目根路径
        tool_version: 工具版本

    Returns:
        SARIF 格式的字典
    """
    sarif = {
        "$schema": SARIF_SCHEMA,
        "version": SARIF_VERSION,
        "runs": [],
    }

    run = _make_sarif_run(project_path, tool_version)

    # 处理代码坏味道
    for file_data in analysis_results.get("files", []):
        for smell in file_data.get("code_smells", []):
            rule_id = smell.get("name", "unknown")
            description = smell.get("suggestion", smell.get("description", rule_id))
            severity = smell.get("severity", "medium")

            rule_index = _add_rule(run, rule_id, description, severity)
            result = _code_smell_to_sarif_result(smell, rule_index, project_path)
            run["results"].append(result)

    # 处理安全扫描结果
    for issue in analysis_results.get("security_issues", []):
        rule_id = issue.get("rule_id", issue.get("type", "security"))
        description = issue.get("description", issue.get("message", rule_id))
        severity = issue.get("severity", "medium")

        rule_index = _add_rule(run, rule_id, description, severity)
        result = _security_issue_to_sarif_result(issue, rule_index, project_path)
        run["results"].append(result)

    # 更新 invocation 结束时间
    if run["invocations"]:
        run["invocations"][0]["endTimeUtc"] = datetime.now(timezone.utc).isoformat()

    sarif["runs"].append(run)

    return sarif


def write_sarif(
    analysis_results: dict[str, Any],
    output_path: str,
    project_path: str = ".",
    tool_version: str = "0.3.0",
) -> str:
    """将分析结果写入 SARIF 文件

    Args:
        analysis_results: ai-analyze 分析结果字典
        output_path: 输出文件路径
        project_path: 项目根路径
        tool_version: 工具版本

    Returns:
        输出文件路径
    """
    sarif = analysis_to_sarif(analysis_results, project_path, tool_version)

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)

    with open(output, "w", encoding="utf-8") as f:
        json.dump(sarif, f, indent=2, ensure_ascii=False)

    logger.info(f"SARIF report written to {output_path} ({len(sarif['runs'][0]['results'])} results)")
    return str(output)
