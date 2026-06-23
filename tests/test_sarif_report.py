#!/usr/bin/env python3
"""
SARIF 输出格式测试
"""

import json
from pathlib import Path

from src.reports.sarif_report import analysis_to_sarif, write_sarif, SARIF_VERSION, SARIF_SCHEMA


class TestSarifFormat:
    """SARIF 格式测试"""

    def test_empty_analysis(self):
        """空分析结果"""
        sarif = analysis_to_sarif({"files": []})
        assert sarif["version"] == SARIF_VERSION
        assert sarif["$schema"] == SARIF_SCHEMA
        assert len(sarif["runs"]) == 1
        assert len(sarif["runs"][0]["results"]) == 0

    def test_code_smells(self):
        """代码坏味道转换"""
        analysis = {
            "files": [
                {
                    "file_path": "src/main.py",
                    "code_smells": [
                        {
                            "name": "Long Function",
                            "severity": "medium",
                            "location": "src/main.py:42",
                            "description": "Function has 55 lines",
                            "suggestion": "Break into smaller functions",
                        }
                    ]
                }
            ]
        }

        sarif = analysis_to_sarif(analysis, project_path=".")
        run = sarif["runs"][0]

        assert len(run["results"]) == 1
        result = run["results"][0]
        assert result["ruleId"] == "Long Function"
        assert result["level"] == "warning"
        assert result["message"]["text"] == "Function has 55 lines"
        assert result["locations"][0]["physicalLocation"]["artifactLocation"]["uri"] == "src/main.py"
        assert result["locations"][0]["physicalLocation"]["region"]["startLine"] == 42

    def test_critical_severity_maps_to_error(self):
        """critical 严重程度映射为 error"""
        analysis = {
            "files": [
                {
                    "code_smells": [
                        {"name": "SEC001", "severity": "critical", "location": "a.py:1", "description": "eval() usage"}
                    ]
                }
            ]
        }

        sarif = analysis_to_sarif(analysis)
        assert sarif["runs"][0]["results"][0]["level"] == "error"

    def test_security_issues(self):
        """安全扫描结果转换"""
        analysis = {
            "files": [],
            "security_issues": [
                {
                    "rule_id": "SEC001",
                    "type": "eval_usage",
                    "severity": "high",
                    "file_path": "src/app.py",
                    "line_number": 10,
                    "description": "Use of eval() is dangerous",
                }
            ]
        }

        sarif = analysis_to_sarif(analysis)
        result = sarif["runs"][0]["results"][0]

        assert result["ruleId"] == "SEC001"
        assert result["level"] == "error"
        assert result["locations"][0]["physicalLocation"]["artifactLocation"]["uri"] == "src/app.py"
        assert result["locations"][0]["physicalLocation"]["region"]["startLine"] == 10

    def test_rules_deduplication(self):
        """规则去重"""
        analysis = {
            "files": [
                {"code_smells": [
                    {"name": "Long Function", "severity": "medium", "location": "a.py:1", "description": "Long"},
                    {"name": "Long Function", "severity": "medium", "location": "b.py:1", "description": "Long"},
                ]}
            ]
        }

        sarif = analysis_to_sarif(analysis)
        driver = sarif["runs"][0]["tool"]["driver"]

        # 同名规则只添加一次
        assert len(driver["rules"]) == 1
        # 两个结果引用同一规则
        assert len(sarif["runs"][0]["results"]) == 2

    def test_write_sarif_file(self, tmp_path):
        """SARIF 文件写入"""
        analysis = {
            "files": [
                {"code_smells": [
                    {"name": "COMPLEX001", "severity": "high", "location": "test.py:5", "description": "Too complex"}
                ]}
            ]
        }

        output_path = str(tmp_path / "results.sarif")
        result_path = write_sarif(analysis, output_path)

        assert Path(result_path).exists()
        with open(result_path) as f:
            sarif = json.load(f)

        assert sarif["version"] == SARIF_VERSION
        assert len(sarif["runs"][0]["results"]) == 1

    def test_tool_metadata(self):
        """工具元数据"""
        sarif = analysis_to_sarif({"files": []}, tool_version="1.2.3")
        driver = sarif["runs"][0]["tool"]["driver"]

        assert driver["name"] == "ai-analyze"
        assert driver["version"] == "1.2.3"
        assert "informationUri" in driver

    def test_location_without_line_number(self):
        """没有行号的 location"""
        analysis = {
            "files": [
                {"code_smells": [
                    {"name": "test", "severity": "low", "location": "src/main.py", "description": "Test"}
                ]}
            ]
        }

        sarif = analysis_to_sarif(analysis)
        result = sarif["runs"][0]["results"][0]

        # 没有 : 分隔符时，行号默认为 1
        assert result["locations"][0]["physicalLocation"]["region"]["startLine"] == 1
